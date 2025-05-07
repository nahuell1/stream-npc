from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings configuration.
    
    Attributes:
        twitch_channel: The Twitch channel name to connect to.
    """
    twitch_channel: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()