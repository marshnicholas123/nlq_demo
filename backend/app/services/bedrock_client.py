import boto3
import json
from typing import Dict, Any
from app.config import settings
from opentelemetry import trace

# Get tracer for custom spans
tracer = trace.get_tracer(__name__)


class BedrockClient:
    def __init__(self):
        # Note: BedrockInstrumentor will automatically instrument this client
        # when Phoenix observability is initialized
        self.client = boto3.client('bedrock-runtime', region_name=settings.aws_region)
        self.model_id = settings.bedrock_model_id

    def invoke_model(self, prompt: str, system: str = "", max_tokens: int = 4000, operation_type: str = None) -> str:
        """Invoke Claude model via Bedrock

        Args:
            prompt: User prompt to send to the model
            system: System prompt for the model
            max_tokens: Maximum tokens to generate
            operation_type: Type of operation (e.g., 'sql_generation', 'response_generation')
        """

        # Create custom span for additional context
        with tracer.start_as_current_span("bedrock.invoke_model") as span:
            # Add custom attributes to the span
            span.set_attribute("llm.model_id", self.model_id)
            span.set_attribute("llm.max_tokens", max_tokens)
            span.set_attribute("llm.has_system_prompt", bool(system))
            span.set_attribute("llm.prompt_length", len(prompt))
            span.set_attribute("llm.prompt", prompt)

            if system:
                span.set_attribute("llm.system_prompt", system)

            # Add operation type if provided for better trace filtering
            if operation_type:
                span.set_attribute("llm.operation_type", operation_type)

            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            if system:
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "system": system,
                    "messages": messages
                }
                # Create full instruction view
                full_instruction = f"System Prompt:\n{system}\n\nUser Prompt:\n{prompt}"
            else:
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "messages": messages
                }
                full_instruction = prompt

            # Add full instruction to span
            span.set_attribute("llm.full_instruction", full_instruction)

            try:
                # This call is automatically instrumented by BedrockInstrumentor
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body)
                )

                response_body = json.loads(response['body'].read())
                response_text = response_body['content'][0]['text']

                # Add response metadata to span
                span.set_attribute("llm.response_length", len(response_text))
                span.set_attribute("llm.response_text", response_text)
                span.set_attribute("llm.stop_reason", response_body.get('stop_reason', 'unknown'))

                # Track token usage if available
                usage = response_body.get('usage', {})
                if usage:
                    span.set_attribute("llm.input_tokens", usage.get('input_tokens', 0))
                    span.set_attribute("llm.output_tokens", usage.get('output_tokens', 0))

                return response_text

            except Exception as e:
                # Record exception in span
                span.record_exception(e)
                span.set_attribute("error", True)
                raise Exception(f"Error calling Bedrock: {str(e)}")


# Global instance
bedrock_client = BedrockClient()