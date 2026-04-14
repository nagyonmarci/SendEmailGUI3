_lang = "hu"

STRINGS = {
    "hu": {
        "window_title":       "Tömeges emailküldés",
        "menu_file":          "Fájl",
        "menu_save":          "Mentés",
        "menu_save_as":       "Mentés másként…",
        "menu_open":          "Megnyitás…",
        "menu_reset":         "Alaphelyzetbe állítás",
        "menu_language":      "Nyelv",
        "menu_quit":          "Kilépés",
        "menu_edit":          "Szerkesztés",
        "menu_bold":          "Félkövér",
        "menu_italic":        "Dőlt",
        "menu_underline":     "Aláhúzás",
        "menu_insert_table":  "Táblázat beszúrása…",
        "menu_email":         "Email",
        "menu_generate":      "Generálás indítása",
        "menu_stop":          "Generálás leállítása",
        "menu_close_windows": "Ablakok bezárása",
        "section_data":       "  Adatok  ",
        "section_body":       "  Email törzs  ",
        "label_excel":        "Excel fájl:",
        "label_attachments":  "Mellékletek mappája:",
        "label_sheet":        "Munkalap neve:",
        "label_subject":      "Email tárgy:",
        "btn_browse":         "Tallózás…",
        "btn_generate":       "▶  Email-ek generálása",
        "btn_stop":           "⏹  Leállítás",
        "btn_close_windows":  "✕  Ablakok bezárása",
        "toolbar_table":      "⊞  Táblázat",
        "dlg_table_title":    "Táblázat beszúrása",
        "dlg_rows":           "Sorok száma:",
        "dlg_cols":           "Oszlopok száma:",
        "dlg_insert":         "Beszúrás",
        "fdlg_excel":         "Válassza ki az Excel fájlt",
        "fdlg_attachments":   "Válassza ki a mellékletek mappáját",
        "fdlg_settings_open": "Válassza ki a beállítások fájlt",
        "fdlg_settings_save": "Mentés másként",
    },
    "en": {
        "window_title":       "Bulk Email Sender",
        "menu_file":          "File",
        "menu_save":          "Save",
        "menu_save_as":       "Save As…",
        "menu_open":          "Open…",
        "menu_reset":         "Reset to Default",
        "menu_language":      "Language",
        "menu_quit":          "Quit",
        "menu_edit":          "Edit",
        "menu_bold":          "Bold",
        "menu_italic":        "Italic",
        "menu_underline":     "Underline",
        "menu_insert_table":  "Insert Table…",
        "menu_email":         "Email",
        "menu_generate":      "Start Generation",
        "menu_stop":          "Stop Generation",
        "menu_close_windows": "Close Windows",
        "section_data":       "  Data  ",
        "section_body":       "  Email Body  ",
        "label_excel":        "Excel file:",
        "label_attachments":  "Attachments folder:",
        "label_sheet":        "Sheet name:",
        "label_subject":      "Email subject:",
        "btn_browse":         "Browse…",
        "btn_generate":       "▶  Generate emails",
        "btn_stop":           "⏹  Stop",
        "btn_close_windows":  "✕  Close windows",
        "toolbar_table":      "⊞  Table",
        "dlg_table_title":    "Insert Table",
        "dlg_rows":           "Number of rows:",
        "dlg_cols":           "Number of columns:",
        "dlg_insert":         "Insert",
        "fdlg_excel":         "Select Excel file",
        "fdlg_attachments":   "Select attachments folder",
        "fdlg_settings_open": "Select settings file",
        "fdlg_settings_save": "Save As",
    },
}


def t(key):
    return STRINGS.get(_lang, STRINGS["hu"]).get(key, key)


def set_lang(lang):
    global _lang
    if lang in STRINGS:
        _lang = lang


def get_lang():
    return _lang
