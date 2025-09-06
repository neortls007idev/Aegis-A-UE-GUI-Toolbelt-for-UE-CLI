from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMenu

from aegis.core.app_preferences import (
    list_keybindings,
    list_log_colors,
    list_profiles,
    list_themes,
)


def build_menu(window: QMainWindow) -> dict[str, QAction]:
    actions: dict[str, QAction] = {}
    menu_bar = window.menuBar()

    file_menu = menu_bar.addMenu("&File")
    act_new = QAction("New Window", window)
    file_menu.addAction(act_new)
    act_new.triggered.connect(window._new_window)
    actions["file.new_window"] = act_new

    act_exit = QAction("Exit", window)
    file_menu.addAction(act_exit)
    act_exit.triggered.connect(window.close)
    actions["file.exit"] = act_exit

    view_menu = menu_bar.addMenu("&View")
    act_reset = QAction("Reset Layout", window)
    view_menu.addAction(act_reset)
    act_reset.triggered.connect(window._reset_layout)
    actions["view.reset_layout"] = act_reset

    tools_menu = menu_bar.addMenu("&Tools")
    act_echo = QAction("Echo Test Command", window)
    tools_menu.addAction(act_echo)
    act_echo.triggered.connect(window._echo_test)

    profile_menu = menu_bar.addMenu("&Profile")
    act_new_profile = QAction("New", window)
    profile_menu.addAction(act_new_profile)
    act_new_profile.triggered.connect(window._new_profile)
    actions["profile.new"] = act_new_profile

    act_open_profile = QAction("Open…", window)
    profile_menu.addAction(act_open_profile)
    act_open_profile.triggered.connect(window._open_profile)
    actions["profile.open"] = act_open_profile

    act_save_profile = QAction("Save", window)
    profile_menu.addAction(act_save_profile)
    act_save_profile.triggered.connect(window._save_profile)
    actions["profile.save"] = act_save_profile

    act_edit_profile = QAction("Edit…", window)
    profile_menu.addAction(act_edit_profile)
    act_edit_profile.triggered.connect(window._edit_profile)
    actions["profile.edit"] = act_edit_profile
    _populate_profile_menu(window, profile_menu)

    settings_menu = menu_bar.addMenu("&Settings")

    theme_menu = settings_menu.addMenu("Load Theme…")
    act_system = QAction("System", window)
    theme_menu.addAction(act_system)
    act_system.triggered.connect(lambda: window._set_theme("system"))
    act_light = QAction("Light", window)
    theme_menu.addAction(act_light)
    act_light.triggered.connect(lambda: window._set_theme("light"))
    act_dark = QAction("Dark", window)
    theme_menu.addAction(act_dark)
    act_dark.triggered.connect(lambda: window._set_theme("dark"))
    act_custom = QAction("Create Custom", window)
    theme_menu.addAction(act_custom)
    act_custom.triggered.connect(window._create_custom_theme)
    _populate_theme_menu(window, theme_menu)

    log_menu = settings_menu.addMenu("Log Colors")
    act_edit_log = QAction("Edit…", window)
    log_menu.addAction(act_edit_log)
    act_edit_log.triggered.connect(window._edit_log_colors)
    actions["settings.log_colors.edit"] = act_edit_log
    act_import_log = QAction("Import…", window)
    log_menu.addAction(act_import_log)
    act_import_log.triggered.connect(window._import_log_colors)
    actions["settings.log_colors.import"] = act_import_log
    act_export_log = QAction("Export…", window)
    log_menu.addAction(act_export_log)
    act_export_log.triggered.connect(window._export_log_colors)
    actions["settings.log_colors.export"] = act_export_log
    act_reset_log = QAction("Reset to Defaults", window)
    log_menu.addAction(act_reset_log)
    act_reset_log.triggered.connect(window._reset_log_colors)
    actions["settings.log_colors.reset"] = act_reset_log
    _populate_log_colors_menu(window, log_menu)

    kb_menu = settings_menu.addMenu("Key Bindings")
    act_edit_keys = QAction("Edit…", window)
    kb_menu.addAction(act_edit_keys)
    act_edit_keys.triggered.connect(window._edit_key_bindings)
    act_import_keys = QAction("Import…", window)
    kb_menu.addAction(act_import_keys)
    act_import_keys.triggered.connect(window._import_key_bindings)
    act_export_keys = QAction("Export…", window)
    kb_menu.addAction(act_export_keys)
    act_export_keys.triggered.connect(window._export_key_bindings)
    act_reset_keys = QAction("Reset to Defaults", window)
    kb_menu.addAction(act_reset_keys)
    act_reset_keys.triggered.connect(window._reset_key_bindings)
    _populate_keybindings_menu(window, kb_menu)

    prefs_menu = settings_menu.addMenu("Preferences")
    act_docking = QAction("Allow Docking", window)
    act_docking.setCheckable(True)
    act_docking.setChecked(window.prefs.allow_docking)
    prefs_menu.addAction(act_docking)
    act_docking.toggled.connect(window._toggle_docking)
    actions["settings.preferences.docking"] = act_docking

    act_resizing = QAction("Allow Resizing", window)
    act_resizing.setCheckable(True)
    act_resizing.setChecked(window.prefs.allow_resizing)
    prefs_menu.addAction(act_resizing)
    act_resizing.toggled.connect(window._toggle_resizing)
    actions["settings.preferences.resizing"] = act_resizing

    act_maximized = QAction("Launch Maximized", window)
    act_maximized.setCheckable(True)
    act_maximized.setChecked(window.prefs.launch_maximized)
    prefs_menu.addAction(act_maximized)
    act_maximized.toggled.connect(window._toggle_maximized)
    actions["settings.preferences.launch_maximized"] = act_maximized

    help_menu = menu_bar.addMenu("&Help")
    act_help = QAction("Help", window)
    help_menu.addAction(act_help)
    act_help.triggered.connect(window._show_help)
    actions["help.contents"] = act_help

    act_feedback = QAction("Provide Feedback", window)
    help_menu.addAction(act_feedback)
    act_feedback.triggered.connect(window._send_feedback)
    actions["help.feedback"] = act_feedback

    act_about = QAction("About", window)
    help_menu.addAction(act_about)
    act_about.triggered.connect(window._show_about)
    actions["help.about"] = act_about

    return actions


def _populate_profile_menu(window: QMainWindow, menu: QMenu) -> None:
    paths = list_profiles()
    if paths:
        menu.addSeparator()
        for path in paths:
            act = QAction(path.stem, window)
            act.triggered.connect(
                lambda _checked=False, p=path: window._open_profile_file(p)
            )
            menu.addAction(act)


def _populate_theme_menu(window: QMainWindow, menu: QMenu) -> None:
    paths = list_themes()
    if paths:
        menu.addSeparator()
        for path in paths:
            act = QAction(path.stem, window)
            act.triggered.connect(
                lambda _checked=False, p=path: window._load_theme_file(p)
            )
            menu.addAction(act)


def _populate_log_colors_menu(window: QMainWindow, menu: QMenu) -> None:
    paths = list_log_colors()
    if paths:
        menu.addSeparator()
        for path in paths:
            act = QAction(path.stem, window)
            act.triggered.connect(
                lambda _checked=False, p=path: window._load_log_colors_file(p)
            )
            menu.addAction(act)


def _populate_keybindings_menu(window: QMainWindow, menu: QMenu) -> None:
    paths = list_keybindings()
    if paths:
        menu.addSeparator()
        for path in paths:
            act = QAction(path.stem, window)
            act.triggered.connect(
                lambda _checked=False, p=path: window._load_key_bindings_file(p)
            )
            menu.addAction(act)
