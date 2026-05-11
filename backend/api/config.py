from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    openai_api_key: str = ""
    jwt_secret_key: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # OAuth
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""

    # External APIs
    amadeus_api_key: str = ""
    amadeus_api_secret: str = ""
    booking_api_key: str = ""
    google_maps_api_key: str = ""
    openweather_api_key: str = ""

    # Notifications
    fcm_server_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    # Webhook
    webhook_secret: str = ""

    # App URLs
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    # Vector DB
    pinecone_api_key: str = ""
    pinecone_env: str = ""
    faiss_index_path: str = "/tmp/travel_ai_faiss"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
