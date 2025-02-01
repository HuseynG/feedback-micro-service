import pytest
from unittest.mock import patch, MagicMock

# Mock the entire google.genai module
@pytest.fixture(autouse=True)
def mock_genai():
    with patch('app.ai_utils.company_insights_utils.genai') as mock:
        # Configure the mock with proper response structure
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Test response"
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        # Set up the models attribute
        mock_models = MagicMock()
        mock_models.generate_content.return_value = mock_response
        mock.models = mock_models
        
        # Set up the Client
        mock_client = MagicMock()
        mock_client.models = mock_models
        mock.Client.return_value = mock_client
        
        yield mock

@pytest.fixture
def company_insights_generator():
    """Fixture that provides a CompanyInsightsGenerator instance for testing."""
    from app.ai_utils.company_insights_utils import CompanyInsightsGenerator
    return CompanyInsightsGenerator()

class TestCompanyInsightsGenerator:
    """Test suite for CompanyInsightsGenerator class."""

    @pytest.mark.asyncio
    async def test_generate_company_overview(self, company_insights_generator, mock_genai):
        """
        Test company overview generation.
        
        Should successfully generate a company overview using the Google AI model.
        
        Args:
            company_insights_generator: The generator instance
            mock_genai: Mocked Google AI module
        """
        result = await company_insights_generator.generate_company_overview("Test Company")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Test response" in result

    @pytest.mark.asyncio
    async def test_generate_company_role(self, company_insights_generator, mock_genai):
        """
        Test company role information generation.
        
        Should successfully generate role-specific information using the Google AI model.
        
        Args:
            company_insights_generator: The generator instance
            mock_genai: Mocked Google AI module
        """
        result = await company_insights_generator.generate_company_role(
            "Test Company", "Software Engineer", "New York"
        )
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Test response" in result 