from nanexus.config import Settings
def test_current_configuration_defaults_are_stable(monkeypatch):
    for name in ("DATABASE_URL", "REDIS_URL", "MQTT_HOST", "MQTT_PORT", "MQTT_TOPIC", "AI_MODE", "SUMMARY_MODE", "CHAT_MODE", "FRIGATE_TOKEN", "LLM_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    settings = Settings(_env_file=None)
    assert settings.mqtt_topic == "frigate/events"
    assert settings.ai_mode == "openclip"
    assert settings.summary_mode == "rule"
    assert settings.chat_mode == "extractive"
    assert settings.frigate_token == ""
    assert settings.llm_api_key == ""
    assert settings.model_provider == "stub"
    assert settings.legacy_api_model_inference_enabled is False
