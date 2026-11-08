from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    source_dir: Path = ROOT / "I Married a Broken Soldier. He was a Duke"
    db_path: Path = ROOT / "data/kuku.sqlite3"
    provider: str = "rules"
    model_url: str = "http://127.0.0.1:11434"
    model_name: str = ""
    model_revision: str = ""
    model_timeout: float = 60
    model_context: int = 16384
    api_key: str = ""

    @classmethod
    def from_env(cls):
        return cls(source_dir=Path(os.getenv("KUKU_SOURCE_DIR", str(cls.source_dir))),
            db_path=Path(os.getenv("KUKU_DB_PATH", str(cls.db_path))),
            provider=os.getenv("KUKU_PROVIDER", "rules"),
            model_url=os.getenv("KUKU_MODEL_URL", cls.model_url).rstrip("/"),
            model_name=os.getenv("KUKU_MODEL_NAME", ""), model_revision=os.getenv("KUKU_MODEL_REVISION", ""),
            model_timeout=float(os.getenv("KUKU_MODEL_TIMEOUT", "60")),
            model_context=int(os.getenv("KUKU_MODEL_CONTEXT", "16384")), api_key=os.getenv("KUKU_API_KEY", ""))

    def public(self):
        return {"default_provider": self.provider, "model_name": self.model_name,
                "model_revision": self.model_revision, "model_configured": bool(self.model_name),
                "providers": ["rules"] + (["ollama"] if self.model_name else []),
                "scope": "continuous_candidates", "ranking": "not_implemented"}
