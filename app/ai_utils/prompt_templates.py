# app/ai_utils/chatbot_utils.py
question_generator_model_system_prompt_template = """Your are a helpful AI assistant that needs to generate interview questions and ideal answers for the user based on the given info. Your response must be in JSON format."""
question_generator_model_user_prompt_template = """Please generate interview questions and ideal answers base on the following information: {text}"""


question_feedback_generator_model_system_prompt_template = """Your are a helpful AI assistant that needs to generate generate feedback for given question. Your response must be in JSON format."""
question_feedback_generator_model_user_prompt_template = """Please generate feedback for given question from the user based on the given info. You must provide feedback 
to the question from the following perspectives:
    - content of the response
    - coherence of the response
    - confidence in the response
    - relevance of the response
    - professionalism of the response
    - appropriateness of the response
    - overall summary of the feedback you have provided based on the points of given above.

Your response must be in JSON format. In addition you need to provide the AI modified version of the user answer (ai_modified_user_answer). Here is the information for your feedback generation:

{text}"""

follow_up_question_generator_model_system_prompt_template = """
You are a helpful AI assistant tasked with generating at least 5 follow-up interview questions and their ideal answers based on the provided information. Your response must be in JSON format, following the specified structure.
"""

follow_up_question_generator_model_user_prompt_template = """
Please generate at least 5 follow-up interview questions and ideal answers based on the following information: {text}

Your response must be in the following JSON format.


"question": "First follow-up question",
"original_user_answer": "The answer provided by the user.",
"ai_modified_user_answer": "The AI-rectified user answer.",
"ideal_answer": "Ideal answer to the first follow-up question",
"ai_feedback": QA_Feedback_Model


Please ensure that the follow-up questions are engaging and directly related to the provided information. The fields "original_user_answer", "ai_modified_user_answer", and "ai_feedback" should be set to null.
"""
