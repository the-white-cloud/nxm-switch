import contextlib
import os
import shutil
import subprocess
from pathlib import Path

from constants import MIME_TYPE, NXM_SCHEME


# Derived from Amethyst-Mod-Manager by ChrisDKN (GPL-3.0)
# Original source:
# https://github.com/ChrisDKN/Amethyst-Mod-Manager/blob/5e5d1dee0bcafd6ddef1ea8fce68ed6df5e14644/src/Nexus/nxm_handler.py
#
# Original work licensed under GPL-3.0
#
# Modifications Copyright (C) 2026 Jules (the-white-cloud)
# Modifications:
# - Refactored class method into standalone function
# - Simplified list/path construction
# - Rewrote DE path generation using generator expression and walrus
#   operator
# - Retained original behaviour and compatibility paths
# - Removed various comments
def _mimeapps_paths() -> list[Path]:
    xdg_cfg = os.environ.get("XDG_CONFIG_HOME")
    cfg_base = Path(xdg_cfg) if xdg_cfg else Path.home() / ".config"
    paths = [cfg_base / "mimeapps.list"]
    paths.extend(
        cfg_base / f"{de_name}-mimeapps.list"
        for raw in os.environ.get("XDG_CURRENT_DESKTOP", "").split(":")
        if (de_name := raw.strip().lower())
    )
    paths.append(Path.home() / ".local" / "share" / "applications" / "mimeapps.list")
    return paths


# Derived from Amethyst-Mod-Manager by ChrisDKN (GPL-3.0)
# https://github.com/ChrisDKN/Amethyst-Mod-Manager/blob/5e5d1dee0bcafd6ddef1ea8fce68ed6df5e14644/src/Nexus/nxm_handler.py
def _patch_mimeapps(content: str, desktop_id: str) -> str:
    target_sections = ("[Default Applications]", "[Added Associations]")
    lines = content.splitlines() if content else []

    section_present: dict[str, bool] = dict.fromkeys(target_sections, False)
    key_set: dict[str, bool] = dict.fromkeys(target_sections, False)
    current_section: str | None = None
    new_lines: list[str] = []

    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current_section = stripped
            if current_section in section_present:
                section_present[current_section] = True
            new_lines.append(raw)
            continue

        is_mime_type_entry = (
            current_section is not None
            and current_section in target_sections
            and "=" in stripped
            and stripped.split("=", 1)[0].strip() == MIME_TYPE
        )

        if is_mime_type_entry:
            new_lines.append(f"{MIME_TYPE}={desktop_id}")
            key_set[current_section] = True
            continue

        new_lines.append(raw)

    for section in target_sections:
        if not section_present[section]:
            if new_lines and new_lines[-1]:
                new_lines.append("")
            new_lines.extend((section, f"{MIME_TYPE}={desktop_id}"))
        elif not key_set[section]:
            section_idx = find_section_index(new_lines, section)
            insert_at = find_next_section_index(new_lines, start=section_idx)
            new_lines.insert(insert_at, f"{MIME_TYPE}={desktop_id}")

    return "\n".join(new_lines) + ("\n" if new_lines else "")


def find_section_index(lines: list[str], section: str) -> int:
    """Return index of the line matching the given section header."""
    return next(i for i, line in enumerate(lines) if line.strip() == section)


def find_next_section_index(lines: list[str], start: int) -> int:
    """Return index of next section header after start position.

    If no section header exists after start, index of the end of list is
    returned.
    """
    return next(
        (
            i
            for i, line in enumerate(lines)
            if i > start and line.strip().startswith("[") and line.strip().endswith("]")
        ),
        len(lines),
    )


def get_current_default() -> str:
    for tool, args in [
        ("xdg-settings", ["get", "default-url-scheme-handler", NXM_SCHEME]),
        ("xdg-mime", ["query", "default", MIME_TYPE]),
    ]:
        if shutil.which(tool):
            with contextlib.suppress(Exception):
                r = subprocess.run(
                    [tool, *args], capture_output=True, text=True, timeout=3, check=True
                )
                v = r.stdout.strip()
                if v:
                    return v

    for path in _mimeapps_paths():
        if not path.exists():
            continue
        with path.open() as f:
            for line in f:
                if "=" in line and line.split("=", 1)[0].strip() == MIME_TYPE:
                    v = line.split("=", 1)[1].split(";")[0].strip()
                    if v:
                        return v
    return ""


def set_mime_default(desktop_id: str) -> bool:
    written = False
    paths = _mimeapps_paths()
    for path in paths:
        with contextlib.suppress(OSError):
            if not path.parent.exists():
                if path != paths[0]:
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
            existing = path.read_text() if path.exists() else ""
            updated = _patch_mimeapps(existing, desktop_id)
            if updated != existing:
                path.write_text(updated)
            written = True

    for tool, args in [
        ("xdg-settings", ["set", "default-url-scheme-handler", NXM_SCHEME, desktop_id]),
        ("xdg-mime", ["default", desktop_id, MIME_TYPE]),
    ]:
        if shutil.which(tool):
            with contextlib.suppress(Exception):
                subprocess.run(
                    [tool, *args], capture_output=True, timeout=5, check=False
                )

    return written
