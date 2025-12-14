from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from enum import Enum

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        field_schema.update(type="string")
        return field_schema

class Rating(str, Enum):
    GOOD = "good"
    AVERAGE = "average"
    NO_IMPROVEMENT = "no_improvement"

# Communication Skills Model
class VerbalSkills(BaseModel):
    speak_words_sentences: Optional[Rating] = None
    clarity_pronunciation: Optional[Rating] = None
    expressing_needs: Optional[Rating] = None
    turn_taking: Optional[Rating] = None
    initiating_conversation: Optional[Rating] = None
    vocabulary: Optional[Rating] = None
    functional_speech: Optional[Rating] = None

class NonVerbalSkills(BaseModel):
    eye_contact: Optional[Rating] = None
    gestures: Optional[Rating] = None
    facial_expressions: Optional[Rating] = None
    body_language: Optional[Rating] = None
    following_directions: Optional[Rating] = None

class CommunicationSkills(BaseModel):
    verbal: Optional[VerbalSkills] = None
    non_verbal: Optional[NonVerbalSkills] = None

# Emotional Development Model
class EmotionalDevelopment(BaseModel):
    identify_own_emotions: Optional[Rating] = None
    identify_others_emotions: Optional[Rating] = None
    emotional_regulation: Optional[Rating] = None
    sensory_overload_response: Optional[Rating] = None
    meltdowns_vs_tantrums: Optional[Rating] = None
    coping_strategies: Optional[Rating] = None

# Social Skills Model
class SocialSkills(BaseModel):
    playing_with_peers: Optional[Rating] = None
    sharing_turn_taking: Optional[Rating] = None
    understanding_social_rules: Optional[Rating] = None
    joint_attention: Optional[Rating] = None
    imitation_skills: Optional[Rating] = None
    response_to_name: Optional[Rating] = None
    group_participation: Optional[Rating] = None

# Behavior Model
class Behavior(BaseModel):
    aggression: Optional[Rating] = None
    self_injury: Optional[Rating] = None
    eloping: Optional[Rating] = None
    throwing_objects: Optional[Rating] = None
    behavior_triggers: Optional[Rating] = None
    following_routines: Optional[Rating] = None
    flexibility_to_change: Optional[Rating] = None
    response_to_reinforcement: Optional[Rating] = None

# Cognitive Skills Model
class CognitiveSkills(BaseModel):
    attention_span: Optional[Rating] = None
    focus: Optional[Rating] = None
    memory: Optional[Rating] = None
    problem_solving: Optional[Rating] = None
    matching_sorting_sequencing: Optional[Rating] = None
    learning_new_concepts: Optional[Rating] = None
    basic_academics: Optional[Rating] = None

# Sensory Processing Model
class SensoryProcessing(BaseModel):
    hyper_hypo_sensitivity: Optional[Rating] = None
    stimming: Optional[Rating] = None
    sensory_seeking: Optional[Rating] = None
    light_sound_touch_tolerance: Optional[Rating] = None
    food_selectiveness: Optional[Rating] = None

# Daily Living Skills Model
class DailyLivingSkills(BaseModel):
    eating_independently: Optional[Rating] = None
    dressing: Optional[Rating] = None
    toilet_training: Optional[Rating] = None
    brushing_teeth: Optional[Rating] = None
    hand_washing: Optional[Rating] = None
    sleeping_patterns: Optional[Rating] = None
    using_yes_no: Optional[Rating] = None
    safety_awareness: Optional[Rating] = None

# Therapy Participation Model
class TherapyParticipation(BaseModel):
    sitting_tolerance: Optional[Rating] = None
    responsiveness: Optional[Rating] = None
    engagement_level: Optional[Rating] = None
    prompt_dependency: Optional[Rating] = None
    transitioning_between_tasks: Optional[Rating] = None

# Therapy Log Model
class TherapyLogCreate(BaseModel):
    child_id: str
    session_date: datetime
    duration_minutes: int
    activities_performed: str
    notes: str
    communication_skills: Optional[CommunicationSkills] = None
    emotional_development: Optional[EmotionalDevelopment] = None
    social_skills: Optional[SocialSkills] = None
    behavior: Optional[Behavior] = None
    cognitive_skills: Optional[CognitiveSkills] = None
    sensory_processing: Optional[SensoryProcessing] = None
    daily_living_skills: Optional[DailyLivingSkills] = None
    therapy_participation: Optional[TherapyParticipation] = None

class TherapyLogInDB(TherapyLogCreate):
    id: Optional[str] = Field(default=None, alias="_id")
    doctor_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Child Models
class ChildCreate(BaseModel):
    name: str
    age: int
    gender: str
    diagnosis: str
    parent_email: Optional[EmailStr] = None
    parent_phone: Optional[str] = None
    parent_name: Optional[str] = None

class ChildInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    child_code: str
    name: str
    age: int
    gender: str
    diagnosis: str
    assigned_doctor_id: str
    parent_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChildResponse(BaseModel):
    id: str
    child_code: str
    name: str
    age: int
    gender: str
    diagnosis: str
    created_at: datetime

# Parent Models
class ParentCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    child_code: Optional[str] = None

class ParentInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    email: str
    phone: Optional[str] = None
    password_hash: str
    children: List[str] = []
    created_by_system: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ParentResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    children: List[str] = []
    created_at: datetime

# Doctor Models
class DoctorCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    specialization: str

class DoctorInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    email: str
    password_hash: str
    specialization: str
    assigned_children: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DoctorResponse(BaseModel):
    id: str
    name: str
    email: str
    specialization: str
    assigned_children: List[str] = []
    created_at: datetime

# Child Code Model
class ChildCodeInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    child_id: str
    code: str
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Auth Models
class Token(BaseModel):
    access_token: str
    token_type: str
    user_type: str
    user_id: str
    user_name: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    user_type: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    user_type: str  # "doctor" or "parent"

# Report Models
class WeeklyReport(BaseModel):
    child_id: str
    child_name: str
    week_start: datetime
    week_end: datetime
    total_sessions: int
    total_duration: int
    domain_averages: dict
    session_summaries: List[dict]
    improvement_trends: dict

class MonthlyReport(BaseModel):
    child_id: str
    child_name: str
    month: str
    year: int
    total_sessions: int
    total_duration: int
    domain_averages: dict
    weekly_trends: List[dict]
    recommendations: List[str]
    behavior_alerts: List[str]
