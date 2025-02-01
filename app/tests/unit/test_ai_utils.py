import pytest
from ai_utils.chatbot_utils import AI_Generator, QA_Feedback_Model
from unittest.mock import patch, MagicMock, AsyncMock
from openai import AzureOpenAI
import json
import asyncio

@pytest.fixture
def ai_generator():
    """Fixture that provides an AI_Generator instance for testing."""
    from app.ai_utils.chatbot_utils import AI_Generator
    return AI_Generator()

@pytest.fixture(autouse=True)
async def mock_azure_openai():
    # Mock responses
    mock_questions_data = {
        "qas": [{"question": "Test question?", "ideal_answer": "Test answer"}]
    }
    
    mock_feedback_data = {
        "question": "Test question?",
        "original_user_answer": "Test answer",
        "ai_feedback": {
            "content": {"rating": 8.0, "feedback": "Good answer"},
            "coherence": {"rating": 7.0, "feedback": "Well structured"},
            "confidence": {"rating": 7.0, "feedback": "Good confidence"},
            "relevance": {"rating": 8.0, "feedback": "Very relevant"},
            "professionalism": {"rating": 8.0, "feedback": "Professional"},
            "appropriateness": {"rating": 8.0, "feedback": "Appropriate"},
            "overall_summary": {"rating": 7.5, "feedback": "Overall good"}
        }
    }
    
    # Create a mock response for structured output
    class MockResponse:
        def __init__(self, data):
            self._data = data
        
        def model_dump_json(self):
            return json.dumps(self._data)
        
        def dict(self):
            return self._data
    
    class MockAzureChatOpenAI:
        def __init__(self, *args, **kwargs):
            pass
        
        def with_structured_output(self, schema):
            structured_model = AsyncMock()
            
            async def mock_invoke(messages):
                if schema.__name__ == 'InterviewQuestions':
                    return MockResponse(mock_questions_data)
                elif schema.__name__ == 'QA':
                    return MockResponse(mock_feedback_data)
                return MockResponse({})
            
            structured_model.invoke = mock_invoke
            return structured_model
        
        async def _generate(self, *args, **kwargs):
            return mock_questions_data
        
        def _create_chat_result(self, *args, **kwargs):
            return mock_questions_data
    
    # Apply the patch
    with patch('langchain_openai.AzureChatOpenAI', MockAzureChatOpenAI):
        yield MockAzureChatOpenAI

class TestAIGenerator:
    """Test suite for AI_Generator class."""
    
    @pytest.mark.asyncio
    async def test_generate_questions(self, ai_generator, mock_azure_openai):
        """
        Test question generation functionality.

        Should successfully generate interview questions using Azure OpenAI.

        Args:
            ai_generator: The generator instance
            mock_azure_openai: Mocked Azure OpenAI client
        """
        mock_response = {
            "qas": [{"question": "Test question?", "ideal_answer": "Test answer"}]
        }

        # Create a mock structured output model
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(dict=lambda: mock_response))
        ai_generator.question_generator_model.with_structured_output = MagicMock(return_value=mock_model)

        result = await ai_generator.generate_questions("test input")
        assert isinstance(result, dict)
        assert "qas" in result
        assert len(result["qas"]) > 0

    @pytest.mark.asyncio
    async def test_generate_q_feedback(self, ai_generator, mock_azure_openai):
        """
        Test answer feedback generation.

        Should successfully generate feedback for interview answers using Azure OpenAI.

        Args:
            ai_generator: The generator instance
            mock_azure_openai: Mocked Azure OpenAI client
        """
        expected_feedback = {
            "question": "Test question?",
            "original_user_answer": "Test answer",
            "ai_feedback": {
                "content": {"rating": 8.0, "feedback": "Good answer"},
                "coherence": {"rating": 7.0, "feedback": "Well structured"},
                "confidence": {"rating": 7.0, "feedback": "Good confidence"},
                "relevance": {"rating": 8.0, "feedback": "Very relevant"},
                "professionalism": {"rating": 8.0, "feedback": "Professional"},
                "appropriateness": {"rating": 8.0, "feedback": "Appropriate"},
                "overall_summary": {"rating": 7.5, "feedback": "Overall good"}
            }
        }

        # Create a mock structured output model
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(dict=lambda: expected_feedback))
        ai_generator.question_feedback_generator_model.with_structured_output = MagicMock(return_value=mock_model)

        result = await ai_generator.generate_q_feedback("test input")
        assert isinstance(result, dict)
        assert "ai_feedback" in result
        assert result["ai_feedback"]["content"]["rating"] == 8.0