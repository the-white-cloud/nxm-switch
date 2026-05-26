import contextlib
import json
import shutil
import subprocess
from datetime import UTC, datetime

from constants import CONFIG_DIR, GUARD_LOG_TAG, LOG_FILE


def log_forward(url: str, handler: str, method: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "time": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "url": url,
        "handler": handler,
        "method": method,
    }
    with contextlib.suppress(OSError), LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_activity_log(limit: int = 500) -> list:
    try:
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    entries = []
    for line in lines[-limit:]:
        with contextlib.suppress(ValueError):
            entries.append(json.loads(line))
    entries.reverse()
    return entries


def clear_activity_log() -> None:
    LOG_FILE.unlink(missing_ok=True)


def read_service_log(lines: int = 200) -> str:
    if not shutil.which("journalctl"):
        return "journalctl is not available on this system."
    try:
        r = subprocess.run(
            [
                "journalctl",
                "--user",
                "-t",
                GUARD_LOG_TAG,
                "-n",
                str(lines),
                "--no-pager",
                "-o",
                "short-iso",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
        return f"Could not read the service log: {e}"
    return r.stdout.strip() or "No service log entries yet."


def journal_note(message: str) -> None:
    if not shutil.which("systemd-cat"):
        return
    with contextlib.suppress(subprocess.SubprocessError, OSError):
        subprocess.run(
            ["systemd-cat", "-t", GUARD_LOG_TAG],
            input=message + "\n",
            text=True,
            timeout=5,
            check=True,
        )
