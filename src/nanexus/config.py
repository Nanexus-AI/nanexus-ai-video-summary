from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://nanexus:nanexus@localhost:5432/nanexus"
    redis_url: str = "redis://localhost:6379/0"
    mqtt_host: str = "localhost"
    mqtt_port: int = 1884
    mqtt_topic: str = "frigate/events"
    frigate_base_url: str = "http://localhost:5000"
    frigate_token: str = ""
    embedding_dim: int = 512
    embedding_queue_key: str = "nanexus:search:embedding-jobs"
    embedding_dlq_key: str = "nanexus:search:embedding-dlq"
    embedding_max_attempts: int = 3
    model_service_url: str = "http://model-service:8010"
    search_model: str = ""
    search_model_version: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    ai_queue_key: str = "nanexus:ai:events"
    processed_set_key: str = "nanexus:ai:processed"
    # Legacy AI-worker path only (stub | openclip). Independent of MODEL_PROVIDER.
    ai_mode: str = "openclip"
    ai_device: str = "auto"
    openclip_model: str = "ViT-B-32-quickgelu"
    openclip_pretrained: str = "openai"
    snapshots_dir: str = "data/snapshots"
    public_base_url: str = "http://127.0.0.1:8000"
    event_intelligence_url: str = "http://event-intelligence:8000"
    # Browser/mobile-safe public origin used only to build stable Subject links.
    event_intelligence_public_url: str = "http://127.0.0.1:8001"
    event_intelligence_token: str = ""
    event_intelligence_timeout_seconds: float = 10.0
    event_intelligence_poll_seconds: float = 1.0
    # Current v1 enrichment/model-service path (stub | openclip). Cloud unsupported.
    model_provider: str = "stub"
    model_timeout_seconds: float = 60.0
    model_max_image_bytes: int = 10 * 1024 * 1024
    # Rollback-only switch for the legacy Search path. New API processes never infer.
    legacy_api_model_inference_enabled: bool = False

    # Summary worker
    summary_queue_key: str = "nanexus:summary:jobs"
    summary_done_set_key: str = "nanexus:summary:done"
    # rule | llm
    summary_mode: str = "rule"
    summary_hour: int = 23
    summary_minute: int = 50
    # UTC | local
    summary_timezone: str = "UTC"
    summary_site_id: str = "default"
    summary_rule_version: str = "rule-v1"
    summary_prompt_version: str = "daily-security-v1"
    summary_llm_max_input_chars: int = 16_000
    summary_llm_max_tokens: int = 700
    summary_llm_max_cost_micros: int = 25_000
    summary_llm_input_cost_per_million_micros: int = 1_000_000
    summary_llm_output_cost_per_million_micros: int = 10_000_000

    # Chat
    # extractive | llm
    chat_mode: str = "extractive"
    chat_lookback_days: int = 3
    chat_queue_key: str = "nanexus:chat:jobs"
    chat_context_subject_limit: int = 8
    chat_max_context_chars: int = 12_000
    chat_max_output_tokens: int = 500
    chat_max_output_chars: int = 4_000
    chat_llm_input_cost_per_million_micros: int = 1_000_000
    chat_llm_output_cost_per_million_micros: int = 10_000_000

    # Client compatibility. Legacy APIs remain available as an explicit rollback.
    client_api_version: str = "v1"
    legacy_client_api_enabled: bool = True

    # OpenAI-compatible LLM (optional)
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 60.0

    # Security boundary. Development is explicit and must never be used by the
    # production Compose profile. Static is a deterministic local reference
    # identity provider; gateways can mint/rotate opaque tokens out of band.
    deployment_mode: str = "development"  # development | production
    auth_mode: str = "development"  # development | static
    auth_tokens_file: str = ""
    service_token_file: str = ""
    cors_allowed_origins: str = "http://127.0.0.1:8080,http://localhost:8080"
    expected_event_api_version: str = "1.0"
    expected_canonical_schema_version: str = "1.0"
    expected_capability_version: str = "1.0"
    expected_processor_contract_version: str = "1.0"
    capability_check_enabled: bool = False
    worker_heartbeat_ttl_seconds: int = 30

    def validate_runtime(self) -> None:
        if self.deployment_mode not in {"development", "production"}:
            raise RuntimeError("DEPLOYMENT_MODE must be development or production")
        if self.auth_mode not in {"development", "static"}:
            raise RuntimeError("AUTH_MODE must be development or static")
        if self.deployment_mode == "production":
            if self.auth_mode == "development":
                raise RuntimeError("production refuses development authentication")
            if not self.auth_tokens_file or not Path(self.auth_tokens_file).is_file():
                raise RuntimeError("production requires AUTH_TOKENS_FILE")
            if not self.service_token_file or not Path(self.service_token_file).is_file():
                raise RuntimeError("production requires SERVICE_TOKEN_FILE")
            for name, value in {
                "PUBLIC_BASE_URL": self.public_base_url,
                "EVENT_INTELLIGENCE_PUBLIC_URL": self.event_intelligence_public_url,
            }.items():
                if urlparse(value).scheme != "https":
                    raise RuntimeError(f"production requires HTTPS for {name}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
