from pydantic import BaseModel, Field
from typing import Literal


class ImageChatResponse(BaseModel):
    """Response from the image + text chat endpoint."""

    reply: str = Field(..., description="ESTIA's response to the image and question")
    conversation_id: str = Field(..., description="Conversation session ID")
    language_detected: str = Field(..., description="Detected or requested language")
    model_used: str = Field(..., description="Vision model used")
    tokens_used: int = Field(default=0)
    image_description: str | None = Field(
        default=None,
        description="Internal description of what was detected in the image",
    )


class ImageAnalysisResult(BaseModel):
    """Internal result from the image service."""

    description: str = Field(..., description="What the model sees in the image")
    reply: str = Field(..., description="Concierge reply in context")
    tokens_used: int = Field(default=0)
