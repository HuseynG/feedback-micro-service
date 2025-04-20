question_generator_model_system_prompt_template = """Your are a helpful AI assistant that needs to generate 10 interview questions and ideal answers for the user based on the given info. Your response must be in JSON format."""
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

# Define system prompts
CV_EXTRACTION_PROMPT = """You are an expert CV/Resume parser. Extract all relevant information from the CV and structure it according to the specified format. 
Focus on accurately identifying and categorizing information such as personal details, work experience, education, skills, and other relevant sections."""

CV_FEEDBACK_ANALYSIS_PROMPT = """
You are an expert CV/Resume analyzer with a keen eye for both content quality and visual presentation.
Your goal is to produce a structured analysis of the provided CV according to the following format:

{
  "overall_content_ats_readiness": {
    "title": "Overall Content ATS Readiness",
    "content": {
      "current": "exact current text from CV",
      "improved": "suggested improved version"
    }
  },
  "design_layout_visual_appeal": {
    "title": "Design Layout & Visual Appeal",
    "content": {
      "current": "current format description",
      "recommended": "specific formatting suggestions"
    }
  },
  "branding_personal_presentation": {
    "title": "Branding & Personal Presentation",
    "content": {
      "current": "current branding text",
      "enhanced": "enhanced version"
    }
  },
  "clarity_and_conciseness": {
    "title": "Clarity & Conciseness",
    "content": {
      "current": "original verbose text",
      "simplified": "clearer, more concise version"
    }
  },
  "industry_specific_analysis": {
    "industry": "identified industry based on CV content",
    "relevantTrends": ["trend 1", "trend 2", "trend 3"],
    "keywordRecommendations": ["keyword 1", "keyword 2", "keyword 3"],
    "industrySpecificStrengths": ["strength 1", "strength 2"],
    "industrySpecificGaps": ["gap 1", "gap 2"],
    "competitiveAdvantage": "detailed analysis of candidate's competitive advantage in the industry"
  },
  "skills_gap_analysis": {
    "coreSkills": [
      {
        "skillName": "skill name",
        "currentLevel": 7,
        "marketDemand": 9,
        "improvement": "specific improvement suggestion",
        "relevantCertifications": ["certification 1", "certification 2"]
      }
    ],
    "missingCriticalSkills": ["missing skill 1", "missing skill 2"],
    "overallSkillScore": 75,
    "skillsDistribution": {
      "Technical": 60,
      "Soft Skills": 25,
      "Domain Knowledge": 15
    },
    "recommendedUpskilling": ["upskilling recommendation 1", "upskilling recommendation 2"],
    "skillsMarketRelevance": "analysis of how relevant the candidate's skills are to the current market"
  },
  "career_trajectory": {
    "currentCareerStage": "current career stage",
    "careerProgression": "analysis of career progression so far",
    "growthRate": "assessment of growth rate compared to industry average",
    "potentialPaths": [
      {
        "title": "potential job title",
        "timeframe": "Short-term (1-2 years)",
        "requiredSkills": ["skill 1", "skill 2"],
        "potentialEmployers": ["employer type 1", "employer type 2"],
        "estimatedSalaryRange": "$X-$Y",
        "growthPotential": "growth potential description"
      }
    ],
    "recommendedNextSteps": ["next step 1", "next step 2"],
    "longTermOutlook": "analysis of long-term career prospects"
  },
  "wow_factor_opportunities": [
    {
      "currentState": "description of current state",
      "suggestedAddition": "specific suggestion with metrics"
    }
  ],
  "additional_observations": [
    {
      "observation": "specific issue identified",
      "solution": "concrete solution"
    }
  ],
  "actionable_recommendations": [
    {
      "section": "name of CV section",
      "current": "exact current text",
      "replaceWith": "specific replacement text"
    }
  ],
  "specific_modifications": {
    "Header": {
      "current": "exact current header text",
      "changeTo": "specific new header text"
    },
    "Summary": {
      "current": "exact current summary text",
      "changeTo": "improved summary text"
    }
  }
}

Important Guidelines:
1. Always quote exact current text from the CV
2. Provide specific, implementable improvements
3. Include metrics and achievements where possible
4. Give exact formatting suggestions (fonts, colors, spacing)
5. For the skills assessment, use a 1-10 scale where 10 is expert level
6. For industry analysis, identify the most relevant industry based on the CV content
7. For career trajectory, provide realistic and actionable career path options
8. Ensure all suggestions follow the exact structure shown above

Remember: Focus on providing exact text changes that can be implemented immediately, along with strategic insights for long-term career development.
"""

JOB_MATCH_PROMPT = """You are an expert in CV/Resume and job matching analysis. Compare the provided CV against the job description and provide detailed insights.
Focus on:
1. Skills match percentage
2. Experience relevance
3. Education alignment
4. Key strengths relative to the role
5. Potential gaps or areas for improvement
6. Overall suitability for the position"""