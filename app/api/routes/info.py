from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings
from app.services import rag_service

router = APIRouter()


class InfoResponse(BaseModel):
    app_name: str
    version: str
    model: str
    embedding_model: str
    knowledge_base_path: str
    chroma_collection: str
    documents_indexed: int
    supported_languages: list[str]
    active_properties: list[str]


@router.get(
    "/info",
    response_model=InfoResponse,
    summary="System Information",
    description="Returns configuration details and RAG index statistics.",
    tags=["System"],
)
async def info() -> InfoResponse:
    return InfoResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        model=settings.openai_model,
        embedding_model=settings.openai_embedding_model,
        knowledge_base_path=settings.knowledge_base_path,
        chroma_collection=settings.chroma_collection_name,
        documents_indexed=rag_service.collection_count(),
        supported_languages=settings.supported_languages_list,
        active_properties=settings.active_properties_list,
    )
