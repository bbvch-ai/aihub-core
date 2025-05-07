from typing import Optional

from pydantic import BaseModel, Field


class OpenWebUIConfig(BaseModel):
    """Configuration class for Nats infrastructure"""

    webui_name: str = Field(description="Name of web UI")
    admin_email: str = Field(description="Admin email for web UI")
    default_locale: str = Field(description="Default locale for web UI")

    aihub_api_key: Optional[str] = Field(description="AIHub API key")
    custom_openai_api_key: Optional[str] = Field(description="OpenAI API key")
    custom_rag_openai_api_key: Optional[str] = Field(description="OpenAI API key for RAG")
    custom_audio_stt_openai_api_key: Optional[str] = Field(description="OpenAI API key for audio STT")
    custom_audio_tts_openai_api_key: Optional[str] = Field(description="OpenAI API key for audio TTS")
    custom_images_openai_api_key: Optional[str] = Field(description="OpenAI API key for images")
    jina_api_key: str = Field(description="Jina API key")

    oidc_client_id: str = Field(description="OIDC client ID")
    oidc_client_secret: str = Field(description="OIDC client secret")
    oidc_provider_url: str = Field(description="OIDC provider URL")
    oidc_provider_name: str = Field(description="OIDC provider name")

    additional_env_vars: dict = Field(default=dict(), description="Additional environment variables")

    @property
    def rag_openai_api_key(self) -> str:
        return self.custom_rag_openai_api_key or self.aihub_api_key

    @property
    def openai_api_key(self) -> str:
        return self.custom_rag_openai_api_key or self.aihub_api_key

    @property
    def audio_stt_openai_api_key(self) -> str:
        return self.custom_audio_stt_openai_api_key or self.aihub_api_key

    @property
    def audio_tts_openai_api_key(self) -> str:
        return self.custom_audio_tts_openai_api_key or self.aihub_api_key

    @property
    def images_openai_api_key(self) -> str:
        return self.custom_images_openai_api_key or self.aihub_api_key
