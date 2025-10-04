"""
Phoenix Observability Configuration

This module initializes and configures Arize Phoenix for LLM tracing and observability.
Supports both AWS Bedrock and LangChain instrumentation.
"""

import phoenix as px
from phoenix.otel import register
from openinference.instrumentation.bedrock import BedrockInstrumentor
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.sdk.trace import TracerProvider
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PhoenixObservability:
    """Manages Phoenix tracing and observability initialization"""

    def __init__(self):
        self.tracer_provider: Optional[TracerProvider] = None
        self.phoenix_session = None
        self._initialized = False

    def initialize(
        self,
        project_name: str = "text2sql-app",
        endpoint: Optional[str] = None,
        auto_instrument: bool = True,
        launch_app: bool = False
    ):
        """
        Initialize Phoenix observability

        Args:
            project_name: Name of the project for trace organization
            endpoint: OTLP endpoint URL (None for local Phoenix)
            auto_instrument: Whether to auto-instrument based on installed dependencies
            launch_app: Whether to launch Phoenix UI locally
        """
        if self._initialized:
            logger.warning("Phoenix already initialized, skipping re-initialization")
            return

        try:
            # Launch Phoenix app if requested (useful for local development)
            if launch_app:
                logger.info("Launching Phoenix UI...")
                self.phoenix_session = px.launch_app()
                logger.info(f"Phoenix UI available at: {self.phoenix_session.url}")

            # Register tracer provider
            # If endpoint is empty or None, default to local Phoenix with OTLP path
            if endpoint:
                phoenix_endpoint = endpoint
            else:
                # Local Phoenix OTLP endpoint
                phoenix_endpoint = "http://127.0.0.1:6006/v1/traces"

            logger.info(f"Registering Phoenix tracer for project: {project_name}")
            logger.info(f"Phoenix endpoint: {phoenix_endpoint}")
            self.tracer_provider = register(
                project_name=project_name,
                endpoint=phoenix_endpoint,
            )

            # Manual instrumentation for Bedrock
            logger.info("Instrumenting AWS Bedrock...")
            BedrockInstrumentor().instrument(tracer_provider=self.tracer_provider)

            # Manual instrumentation for LangChain
            logger.info("Instrumenting LangChain...")
            LangChainInstrumentor().instrument(
                tracer_provider=self.tracer_provider,
                skip_dep_check=True
            )

            self._initialized = True
            logger.info("Phoenix observability initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Phoenix observability: {str(e)}")
            # Don't raise - allow app to continue without observability

    def shutdown(self):
        """Shutdown Phoenix and cleanup resources"""
        # Force flush any pending spans before shutdown
        if self.tracer_provider:
            try:
                logger.info("Flushing pending traces...")
                self.tracer_provider.force_flush(timeout_millis=5000)
            except Exception as e:
                logger.error(f"Error flushing traces: {str(e)}")

        if self.phoenix_session:
            try:
                logger.info("Shutting down Phoenix session...")
                # Phoenix sessions auto-cleanup, but we can explicitly close if needed
                self.phoenix_session = None
            except Exception as e:
                logger.error(f"Error shutting down Phoenix: {str(e)}")

        self._initialized = False
        logger.info("Phoenix observability shutdown complete")

    def is_initialized(self) -> bool:
        """Check if Phoenix is initialized"""
        return self._initialized

    def get_tracer(self, name: str = __name__):
        """Get an OpenTelemetry tracer for custom spans"""
        if not self._initialized:
            logger.warning("Phoenix not initialized, returning no-op tracer")
        return trace_api.get_tracer(name)


# Global Phoenix instance
phoenix_observability = PhoenixObservability()


def get_tracer(name: str = __name__):
    """Convenience function to get a tracer"""
    return phoenix_observability.get_tracer(name)
