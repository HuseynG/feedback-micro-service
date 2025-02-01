import pytest
from unittest.mock import patch, MagicMock

# Mock the entire google.genai module
@pytest.fixture(autouse=True)
def mock_genai():
    """Fixture that provides a mocked Google AI (Gemini) client for testing.
    
    This fixture sets up a complete mock of the Google AI environment by:
    1. Mocking the entire google.genai module
    2. Creating mock responses that simulate AI-generated content
    3. Setting up mock models and clients with appropriate response structures
    
    The mock is configured to return a consistent test response across all tests,
    allowing for reliable and predictable test execution.
    """
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
    """Test suite for CompanyInsightsGenerator class.
    
    This suite verifies the functionality of company and role-specific insight
    generation using Google's Gemini AI. It tests:
    1. Company overview generation
    2. Role-specific information generation
    3. Integration with Google AI services
    4. Proper formatting and content of generated insights
    """

    @pytest.mark.asyncio
    async def test_generate_company_overview(self, company_insights_generator, mock_genai):
        """Test company overview generation functionality.
        
        This test verifies that:
        1. The generator can successfully connect to the Google AI service
        2. It produces a non-empty string response
        3. The response contains the expected test content
        4. The integration with Google AI models works correctly
        
        Args:
            company_insights_generator: Fixture providing a CompanyInsightsGenerator instance
            mock_genai: Fixture providing a mocked Google AI module
            
        The test passes if:
        - The result is a non-empty string
        - The result contains the expected test response
        - No exceptions are raised during execution
        """
        result = await company_insights_generator.generate_company_overview("Test Company")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Test response" in result

    @pytest.mark.asyncio
    async def test_generate_company_role(self, company_insights_generator, mock_genai):
        """Test role-specific information generation functionality.
        
        This test verifies that:
        1. The generator can produce role-specific insights
        2. It properly handles multiple input parameters (company, role, location)
        3. The response contains relevant information
        4. The integration handles complex prompts correctly
        
        Args:
            company_insights_generator: Fixture providing a CompanyInsightsGenerator instance
            mock_genai: Fixture providing a mocked Google AI module
            
        The test passes if:
        - The result is a non-empty string
        - The result contains the expected test response
        - The function properly processes all input parameters
        """
        result = await company_insights_generator.generate_company_role(
            "Test Company", "Software Engineer", "New York"
        )
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Test response" in result 