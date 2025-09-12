"""
pydantic model for chatbot

"""

from pydantic import BaseModel,Field
from typing import Optional, Any,List, Dict


class Requirements(BaseModel):
   minimum_gpa : Optional[float] = Field(None, description="Minimum GPA required for the course")
   prerequisites : Optional[List[str]] = Field(None, description="List of prerequisite courses")
   required_tests: List[str] = Field(..., description="List of required tests for the course")
   Scholarship_options: Optional[bool] = Field(None, description="Indicates if scholarship options are available")
   financial_aid: Optional[bool] = Field(None, description="Indicates if financial aid is available")
   application_deadlines: Optional[str] = Field(None, description="Application deadlines for the course")
   course_duration: Optional[str] = Field(None, description="Duration of the course")
   research_opportunities: Optional[bool] = Field(None, description="Indicates if research opportunities are available")

class University(BaseModel):
   name: str = Field(..., description="Name of the university")
   location: str = Field(..., description="Location of the university")
   ranking: Optional[int] = Field(None, description="Ranking of the university")
   requirements: Optional[Requirements] = Field(None, description="Requirements for the university")
   tuition_fees: Optional[float] = Field(None, description="Tuition fees for the university")
   programs_offered: Optional[List[str]] = Field(None, description="List of programs offered by the university")
   contact_information: Optional[Dict[str, Any]] = Field(None, description="Contact information for the university")
   website: Optional[str] = Field(None, description="Website of the university")

class UniversityFilters(BaseModel):
    max_tuition: Optional[float] = None
    min_rank: Optional[int] = None
    max_rank: Optional[int] = None
    location: Optional[str] = None
    programs: List[str] = []
    min_gpa: Optional[float] = None
    required_tests: List[str] = []
    scholarship_options: Optional[bool] = None
    financial_aid: Optional[bool] = None
    research_opportunities: Optional[bool] = None

class ChatMessage(BaseModel):
    role: Optional[str] = Field(None, description="Role of the message sender, e.g., user or bot")
    message: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: List[str] = []
    metadata: Optional[Dict[str, Any]] = None
    suggested_questions: List[str] = []

class GraphNode(BaseModel):
    id: str
    labels: List[str]
    properties: Dict[str, Any]

class GraphRelationship(BaseModel):
    id: str
    type: str
    start_node: str
    end_node: str
    properties: Dict[str, Any] = {}

class conversationSummary(BaseModel):
    conversation_id: str
    messages: List[Dict[str, str]] = []
    user_preferences: Dict[str, Any] = {}
    created_at: str
    last_updated: str

class HealthCheck(BaseModel):
    status: str
    database_connected: bool
    llm_available: bool
    timestamp: str



