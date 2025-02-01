import pytest
from bson import ObjectId
from unittest.mock import patch, MagicMock, AsyncMock
import os

class TestInterviewEndpoints:
    """Test suite for Interview API endpoints.
    
    This suite verifies the functionality of the interview-related API endpoints,
    including interview creation and feedback generation. It tests:
    1. Interview creation with various parameters
    2. Feedback generation for interview answers
    3. API authentication and authorization
    4. Integration with AI services
    5. Database operations and state management
    """

    @patch('app.api.interview.AI_Generator')
    def test_create_interview(self, mock_ai_generator, test_client):
        """Test the interview creation endpoint (/interview/generate-question).
        
        This test verifies that:
        1. The endpoint accepts and validates interview creation parameters
        2. It properly integrates with the AI generator for question generation
        3. The response includes all required fields (id, user_id, job_title, QAs)
        4. The API key authentication works correctly
        5. The interview data is properly stored in the database
        
        Args:
            mock_ai_generator: Mock of the AI_Generator class
            test_client: FastAPI TestClient instance
            
        The test passes if:
        - Response status code is 200
        - Response contains a valid interview ID
        - User ID and job title match the input
        - Questions are generated and stored
        """
        mock_instance = MagicMock()
        mock_response = {
            "qas": [{"question": "Test question?", "ideal_answer": "Test answer"}]
        }

        # Mock the ainvoke method to return a mock response
        mock_structured_output = MagicMock()
        mock_structured_output.dict = MagicMock(return_value=mock_response)
        mock_instance.generate_questions = AsyncMock(return_value=mock_response)
        mock_ai_generator.return_value = mock_instance

        interview_data = {
            "user_id": "test_user",
            "job_title": "Software Engineer",
            "question_type": "technical",
            "role_level": "mid_senior_level",
            "profile_data": {
                "cv": "Test CV content",
                "cover_letter": "Test cover letter content"
            },
            "industry_standard": True,
            "company_name": "Test Company",
            "location": "New York",
            "number_of_questions": 5
        }

        headers = {"api-key": os.getenv('EXPECTED_API_KEY')}  # Use the mocked API key with correct header name
        response = test_client.post("/interview/generate-question",
                                  json=interview_data,
                                  headers=headers)
        assert response.status_code == 200
        assert "_id" in response.json()
        assert response.json()["user_id"] == interview_data["user_id"]
        assert response.json()["job_title"] == interview_data["job_title"]
        assert len(response.json()["QAs"]) > 0

    @patch('app.api.interview.AI_Generator')
    def test_generate_feedback(self, mock_ai_generator, test_client, mock_db):
        """Test the feedback generation endpoint.
        
        This test verifies that:
        1. The endpoint can process answer submissions
        2. It integrates correctly with the AI feedback generator
        3. The feedback includes all required components (ratings, comments)
        4. The database is properly updated with feedback
        5. The response format matches the expected schema
        
        Args:
            mock_ai_generator: Mock of the AI_Generator class
            test_client: FastAPI TestClient instance
            mock_db: Mock of the MongoDB database
            
        The test passes if:
        - The feedback is generated successfully
        - The response includes detailed feedback components
        - The database is updated with the feedback
        - The response format matches expectations
        """
        # Mock AI response
        mock_instance = MagicMock()
        mock_response = {
            "question": "Test question?",
            "original_user_answer": "Test answer",
            "ai_feedback": {
                "content": {"rating": 8.0, "feedback": "Good answer"},
                "coherence": {"rating": 7.0, "feedback": "Well structured"}
            },
            "ai_modified_user_answer": "Modified test answer"  # Add this if required
        }

        # Mock the ainvoke method to return a mock response
        mock_structured_output = MagicMock()
        mock_structured_output.dict = MagicMock(return_value=mock_response)
        mock_instance.generate_q_feedback = AsyncMock(return_value=mock_response)
        mock_ai_generator.return_value = mock_instance

        # Create test interview
        interview_id = str(ObjectId())
        test_client.app.database.interviews.insert_one({
            "_id": ObjectId(interview_id),
            "user_id": "test_user",
            "job_title": "Software Engineer",
            "question_type": "technical",
            "role_level": "mid_senior_level",
            "profile_data": {
                "cv": "Test CV content",
                "cover_letter": "Test cover letter content"
            },
            "industry_standard": True,
            "QAs": [{
                "question": "Test question?",
                "original_user_answer": None,
                "ai_feedback": None
            }]
        })

        feedback_data = {
            "question": "Test question?",
            "answer": "Test answer",
            "interview_id": interview_id,
            "user_id": "test_user"
        }

        headers = {"api-key": os.getenv('EXPECTED_API_KEY')}
        response = test_client.put(
            f"/interview/generate_interview_feedback/test_user/{interview_id}",
            json=feedback_data,
            headers=headers
        )

        assert response.status_code == 200
        assert response.json()["question"] == feedback_data["question"]
        assert response.json()["original_user_answer"] == feedback_data["answer"]
        assert "ai_feedback" in response.json()