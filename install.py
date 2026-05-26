import contextlib
import shutil
import subprocess
import sys
from pathlib import Path

from constants import (
    DESKTOP_DIRS,
    DESKTOP_ID,
    GUARD_LOG_TAG,
    GUARD_PATH_UNIT,
    GUARD_SERVICE_UNIT,
    MIME_TYPE,
    SELF_DESKTOP,
    SYSTEMD_USER_DIR,
)
from mime import _mimeapps_paths, get_current_default, set_mime_default


def is_package_installed(package: str) -> bool:
    if not shutil.which("pacman"):
        return False
    try:
        return (
            subprocess.run(
                ["pacman", "-Q", package], capture_output=True, timeout=3, check=False
            ).returncode
            == 0
        )
    except (subprocess.TimeoutExpired, OSError):
        return False


def _self_invocation() -> str:
    if getattr(sys, "frozen", False) or globals().get("__compiled__", False):
        return str(Path(sys.executable).resolve())
    return f"{sys.executable} {Path(sys.argv[0]).resolve()}"


def install_self() -> bool:
    desktop_dir = SELF_DESKTOP.parent
    desktop_dir.mkdir(parents=True, exist_ok=True)
    invocation = _self_invocation()
    SELF_DESKTOP.write_text(
        "[Desktop Entry]\n"
        "Name=NXM Switch\n"
        "Comment=Intercept NXM links and forward to your chosen mod manager\n"
        f"Exec={invocation} %u\n"
        "Terminal=false\n"
        "Type=Application\n"
        f"MimeType={MIME_TYPE};\n"
        "Categories=Utility;\n"
        "Keywords=nxm;nexus;mods;switcher;\n"
        "Actions=Uninstall;\n\n"
        "[Desktop Action Uninstall]\n"
        "Name=Uninstall NXM Switch\n"
        f"Exec={invocation} --uninstall\n"
    )
    if shutil.which("update-desktop-database"):
        subprocess.run(
            ["update-desktop-database", str(desktop_dir)],
            capture_output=True,
            check=False,
        )
    return set_mime_default(DESKTOP_ID)


def uninstall_self() -> None:
    uninstall_guard()
    SELF_DESKTOP.unlink(missing_ok=True)
    if shutil.which("update-desktop-database"):
        subprocess.run(
            ["update-desktop-database", str(SELF_DESKTOP.parent)],
            capture_output=True,
            check=False,
        )


def self_is_installed() -> bool:
    return SELF_DESKTOP.exists() or any((d / DESKTOP_ID).exists() for d in DESKTOP_DIRS)


def self_is_default() -> bool:
    return get_current_default() == DESKTOP_ID


def reassert_default() -> bool:
    """Make default if not default"""
    if self_is_default():
        return False
    if self_is_installed():
        set_mime_default(DESKTOP_ID)
    else:
        install_self()
    return True


def guard_available() -> bool:
    return shutil.which("systemctl") is not None


def guard_is_active() -> bool:
    if not guard_available():
        return False
    try:
        r = subprocess.run(
            ["systemctl", "--user", "is-enabled", GUARD_PATH_UNIT],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        return r.stdout.strip() == "enabled"
    except (subprocess.TimeoutExpired, OSError):
        return False


def install_guard() -> bool:
    if not guard_available():
        return False
    if not self_is_installed():
        install_self()

    SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)
    watched = list(dict.fromkeys(_mimeapps_paths()))
    watch_lines = "\n".join(f"PathModified={p}" for p in watched)

    (SYSTEMD_USER_DIR / GUARD_PATH_UNIT).write_text(
        "[Unit]\n"
        "Description=Keep NXM Switch as the default nxm:// handler\n\n"
        "[Path]\n"
        f"{watch_lines}\n"
        f"Unit={GUARD_SERVICE_UNIT}\n\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )
    (SYSTEMD_USER_DIR / GUARD_SERVICE_UNIT).write_text(
        "[Unit]\n"
        "Description=Re-assert NXM Switch as the default nxm:// handler\n\n"
        "[Service]\n"
        "Type=oneshot\n"
        f"SyslogIdentifier={GUARD_LOG_TAG}\n"
        f"ExecStart={_self_invocation()} --reassert-default\n"
    )

    try:
        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            capture_output=True,
            timeout=5,
            check=True,
        )
        subprocess.run(
            ["systemctl", "--user", "enable", "--now", GUARD_PATH_UNIT],
            capture_output=True,
            timeout=5,
            check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False

    reassert_default()
    return True


def uninstall_guard() -> bool:
    if guard_available():
        with contextlib.suppress(subprocess.SubprocessError, OSError):
            subprocess.run(
                ["systemctl", "--user", "disable", "--now", GUARD_PATH_UNIT],
                capture_output=True,
                timeout=5,
                check=True,
            )

    removed = False
    for name in (GUARD_PATH_UNIT, GUARD_SERVICE_UNIT):
        unit = SYSTEMD_USER_DIR / name
        if unit.exists():
            unit.unlink(missing_ok=True)
            removed = True

    if guard_available():
        with contextlib.suppress(subprocess.SubprocessError, OSError):
            subprocess.run(
                ["systemctl", "--user", "daemon-reload"],
                capture_output=True,
                timeout=5,
                check=True,
            )
    return removed
