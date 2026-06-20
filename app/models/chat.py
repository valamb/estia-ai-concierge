from pydantic import BaseModel, Field
from typing import Literal


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    """Request body for POST /chat."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The guest's message",
        examples=["What time does the spa open?"],
    )
    conversation_id: str | None = Field(
        default=None,
        description="Optional ID to continue an existing conversation",
    )
    language: Literal["en", "el"] | None = Field(
        default=None,
        description="Preferred response language. Auto-detected if omitted.",
    )
    property_id: str | None = Field(
        default=None,
        description="Hotel property context (e.g. 'porto_elounda')",
    )


class ChatResponse(BaseModel):
    """Response body for POST /chat."""

    reply: str = Field(..., description="The assistant's reply")
    conversation_id: str = Field(..., description="Conversation session ID")
    language_detected: str = Field(..., description="Detected or requested language")
    model_used: str = Field(..., description="OpenAI model used")
    tokens_used: int = Field(default=0, description="Total tokens consumed")


class ChatHistory(BaseModel):
    """Full conversation history for a session."""

    conversation_id: str
    messages: list[ChatMessage] = []
