from enum import StrEnum
from pathlib import Path


class ForwardMethod(StrEnum):
    RULE = "rule"
    MANUAL = "manual"
    TIMEOUT = "timeout"


MIME_TYPE = "x-scheme-handler/nxm"
NXM_SCHEME = "nxm"
DEFAULT_TIMEOUT = 15
DESKTOP_ID = "nxm-switch.desktop"
CONFIG_DIR = Path.home() / ".config" / "nxm-switch"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = CONFIG_DIR / "activity.jsonl"
DESKTOP_DIRS = [
    Path("/", "usr", "share", "applications"),
    Path("/", "usr", "local", "share", "applications"),
    Path.home() / ".local" / "share" / "applications",
]
SELF_DESKTOP = Path.home() / ".local" / "share" / "applications" / DESKTOP_ID
SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd" / "user"
GUARD_PATH_UNIT = "nxm-switch-guard.path"
GUARD_SERVICE_UNIT = "nxm-switch-guard.service"
GUARD_LOG_TAG = "nxm-switch-guard"
