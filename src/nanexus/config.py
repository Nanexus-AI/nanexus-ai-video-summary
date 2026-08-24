from functools import lru_cache

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
    # stub | openclip
    ai_mode: str = "openclip"
    ai_device: str = "auto"
    openclip_model: str = "ViT-B-32"
    openclip_pretrained: str = "openai"
    snapshots_dir: str = "data/snapshots"
    public_base_url: str = "http://127.0.0.1:8000"
    event_intelligence_url: str = "http://event-intelligence:8000"
    event_intelligence_token: str = ""
    event_intelligence_timeout_seconds: float = 10.0
    event_intelligence_poll_seconds: float = 1.0
    # Dedicated enrichment worker only. Cloud providers remain unsupported/default-off.
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

    # OpenAI-compatible LLM (optional)
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 60.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
