from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

from app.chat.enums import MessageRole
from app.chat.llm import MODELS

class CreateConversationRequest(BaseModel):
    title: str
    model: str = "llama-3.1-70b-versatile"

    @field_validator("model")
    @classmethod
    def model_must_be_supported(cls, v:str) -> str:
        if v not in MODELS:
            raise ValueError(f"Model {v} is not supported")
        return v


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    created_at: datetime
    user_id: int
    model:str


class UpdateConversationRequest(BaseModel):
    title: str | None = None
    model:str | None = None
    @field_validator("model")
    @classmethod
    def model_must_be_supported(cls, v: str | None) -> str | None:
        if v is not None and v not in MODELS:
            raise ValueError(f"Model {v} is not supported")
        return v


class SendMessageRequest(BaseModel):
    message: str
    temperature: float = 0.2

class MessageResponse(BaseModel): 
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: MessageRole
    content: str
    created_at: datetime
    model:str
    message_type:str

class BurnedTokensResponse(BaseModel):
    tokens: int

class ToolCallResponse(BaseModel):
    content: str