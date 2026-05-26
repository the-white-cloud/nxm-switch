import json
import os
import sys
from urllib.parse import unquote, urlparse

from constants import CONFIG_DIR, CONFIG_FILE, DEFAULT_TIMEOUT


def clean_env() -> dict:
    """Return environ with LD_LIBRARY_PATH restored.

    PyInstaller prepends its bundle dir to LD_LIBRARY_PATH and saves the
    original as LD_LIBRARY_PATH_ORIG. Passing the patched env to child
    processes (konsole, mod managers, etc.) causes them to load the
    wrong Qt libs, breaking icon themes and font rendering.
    """
    env = os.environ.copy()
    if getattr(sys, "frozen", False):
        orig = env.pop("LD_LIBRARY_PATH_ORIG", None)
        if orig is not None:
            env["LD_LIBRARY_PATH"] = orig
        else:
            env.pop("LD_LIBRARY_PATH", None)
    return env


def load_config() -> dict:
    try:
        data = json.loads(CONFIG_FILE.read_text())
        data.setdefault("rules", {})
        data.setdefault("timeout", DEFAULT_TIMEOUT)
        data.setdefault("preferred", "")
        data.setdefault("stop_on_interact", True)
        data.setdefault("countdown_enabled", False)
        data.setdefault("custom_handlers", [])
        data.setdefault("warn_if_not_default", True)
    except OSError, json.JSONDecodeError:
        pass
    else:
        return data
    return {
        "rules": {},
        "timeout": DEFAULT_TIMEOUT,
        "preferred": "",
        "stop_on_interact": True,
        "countdown_enabled": False,
        "custom_handlers": [],
        "warn_if_not_default": True,
    }


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def parse_game(url: str) -> str:
    """Extract game slug from nxm://gamename/mods/... → 'gamename'"""
    try:
        return urlparse(unquote(url)).netloc.lower().strip()
    except ValueError:
        return ""
