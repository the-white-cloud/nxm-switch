"""NXM Switch

• Launched bare            → Settings UI
• Launched with nxm://...  → Resolve via rules → picker dialog

Resolution order for an incoming link:
  1. Game-specific rule   (nxm://helldivers2/... → always Arsenal)
  2. Picker dialog        (manual choice)

Config:  ~/.config/nxm-switch/config.json
Desktop: ~/.local/share/applications/nxm-switch.desktop
"""

import signal
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from .activity_log import log_forward
from .config import load_config, parse_game, save_config
from .constants import ForwardMethod
from .discovery import get_handlers, resolve_handler
from .install import reassert_default, uninstall_self
from .intercept_dialog import InterceptDialog
from .launch import launch_handler
from .settings_window import SettingsWindow
from .theme import get_stylesheet


def main() -> None:
    # Headless: used by the systemd guard service, must run before QApplication.
    if "--reassert-default" in sys.argv:
        changed = reassert_default()
        print(  # noqa: T201
            "re-asserted NXM Switch as the default nxm handler"
            if changed
            else "already the default nxm handler; no change"
        )
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("NXM Switch")
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.styleHints().colorSchemeChanged.connect(
        lambda: app.setStyleSheet(get_stylesheet())
    )
    app.setStyleSheet(get_stylesheet())

    if "--uninstall" in sys.argv:
        uninstall_self()
        QMessageBox.information(
            None,
            "Uninstalled",
            "NXM Switch has been removed as a handler and deleted from your application menu.",
        )
        sys.exit(0)

    nxm_args = [a for a in sys.argv[1:] if a.lower().startswith("nxm://")]
    if nxm_args:
        url = nxm_args[0]
        game = parse_game(url)
        config = load_config()

        if game and config.get("last_game") != game:
            config["last_game"] = game
            save_config(config)

        rule_id = config.get("rules", {}).get(game)
        if rule_id:
            target = resolve_handler(rule_id, config)
            if target:
                launch_handler(target, url)
                log_forward(url, target["name"], ForwardMethod.RULE)
                sys.exit(0)

        InterceptDialog(
            url, game=game, config=config, handlers=get_handlers(config)
        ).exec()
        sys.exit(0)

    window = SettingsWindow()
    window.show()

    if (not window.installed or not window.is_default) and window.config.get(
        "warn_if_not_default", True
    ):
        reply = QMessageBox.question(
            window,
            "Set as Default",
            "NXM Switch is not currently set as your default NXM link handler.\n\n"
            "Would you like to set it as default now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            reassert_default()
            window._load()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
