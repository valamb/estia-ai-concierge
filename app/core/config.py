from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = Field(default="ESTIA", description="Application name")
    app_version: str = Field(default="0.1.0")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o")
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    openai_max_tokens: int = Field(default=1000)
    openai_temperature: float = Field(default=0.3)

    # ChromaDB
    chroma_db_path: str = Field(default="./chroma_db")
    chroma_collection_name: str = Field(default="estia_knowledge")

    # Knowledge Base
    knowledge_base_path: str = Field(default="./knowledge")

    # Language
    default_language: str = Field(default="en")
    supported_languages: str = Field(default="en,el")

    # RAG
    rag_chunk_size: int = Field(default=500)
    rag_chunk_overlap: int = Field(default=50)
    rag_top_k: int = Field(default=5)

    # Hotel Properties
    active_properties: str = Field(
        default="porto_elounda,elounda_mare,elounda_peninsula"
    )

    @property
    def supported_languages_list(self) -> list[str]:
        return [lang.strip() for lang in self.supported_languages.split(",")]

    @property
    def active_properties_list(self) -> list[str]:
        return [prop.strip() for prop in self.active_properties.split(",")]


settings = Settings()
