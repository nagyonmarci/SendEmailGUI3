import json
import tkinter as tk
from tkinter import filedialog

DEFAULT_SETTINGS_FILE = 'settings.json'
DEFAULT_HTML_BODY_FIRST = """<font style="font-family:Verdana" size="10pt" color="#184879">"""
DEFAULT_HTML_BODY_LAST = """</font>"""

current_settings_file = DEFAULT_SETTINGS_FILE

def get_settings(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    return {
        'table_filename': table_filename.get(),
        'attachment_dir': attachment_dir.get(),
        'sheet_name': sheet_name_entry.get(),
        'subject': subject_entry.get(),
        'html_body': html_body_text.get("1.0", "end-1c"),
    }

def save_settings(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    global current_settings_file
    settings = get_settings(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)
    with open(current_settings_file, 'w') as f:
        json.dump(settings, f, indent=4)

def save_settings_as(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    global current_settings_file
    filepath = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        title="Mentés másként"
    )
    if filepath:
        current_settings_file = filepath
        settings = get_settings(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)
        with open(filepath, 'w') as f:
            json.dump(settings, f, indent=4)

def load_settings(filepath=DEFAULT_SETTINGS_FILE):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def load_settings_gui():
    global current_settings_file
    filepath = filedialog.askopenfilename(
        title="Válassza ki a beállítások fájlt",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if filepath:
        current_settings_file = filepath
        settings = load_settings(filepath)
        return settings

def apply_settings(settings, table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    table_filename.set(settings.get('table_filename', ''))
    attachment_dir.set(settings.get('attachment_dir', ''))
    sheet_name_entry.delete(0, tk.END)
    sheet_name_entry.insert(0, settings.get('sheet_name', ''))
    subject_entry.delete(0, tk.END)
    subject_entry.insert(0, settings.get('subject', ''))
    html_body_text.delete("1.0", tk.END)
    html_body_text.insert("1.0", settings.get('html_body', ''))

def reset_settings_to_default(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    default_settings = {
        'table_filename': '',
        'attachment_dir': '',
        'sheet_name': '',
        'subject': '',
        'html_body': '',
    }
    apply_settings(default_settings, table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)