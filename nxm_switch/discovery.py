from pathlib import Path

from .constants import DESKTOP_DIRS, DESKTOP_ID, MIME_TYPE


def _parse_desktop_file(path_obj: Path) -> dict | None:
    name = path_obj.name
    app_exec = ""
    is_handler = False
    try:
        with path_obj.open("r", encoding="utf-8-sig", errors="ignore") as f:
            in_main_section = False
            for line in f:
                stripped = line.strip()
                if stripped == "[Desktop Entry]":
                    in_main_section = True
                    continue
                if stripped.startswith("[") and stripped.endswith("]"):
                    in_main_section = False
                    continue
                if in_main_section and "=" in stripped:
                    key, val = stripped.split("=", 1)
                    key = key.strip().lower()
                    if key == "name":
                        name = val.strip()
                    elif key == "exec":
                        app_exec = val.strip()
                    elif key == "mimetype" and MIME_TYPE in val.lower():
                        is_handler = True
    except OSError:
        return None

    if not is_handler:
        return None
    return {"id": path_obj.name, "path": str(path_obj), "name": name, "exec": app_exec}


def find_nxm_handlers(*, exclude_self: bool = True) -> list:
    handlers, seen = [], set()
    for d_path in DESKTOP_DIRS:
        if not d_path.exists():
            continue
        for path_obj in d_path.glob("*.desktop"):
            did = path_obj.name
            if (exclude_self and did == DESKTOP_ID) or did in seen:
                continue
            info = _parse_desktop_file(path_obj)
            if info:
                seen.add(did)
                handlers.append(info)
    return sorted(handlers, key=lambda x: x["name"].lower())


def resolve_handler(handler_id: str, config: dict) -> dict | None:
    if handler_id.startswith("custom:"):
        for c in config.get("custom_handlers", []):
            if f"custom:{c['name']}" == handler_id:
                return {
                    "id": handler_id,
                    "path": "",
                    "name": c["name"],
                    "exec": c["exec"],
                }
        return None
    for d_path in DESKTOP_DIRS:
        info = _parse_desktop_file(d_path / handler_id)
        if info:
            return info
    return None


def merge_custom_handlers(handlers: list, config: dict) -> list:
    custom = config.get("custom_handlers", [])
    if not custom:
        return handlers
    existing_ids = {h["id"] for h in handlers}
    extras = [
        {"id": f"custom:{c['name']}", "path": "", "name": c["name"], "exec": c["exec"]}
        for c in custom
        if f"custom:{c['name']}" not in existing_ids
    ]
    return sorted(handlers + extras, key=lambda x: x["name"].lower())


def get_handlers(config: dict) -> list:
    return merge_custom_handlers(find_nxm_handlers(), config)


def handler_name(desktop_id: str, handlers: list) -> str:
    for h in handlers:
        if h["id"] == desktop_id:
            return h["name"]
    return f"⚠️ Missing handler ({desktop_id})"
