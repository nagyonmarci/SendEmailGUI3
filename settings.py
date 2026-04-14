import json
import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog
import i18n

IS_MAC = sys.platform == 'darwin'


def _get_default_settings_path():
    if getattr(sys, 'frozen', False):   # PyInstaller bundle
        if sys.platform == 'win32':
            base = os.environ.get('APPDATA', os.path.expanduser('~'))
        elif sys.platform == 'darwin':
            base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
        else:
            base = os.path.expanduser('~')
        app_dir = os.path.join(base, 'SendEmailGUI3')
        os.makedirs(app_dir, exist_ok=True)
        return os.path.join(app_dir, 'settings.json')
    return 'settings.json'


DEFAULT_SETTINGS_FILE = _get_default_settings_path()
DEFAULT_HTML_BODY_FIRST = """<font style="font-family:Verdana" size="10pt" color="#184879">"""
DEFAULT_HTML_BODY_LAST = """</font>"""

current_settings_file = DEFAULT_SETTINGS_FILE


def _mac_ask_file(prompt, file_types=None):
    """Native macOS open-file dialog via AppleScript (avoids Python 3.13 tkinter crash)."""
    type_clause = ""
    if file_types:
        types_str = ", ".join(f'"{t}"' for t in file_types)
        type_clause = f" of type {{{types_str}}}"
    script = f'set f to choose file with prompt "{prompt}"{type_clause}\nreturn POSIX path of f'
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def _mac_ask_directory(prompt):
    """Native macOS folder dialog via AppleScript."""
    script = f'set d to choose folder with prompt "{prompt}"\nreturn POSIX path of d'
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return r.stdout.strip().rstrip("/") if r.returncode == 0 else None


def _mac_ask_save_file(prompt, default_name="settings.json"):
    """Native macOS save-file dialog via AppleScript."""
    script = f'set f to choose file name with prompt "{prompt}" default name "{default_name}"\nreturn POSIX path of f'
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def get_settings(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    return {
        'table_filename': table_filename.get(),
        'attachment_dir': attachment_dir.get(),
        'sheet_name': sheet_name_entry.get(),
        'subject': subject_entry.get(),
        'html_body': html_body_text.get_html() if hasattr(html_body_text, 'get_html') else html_body_text.get("1.0", "end-1c"),
        'language': i18n.get_lang(),
    }


def save_settings(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    global current_settings_file
    data = get_settings(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)
    with open(current_settings_file, 'w') as f:
        json.dump(data, f, indent=4)


def save_settings_as(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    global current_settings_file
    if IS_MAC:
        filepath = _mac_ask_save_file(i18n.t("fdlg_settings_save"))
        if filepath and not filepath.endswith(".json"):
            filepath += ".json"
    else:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Mentés másként"
        )
    if filepath:
        current_settings_file = filepath
        data = get_settings(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)


def load_settings(filepath=DEFAULT_SETTINGS_FILE):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_settings_gui():
    global current_settings_file
    if IS_MAC:
        filepath = _mac_ask_file(i18n.t("fdlg_settings_open"), ["json"])
    else:
        filepath = filedialog.askopenfilename(
            title=i18n.t("fdlg_settings_open"),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
    if filepath:
        current_settings_file = filepath
        return load_settings(filepath)


def apply_settings(settings, table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    if 'language' in settings:
        i18n.set_lang(settings['language'])
    table_filename.set(settings.get('table_filename', ''))
    attachment_dir.set(settings.get('attachment_dir', ''))
    sheet_name_entry.delete(0, tk.END)
    sheet_name_entry.insert(0, settings.get('sheet_name', ''))
    subject_entry.delete(0, tk.END)
    subject_entry.insert(0, settings.get('subject', ''))
    html = settings.get('html_body', '')
    if hasattr(html_body_text, 'set_html'):
        html_body_text.set_html(html)
    else:
        html_body_text.delete("1.0", tk.END)
        html_body_text.insert("1.0", html)


def reset_settings_to_default(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    apply_settings(
        {'table_filename': '', 'attachment_dir': '', 'sheet_name': '', 'subject': '', 'html_body': ''},
        table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text
    )
