"""Local AI provider settings for Resume Fixer.

Settings live outside the repository. API keys are optional and can either be
stored in a user-only credentials file or kept in memory for the current app
session.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4.1-mini"
CONFIG_DIR = Path.home() / ".resume-fixer"
CONFIG_PATH = CONFIG_DIR / "config.json"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"

_SESSION_KEY = ""


@dataclass
class AISettings:
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    api_key: str = ""
    ca_bundle: str = ""
    target_language: str = "English"
    remember_key: bool = False

    @property
    def configured(self) -> bool:
        return bool(self.base_url.strip() and self.model.strip())

    @property
    def key_hint(self) -> str:
        if not self.api_key:
            return "No API key configured"
        tail = self.api_key[-4:] if len(self.api_key) >= 8 else "saved"
        return f"API key ending in {tail}"


def _read_json(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def load_settings() -> AISettings:
    config = _read_json(CONFIG_PATH)
    credentials = _read_json(CREDENTIALS_PATH)
    base_url = str(
        os.environ.get("RESUME_AI_BASE_URL")
        or os.environ.get("OPENAI_BASE_URL")
        or config.get("base_url")
        or DEFAULT_BASE_URL
    ).strip()
    model = str(os.environ.get("RESUME_AI_MODEL") or config.get("model") or DEFAULT_MODEL).strip()
    api_key = str(
        os.environ.get("RESUME_AI_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or credentials.get("api_key")
        or _SESSION_KEY
    ).strip()
    ca_bundle = str(
        os.environ.get("RESUME_AI_CA_BUNDLE")
        or config.get("ca_bundle")
        or ""
    ).strip()
    target_language = str(
        config.get("target_language") or "English"
    ).strip() or "English"
    return AISettings(
        base_url=base_url,
        model=model,
        api_key=api_key,
        ca_bundle=ca_bundle,
        target_language=target_language,
        remember_key=bool(credentials.get("api_key")),
    )


def set_session_key(api_key: str) -> None:
    global _SESSION_KEY
    _SESSION_KEY = api_key.strip()


def save_settings(settings: AISettings, remember_key: bool) -> None:
    CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    config = {
        "base_url": settings.base_url.strip(),
        "model": settings.model.strip(),
        "ca_bundle": settings.ca_bundle.strip(),
        "target_language": settings.target_language.strip() or "English",
    }
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    try:
        CONFIG_PATH.chmod(0o600)
    except OSError:
        pass

    set_session_key(settings.api_key)
    if remember_key and settings.api_key:
        credentials = {"api_key": settings.api_key}
        CREDENTIALS_PATH.write_text(json.dumps(credentials, indent=2) + "\n", encoding="utf-8")
        try:
            CREDENTIALS_PATH.chmod(0o600)
        except OSError:
            pass
    elif CREDENTIALS_PATH.exists():
        try:
            CREDENTIALS_PATH.unlink()
        except OSError:
            pass


def clear_saved_key() -> None:
    set_session_key("")
    if CREDENTIALS_PATH.exists():
        try:
            CREDENTIALS_PATH.unlink()
        except OSError:
            pass


def public_settings_dict(settings: AISettings) -> dict[str, object]:
    data = asdict(settings)
    data.pop("api_key", None)
    return data
