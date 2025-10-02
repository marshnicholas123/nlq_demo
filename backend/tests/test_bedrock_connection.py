import pytest
from unittest.mock import patch, MagicMock
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.services.bedrock_client import BedrockClient
from app.config import settings


class TestBedrockConnection:
    """Test suite for Bedrock LLM connection"""
    
    def test_settings_loaded(self):
        """Test that required settings are loaded from .env"""
        # Verify settings exist (but don't assert specific values)
        assert settings.aws_region is not None
        assert settings.aws_access_key_id is not None
        assert settings.bedrock_model_id is not None
        assert len(settings.aws_region) > 0
        assert len(settings.aws_access_key_id) > 0
        assert len(settings.bedrock_model_id) > 0

    @patch('boto3.client')
    def test_bedrock_client_initialization_mocked(self, mock_boto3_client):
        """Test BedrockClient initialization with mocked boto3"""
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        client = BedrockClient()
        
        # Verify boto3 client was created with correct parameters
        mock_boto3_client.assert_called_once_with('bedrock-runtime', region_name=settings.aws_region)
        assert client.model_id == settings.bedrock_model_id

    def test_invoke_model_real_connection(self):
        """Test invoke_model with actual Bedrock connection"""
        # Create client and invoke model with real connection
        client = BedrockClient()
        result = client.invoke_model(
            prompt="Show me all operational nuclear power plants",
            system="You are an expert SQL generator for nuclear power plant databases.",
            max_tokens=4000
        )
        print(result)
        
        # Verify we got a response (any string is acceptable)
        assert isinstance(result, str)
        assert len(result) > 0

