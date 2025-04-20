from datetime import date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, HttpUrl, Field, field_validator


# -----------------------
# Section: CV (Resume) Data
# -----------------------

class PersonalInfo(BaseModel):
    """
    Basic personal/contact details that an ATS or recruiter would look for.
    """
    full_name: str = Field(
        alias='full_name',
        description="Full name of the candidate"
    )
    email: Optional[EmailStr] = Field(
        default=None,
        alias='email',
        description="Email address"
    )
    phone_number: Optional[str] = Field(
        default=None,
        alias='phone_number',
        description="Contact phone number with country code"
    )
    address: Optional[str] = Field(
        default=None,
        alias='address',
        description="Street address"
    )
    city: Optional[str] = Field(
        default=None,
        alias='city',
        description="City of residence"
    )
    state: Optional[str] = Field(
        default=None,
        alias='state',
        description="State/Province/Region"
    )
    country: Optional[str] = Field(
        default=None,
        alias='country',
        description="Country of residence"
    )
    postal_code: Optional[str] = Field(
        default=None,
        alias='postal_code',
        description="Postal/ZIP code"
    )
    urls: List[HttpUrl] = Field(
        default_factory=list,
        alias='urls',
        description="List of relevant URLs (e.g., LinkedIn, GitHub, personal website, etc.)"
    )


class Education(BaseModel):
    """
    Details regarding academic background.
    """
    institution: str = Field(
        alias='institution',
        description="Name of the educational institution"
    )
    degree: Optional[str] = Field(
        default=None,
        alias='degree',
        description="Type of degree obtained (e.g., 'Bachelor of Science')"
    )
    field_of_study: Optional[str] = Field(
        default=None,
        alias='field_of_study',
        description="Major or field of study"
    )
    start_date: Optional[date] = Field(
        default=None,
        alias='start_date',
        description="Start date of education"
    )
    end_date: Optional[date] = Field(
        default=None,
        alias='end_date',
        description="End date of education or expected graduation date"
    )
    grade: Optional[str] = Field(
        default=None,
        alias='grade',
        description="Grade achieved or expected (e.g., GPA, First Class, Distinction)"
    )
    location: Optional[str] = Field(
        default=None,
        alias='location',
        description="Location of the institution"
    )

    @field_validator('end_date', 'start_date', mode='before')
    @classmethod
    def validate_date_fields(cls, v):
        if isinstance(v, str) and v.lower() in ['present', 'current', 'now', 'ongoing']:
            return None
        return v


class WorkExperience(BaseModel):
    """
    Professional history, including role, company, dates, and responsibilities.
    """
    job_title: str = Field(
        alias='job_title',
        description="Title of the position held"
    )
    company_name: str = Field(
        alias='company_name',
        description="Name of the employer/company"
    )
    start_date: Optional[date] = Field(
        default=None,
        alias='start_date',
        description="Start date of employment"
    )
    end_date: Optional[date] = Field(
        default=None,
        alias='end_date',
        description="End date of employment (null if current)"
    )
    location: Optional[str] = Field(
        default=None,
        alias='location',
        description="Location of employment"
    )
    description: Optional[str] = Field(
        default=None,
        alias='description',
        description="Description of responsibilities and achievements"
    )
    currently_working: bool = Field(
        default=False,
        alias='currently_working',
        description="Indicates if this is the current job"
    )

    @field_validator('end_date', mode='before')
    @classmethod
    def validate_end_date(cls, v):
        if isinstance(v, str) and v.lower() in ['present', 'current', 'now', 'ongoing']:
            return None
        return v


class Project(BaseModel):
    """
    Significant projects, either professional or personal (e.g., open-source).
    """
    name: str = Field(
        alias='name',
        description="Name of the project"
    )
    description: Optional[str] = Field(
        default=None,
        alias='description',
        description="Detailed description of the project"
    )
    technologies_used: List[str] = Field(
        default_factory=list,
        alias='technologies_used',
        description="List of technologies and tools used"
    )
    start_date: Optional[date] = Field(
        default=None,
        alias='start_date',
        description="Project start date"
    )
    end_date: Optional[date] = Field(
        default=None,
        alias='end_date',
        description="Project end date"
    )
    link: Optional[HttpUrl] = Field(
        default=None,
        alias='link',
        description="URL to project (e.g., GitHub repository)"
    )


class Certification(BaseModel):
    """
    Certifications from recognized bodies (e.g., PMP, AWS, etc.).
    """
    name: str = Field(
        alias='name',
        description="Name of the certification"
    )
    issuing_organization: Optional[str] = Field(
        default=None,
        alias='issuing_organization',
        description="Organization that issued the certification"
    )
    issue_date: Optional[date] = Field(
        default=None,
        alias='issue_date',
        description="Date when certification was issued"
    )
    expiration_date: Optional[date] = Field(
        default=None,
        alias='expiration_date',
        description="Expiration date of certification"
    )
    credential_id: Optional[str] = Field(
        default=None,
        alias='credential_id',
        description="Unique identifier for the certification"
    )
    credential_url: Optional[HttpUrl] = Field(
        default=None,
        alias='credential_url',
        description="URL to verify the certification"
    )
    
    @field_validator('issue_date', 'expiration_date', mode='before')
    @classmethod
    def validate_date_fields(cls, v):
        if isinstance(v, str) and v.lower() in ['present', 'current', 'now', 'ongoing', 'no expiration', 'never']:
            return None
        return v


class AwardAchievement(BaseModel):
    """
    Awards, recognitions, competitions, or notable achievements.
    """
    title: str = Field(
        alias='title',
        description="Title of the award or achievement"
    )
    issuer: Optional[str] = Field(
        default=None,
        alias='issuer',
        description="Organization that granted the award"
    )
    date_awarded: Optional[date] = Field(
        default=None,
        alias='date_awarded',
        description="Date when the award was received"
    )
    description: Optional[str] = Field(
        default=None,
        alias='description',
        description="Description of the award and its significance"
    )
    
    @field_validator('date_awarded', mode='before')
    @classmethod
    def validate_date_fields(cls, v):
        if isinstance(v, str) and v.lower() in ['present', 'current', 'now', 'ongoing']:
            return None
        return v


class Publication(BaseModel):
    """
    Publications such as academic papers, articles, or books.
    """
    title: str = Field(
        alias='title',
        description="Title of the publication"
    )
    publisher: Optional[str] = Field(
        default=None,
        alias='publisher',
        description="Name of the publisher or journal"
    )
    publication_date: Optional[date] = Field(
        default=None,
        alias='publication_date',
        description="Date of publication"
    )
    link: Optional[HttpUrl] = Field(
        default=None,
        alias='link',
        description="URL to access the publication"
    )
    description: Optional[str] = Field(
        default=None,
        alias='description',
        description="Brief description or abstract"
    )
    
    @field_validator('publication_date', mode='before')
    @classmethod
    def validate_date_fields(cls, v):
        if isinstance(v, str) and v.lower() in ['present', 'current', 'now', 'ongoing', 'forthcoming', 'in press']:
            return None
        return v


class LanguageProficiency(BaseModel):
    """
    Languages and their proficiency levels.
    """
    language: str = Field(
        alias='language',
        description="Name of the language"
    )
    proficiency: Optional[str] = Field(
        default=None,
        alias='proficiency',
        description="Proficiency level (e.g., 'Native', 'Fluent', 'Intermediate')"
    )


class Reference(BaseModel):
    """
    Professional references or contacts.
    """
    name: str = Field(
        alias='name',
        description="Name of the reference"
    )
    relationship: Optional[str] = Field(
        default=None,
        alias='relationship',
        description="Professional relationship (e.g., 'Former Manager')"
    )
    email: Optional[EmailStr] = Field(
        default=None,
        alias='email',
        description="Email contact of the reference"
    )
    phone: Optional[str] = Field(
        default=None,
        alias='phone',
        description="Phone number of the reference"
    )


class Skill(BaseModel):
    """
    Skills or keywords that an ATS typically matches.
    """
    name: str = Field(
        alias='name',
        description="Name of the skill"
    )
    category: Optional[str] = Field(
        default=None,
        alias='category',
        description="Category of the skill (e.g., 'Programming Language', 'Soft Skill')"
    )
    proficiency_level: Optional[str] = Field(
        default=None,
        alias='proficiency_level',
        description="Level of proficiency in the skill"
    )
    years_of_experience: Optional[float] = Field(
        default=None,
        alias='years_of_experience',
        description="Years of experience with this skill"
    )


class CV(BaseModel):
    """
    Comprehensive CV model capturing all major fields.
    """
    personal_info: PersonalInfo = Field(
        alias='personal_info',
        description="Personal and contact information"
    )
    headline: Optional[str] = Field(
        default=None,
        alias='headline',
        description="Professional headline or title"
    )
    summary: Optional[str] = Field(
        default=None,
        alias='summary',
        description="Professional summary or objective"
    )
    education: List[Education] = Field(
        default_factory=list,
        alias='education',
        description="Educational background"
    )
    work_experience: List[WorkExperience] = Field(
        default_factory=list,
        alias='work_experience',
        description="Professional work history"
    )
    projects: List[Project] = Field(
        default_factory=list,
        alias='projects',
        description="Notable projects"
    )
    certifications: List[Certification] = Field(
        default_factory=list,
        alias='certifications',
        description="Professional certifications"
    )
    awards_achievements: List[AwardAchievement] = Field(
        default_factory=list,
        alias='awards_achievements',
        description="Awards and achievements"
    )
    publications: List[Publication] = Field(
        default_factory=list,
        alias='publications',
        description="Published works"
    )
    languages: List[LanguageProficiency] = Field(
        default_factory=list,
        alias='languages',
        description="Language proficiencies"
    )
    references: List[Reference] = Field(
        default_factory=list,
        alias='references',
        description="Professional references"
    )
    skills: List[Skill] = Field(
        default_factory=list,
        alias='skills',
        description="Professional skills and competencies"
    )


# -----------------------
# Section: General CV Analysis Stats
# -----------------------

class ContentPair(BaseModel):
    """Base model for before/after content pairs"""
    current: str
    improved: str | None = None
    enhanced: str | None = None
    recommended: str | None = None
    simplified: str | None = None
    replaceWith: str | None = None
    changeTo: str | None = None
    suggestedAddition: str | None = None

class SectionContent(BaseModel):
    """Content structure with title and before/after content"""
    title: str
    content: ContentPair

class ActionableRecommendation(BaseModel):
    """Structure for actionable recommendations"""
    section: str
    current: str
    replaceWith: str

class WowFactorOpportunity(BaseModel):
    """Structure for wow factor opportunities"""
    currentState: str
    suggestedAddition: str

class AdditionalObservation(BaseModel):
    """Structure for additional observations"""
    observation: str
    solution: str

class SectionModification(BaseModel):
    """Structure for section-specific modifications"""
    current: str
    changeTo: str

class IndustrySpecificInsight(BaseModel):
    """Structure for industry-specific insights"""
    industry: str
    relevantTrends: List[str]
    keywordRecommendations: List[str]
    industrySpecificStrengths: List[str]
    industrySpecificGaps: List[str]
    competitiveAdvantage: str

class SkillAssessment(BaseModel):
    """Structure for individual skill assessment"""
    skillName: str
    currentLevel: int  # 1-10 scale
    marketDemand: int  # 1-10 scale
    improvement: str
    relevantCertifications: List[str] = Field(default_factory=list)

class SkillsGapAnalysis(BaseModel):
    """Structure for comprehensive skills gap analysis"""
    coreSkills: List[SkillAssessment]
    missingCriticalSkills: List[str]
    overallSkillScore: int  # 1-100 scale
    skillsDistribution: Dict[str, int]  # Category -> Percentage
    recommendedUpskilling: List[str]
    skillsMarketRelevance: str

class CareerPathOption(BaseModel):
    """Structure for a potential career path option"""
    title: str
    timeframe: str  # e.g., "Short-term (1-2 years)"
    requiredSkills: List[str]
    potentialEmployers: List[str]
    estimatedSalaryRange: str
    growthPotential: str

class CareerTrajectoryAnalysis(BaseModel):
    """Structure for analyzing career trajectory and future opportunities"""
    currentCareerStage: str
    careerProgression: str  # Analysis of progression so far
    growthRate: str  # e.g., "Above average for industry"
    potentialPaths: List[CareerPathOption]
    recommendedNextSteps: List[str]
    longTermOutlook: str

class CVAnalysisStats(BaseModel):
    """
    Comprehensive analysis statistics and metrics for a CV with frontend-friendly structure
    """
    overall_content_ats_readiness: SectionContent = Field(
        default_factory=lambda: SectionContent(
            title="Overall Content ATS Readiness",
            content=ContentPair(current="", improved="")
        ),
        description="Assessment of how well the CV is optimized for ATS systems"
    )
    design_layout_visual_appeal: SectionContent = Field(
        default_factory=lambda: SectionContent(
            title="Design Layout & Visual Appeal",
            content=ContentPair(current="", recommended="")
        ),
        description="Evaluation of CV's visual design and layout effectiveness"
    )
    branding_personal_presentation: SectionContent = Field(
        default_factory=lambda: SectionContent(
            title="Branding & Personal Presentation",
            content=ContentPair(current="", enhanced="")
        ),
        description="Analysis of personal branding and professional presentation"
    )
    clarity_and_conciseness: SectionContent = Field(
        default_factory=lambda: SectionContent(
            title="Clarity & Conciseness",
            content=ContentPair(current="", simplified="")
        ),
        description="Assessment of content clarity with specific examples"
    )
    industry_specific_analysis: Optional[IndustrySpecificInsight] = Field(
        default=None,
        description="Industry-specific analysis and recommendations"
    )
    skills_gap_analysis: Optional[SkillsGapAnalysis] = Field(
        default=None,
        description="Detailed analysis of skills with market relevance scoring"
    )
    career_trajectory: Optional[CareerTrajectoryAnalysis] = Field(
        default=None,
        description="Analysis of career progression and future opportunities"
    )
    wow_factor_opportunities: List[WowFactorOpportunity] = Field(
        default_factory=list,
        description="List of opportunities to make the CV stand out"
    )
    additional_observations: List[AdditionalObservation] = Field(
        default_factory=list,
        description="List of additional insights and their solutions"
    )
    actionable_recommendations: List[ActionableRecommendation] = Field(
        default_factory=list,
        description="List of specific recommendations with section, current text, and replacement"
    )
    specific_modifications: Dict[str, SectionModification] = Field(
        default_factory=dict,
        description="Dictionary of sections and their specific modifications"
    )

    @field_validator('specific_modifications', mode='before')
    @classmethod
    def validate_specific_modifications(cls, v):
        if isinstance(v, dict):
            result = {}
            for k, modification in v.items():
                if isinstance(modification, list):
                    # Extract current and changeTo from the list item
                    mod_text = modification[0]
                    current = mod_text.split('Change to:')[0].replace('Current:', '').strip()
                    change_to = mod_text.split('Change to:')[1].strip()
                    result[k] = {'current': current, 'changeTo': change_to}
                elif isinstance(modification, dict):
                    result[k] = modification
                else:
                    raise ValueError(f"Invalid modification format for section {k}")
            return result
        return v


# -----------------------
# Section: Job Requirements / ATS
# -----------------------

class ATSJobRequirement(BaseModel):
    """
    Represents a target job description for which the resume is being matched.
    """
    job_title: str = Field(
        alias='job_title',
        description="Title of the job position"
    )
    job_description: Optional[str] = Field(
        default=None,
        alias='job_description',
        description="Detailed job description"
    )
    required_skills: List[str] = Field(
        default_factory=list,
        alias='required_skills',
        description="List of required skills for the position"
    )
    optional_skills: List[str] = Field(
        default_factory=list,
        alias='optional_skills',
        description="List of preferred but not required skills"
    )
    location: Optional[str] = Field(
        default=None,
        alias='location',
        description="Job location"
    )


# -----------------------
# Section: Analysis Results
# -----------------------

class CVMatchDetail(BaseModel):
    """
    Provides detailed information on how well the CV matches a certain skill.
    """
    skill: str = Field(
        alias='skill',
        description="Name of the skill being matched"
    )
    matched: bool = Field(
        alias='matched',
        description="Whether the skill was found in the CV"
    )


class CVAnalysisResult(BaseModel):
    """
    The output of analyzing a CV against ATS job requirements and best practices.
    """
    cv: CV = Field(
        alias='cv',
        description="The analyzed CV"
    )
    ats_job: ATSJobRequirement = Field(
        alias='ats_job',
        description="The job requirements used for analysis"
    )
    overall_match_score: float = Field(
        alias='overall_match_score',
        description="Overall match score (0.0 to 100.0)"
    )
    matched_keywords: List[CVMatchDetail] = Field(
        default_factory=list,
        alias='matched_keywords',
        description="Skills/keywords found in CV"
    )
    missing_keywords: List[str] = Field(
        default_factory=list,
        alias='missing_keywords',
        description="Required skills/keywords not found in CV"
    )
    strengths: List[str] = Field(
        default_factory=list,
        alias='strengths',
        description="Key strengths identified in the CV"
    )
    areas_for_improvement: List[str] = Field(
        default_factory=list,
        alias='areas_for_improvement',
        description="Areas where the CV could be improved"
    )
    notes: Optional[str] = Field(
        default=None,
        alias='notes',
        description="Additional analysis notes or recommendations"
    )
