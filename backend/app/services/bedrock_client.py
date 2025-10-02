import boto3
import json
from typing import Dict, Any
from app.config import settings

class BedrockClient:
    def __init__(self):
        self.client = boto3.client('bedrock-runtime', region_name=settings.aws_region)
        self.model_id = settings.bedrock_model_id
    
    def invoke_model(self, prompt: str, system: str = "", max_tokens: int = 4000) -> str:
        """Invoke Claude model via Bedrock"""
        
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
        else:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": messages
            }
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            raise Exception(f"Error calling Bedrock: {str(e)}")

# Global instance
bedrock_client = BedrockClient()