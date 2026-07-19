from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CHESSLAB_", env_file=".env")

    database_url: str = f"sqlite+aiosqlite:///{REPO_ROOT / 'chesslab.sqlite3'}"
    stockfish_path: str = str(REPO_ROOT / "engine" / "bin" / "stockfish.exe")
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3"
    engine_depth: int = 18
    engine_multipv: int = 1
    engine_pool_size: int = 2
    engine_threads: int = 2


settings = Settings()
