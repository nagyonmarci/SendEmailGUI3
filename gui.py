import sys
import subprocess
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, VERTICAL
from tkinter import ttk
import threading
import settings
import email_generation

IS_MAC = sys.platform == 'darwin'


# ── WYSIWYG Rich Text Editor ─────────────────────────────────────────────────

class RichTextEditor(tk.Text):
    """tk.Text subclass with WYSIWYG HTML editing.

    Bold / italic / underline are displayed visually using widget tags.
    Raw HTML (tables, unknown tags) is shown in grey monospace.
    get_html() / set_html() handle serialisation to/from HTML strings.
    """

    _TAGS = {
        "bold":      ("<b>",  "</b>"),
        "italic":    ("<i>",  "</i>"),
        "underline": ("<u>",  "</u>"),
    }

    def __init__(self, master, **kwargs):
        font = kwargs.get("font", ("Verdana", 10))
        family = font[0] if isinstance(font, tuple) and len(font) >= 1 else "Verdana"
        size   = font[1] if isinstance(font, tuple) and len(font) >= 2 else 10
        super().__init__(master, **kwargs)
        self.tag_configure("bold",      font=(family, size, "bold"))
        self.tag_configure("italic",    font=(family, size, "italic"))
        self.tag_configure("underline", underline=True)
        self.tag_configure("raw_html",  foreground="#aaaaaa", font=("Courier", 9))

    def toggle_format(self, tag):
        try:
            sel_first = self.index(tk.SEL_FIRST)
            sel_last  = self.index(tk.SEL_LAST)
        except tk.TclError:
            return
        if tag in self.tag_names(sel_first):
            self.tag_remove(tag, sel_first, sel_last)
        else:
            self.tag_add(tag, sel_first, sel_last)

    def insert_raw(self, html_text):
        start = self.index(tk.INSERT)
        self.insert(tk.INSERT, html_text)
        self.tag_add("raw_html", start, self.index(tk.INSERT))

    def get_html(self):
        result = []
        raw_on = False
        for key, value, _ in self.dump("1.0", "end-1c", text=True, tag=True):
            if key == "tagon":
                if value == "raw_html":
                    raw_on = True
                elif value in self._TAGS and not raw_on:
                    result.append(self._TAGS[value][0])
            elif key == "tagoff":
                if value == "raw_html":
                    raw_on = False
                elif value in self._TAGS and not raw_on:
                    result.append(self._TAGS[value][1])
            elif key == "text":
                result.append(value if raw_on else value.replace("\n", "<br>"))
        return "".join(result)

    def set_html(self, html):
        self.delete("1.0", tk.END)
        if not html:
            return
        _TAG_MAP = {
            "b": "bold", "strong": "bold",
            "i": "italic", "em": "italic",
            "u": "underline",
        }
        active = []
        i = 0
        while i < len(html):
            if html[i] != "<":
                j = html.find("<", i)
                chunk = html[i:] if j == -1 else html[i:j]
                if chunk:
                    s = self.index(tk.END + "-1c")
                    self.insert(tk.END, chunk)
                    e = self.index(tk.END + "-1c")
                    for t in active:
                        self.tag_add(t, s, e)
                i = len(html) if j == -1 else j
            else:
                j = html.find(">", i)
                if j == -1:
                    self.insert_raw(html[i:])
                    break
                full  = html[i:j + 1]
                inner = html[i + 1:j].strip()
                name  = (inner.lower().split()[0] if inner else "").rstrip("/")
                i = j + 1
                if name == "br":
                    s = self.index(tk.END + "-1c")
                    self.insert(tk.END, "\n")
                    e = self.index(tk.END + "-1c")
                    for t in active:
                        self.tag_add(t, s, e)
                elif name.startswith("/"):
                    clean = name[1:]
                    if clean in _TAG_MAP:
                        tk_tag = _TAG_MAP[clean]
                        if active and active[-1] == tk_tag:
                            active.pop()
                    else:
                        self.insert_raw(full)
                elif name in _TAG_MAP:
                    active.append(_TAG_MAP[name])
                else:
                    self.insert_raw(full)


# ── Helper functions ──────────────────────────────────────────────────────────

def insert_table(html_body_text):
    dialog = tk.Toplevel()
    dialog.title("Táblázat beszúrása")
    dialog.resizable(False, False)
    dialog.grab_set()

    ttk.Label(dialog, text="Sorok száma:").grid(row=0, column=0, padx=14, pady=8, sticky="w")
    rows_var = tk.IntVar(value=3)
    ttk.Spinbox(dialog, from_=1, to=50, textvariable=rows_var, width=6).grid(row=0, column=1, padx=14, pady=8)

    ttk.Label(dialog, text="Oszlopok száma:").grid(row=1, column=0, padx=14, pady=8, sticky="w")
    cols_var = tk.IntVar(value=3)
    ttk.Spinbox(dialog, from_=1, to=20, textvariable=cols_var, width=6).grid(row=1, column=1, padx=14, pady=8)

    def on_ok():
        rows = rows_var.get()
        cols = cols_var.get()
        cell        = '<td style="border:1px solid #000000;padding:5px;">&nbsp;</td>'
        header_cell = '<th style="border:1px solid #000000;padding:5px;background-color:#d9e1f2;">&nbsp;</th>'
        table_html  = (
            '\n<table border="1" cellpadding="5" cellspacing="0" '
            'style="border-collapse:collapse;width:100%;">\n'
            + "  <tr>" + header_cell * cols + "</tr>\n"
            + ("  <tr>" + cell * cols + "</tr>\n") * (rows - 1)
            + "</table>\n"
        )
        if hasattr(html_body_text, 'insert_raw'):
            html_body_text.insert_raw(table_html)
        else:
            html_body_text.insert(tk.INSERT, table_html)
        dialog.destroy()

    ttk.Button(dialog, text="Beszúrás", command=on_ok).grid(row=2, column=0, columnspan=2, pady=12)
    dialog.bind("<Return>", lambda e: on_ok())


def start_email_generation_thread(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    threading.Thread(
        target=email_generation.generate_emails,
        args=(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text),
        daemon=True,
    ).start()


def select_excel_file():
    if IS_MAC:
        r = subprocess.run(
            ["osascript", "-e",
             'set f to choose file with prompt "Válassza ki az Excel fájlt" of type {"xlsx","xls"}\nreturn POSIX path of f'],
            capture_output=True, text=True,
        )
        filepath = r.stdout.strip() if r.returncode == 0 else None
    else:
        filepath = filedialog.askopenfilename(
            title="Válassza ki a cifzetteket tartalmazó Excel fájlt",
            filetypes=[("Excel files", "*.xlsx;*.xls")],
        )
    if filepath:
        table_filename.set(filepath)


def select_attachment_dir():
    if IS_MAC:
        r = subprocess.run(
            ["osascript", "-e",
             'set d to choose folder with prompt "Válassza ki a mellékletek mappáját"\nreturn POSIX path of d'],
            capture_output=True, text=True,
        )
        directory = r.stdout.strip().rstrip("/") if r.returncode == 0 else None
    else:
        directory = filedialog.askdirectory(title="Válassza ki a mellékletek mappáját")
    if directory:
        attachment_dir.set(directory)


# ── GUI ───────────────────────────────────────────────────────────────────────

def create_gui():
    global table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text

    root = tk.Tk()
    root.title("Tömeges emailküldés")
    root.geometry("900x740")
    root.eval('tk::PlaceWindow . center')
    root.configure(bg="#f2f2f7")

    # ── Styles ───────────────────────────────────────────────────────────
    style = ttk.Style()
    style.configure("TFrame",       background="#f2f2f7")
    style.configure("TLabel",       background="#f2f2f7", font=("Verdana", 10))
    style.configure("TEntry",       font=("Verdana", 10))
    style.configure("TButton",      font=("Verdana", 10))
    style.configure("TLabelframe",  background="#f2f2f7")
    style.configure("TLabelframe.Label", font=("Verdana", 10, "bold"),
                    background="#f2f2f7", foreground="#1a1a2e")
    style.configure("Primary.TButton", font=("Verdana", 10, "bold"))

    # ── Variables ────────────────────────────────────────────────────────
    table_filename = tk.StringVar()
    attachment_dir = tk.StringVar()
    status_var     = tk.StringVar(value=settings.current_settings_file)

    # Action helpers (widgets defined later; closures access globals)
    def save_cmd():
        settings.save_settings(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)
        status_var.set(settings.current_settings_file)

    def save_as_cmd():
        settings.save_settings_as(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)
        status_var.set(settings.current_settings_file)

    def load_cmd():
        data = settings.load_settings_gui()
        if data is not None:
            settings.apply_settings(data, table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)
            status_var.set(settings.current_settings_file)

    def reset_cmd():
        settings.reset_settings_to_default(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)

    def generate_cmd():
        start_email_generation_thread(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)

    # ── Menu bar ─────────────────────────────────────────────────────────
    mod     = "Cmd"     if IS_MAC else "Ctrl"
    mod_key = "Command" if IS_MAC else "Control"

    menubar = tk.Menu(root)

    # Fájl
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Mentés",               accelerator=f"{mod}+S",      command=save_cmd)
    file_menu.add_command(label="Mentés másként…",                                   command=save_as_cmd)
    file_menu.add_command(label="Megnyitás…",           accelerator=f"{mod}+O",      command=load_cmd)
    file_menu.add_command(label="Alaphelyzetbe állítás",                             command=reset_cmd)
    file_menu.add_separator()
    file_menu.add_command(label="Kilépés",              command=root.quit)
    menubar.add_cascade(label="Fájl", menu=file_menu)

    # Szerkesztés
    edit_menu = tk.Menu(menubar, tearoff=0)
    edit_menu.add_command(label="Félkövér",             accelerator=f"{mod}+B",
                          command=lambda: html_body_text.toggle_format("bold"))
    edit_menu.add_command(label="Dőlt",                 accelerator=f"{mod}+I",
                          command=lambda: html_body_text.toggle_format("italic"))
    edit_menu.add_command(label="Aláhúzás",             accelerator=f"{mod}+U",
                          command=lambda: html_body_text.toggle_format("underline"))
    edit_menu.add_separator()
    edit_menu.add_command(label="Táblázat beszúrása…",  command=lambda: insert_table(html_body_text))
    menubar.add_cascade(label="Szerkesztés", menu=edit_menu)

    # Email
    email_menu = tk.Menu(menubar, tearoff=0)
    email_menu.add_command(label="Generálás indítása",  accelerator=f"{mod}+Return", command=generate_cmd)
    email_menu.add_command(label="Generálás leállítása",                             command=email_generation.stop_email_generation)
    email_menu.add_separator()
    email_menu.add_command(label="Ablakok bezárása",                                 command=email_generation.close_all_open_email_windows)
    menubar.add_cascade(label="Email", menu=email_menu)

    root.config(menu=menubar)

    # Keyboard shortcuts
    root.bind(f"<{mod_key}-b>",      lambda e: html_body_text.toggle_format("bold"))
    root.bind(f"<{mod_key}-i>",      lambda e: html_body_text.toggle_format("italic"))
    root.bind(f"<{mod_key}-u>",      lambda e: html_body_text.toggle_format("underline"))
    root.bind(f"<{mod_key}-s>",      lambda e: save_cmd())
    root.bind(f"<{mod_key}-o>",      lambda e: load_cmd())
    root.bind(f"<{mod_key}-Return>", lambda e: generate_cmd())

    # ── Main container ────────────────────────────────────────────────────
    outer = ttk.Frame(root, padding=(18, 14))
    outer.pack(fill="both", expand=True)
    outer.rowconfigure(1, weight=1)
    outer.columnconfigure(0, weight=1)

    # ── Fields section ────────────────────────────────────────────────────
    fields = ttk.LabelFrame(outer, text="  Adatok  ", padding=(12, 8))
    fields.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    fields.columnconfigure(1, weight=1)

    def _field_row(parent, row, label, var=None, browse_cmd=None):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        if var is not None:
            e = ttk.Entry(parent, textvariable=var, state='readonly')
        else:
            e = ttk.Entry(parent)
        e.grid(row=row, column=1, sticky="ew", pady=4)
        if browse_cmd:
            ttk.Button(parent, text="Tallózás…", command=browse_cmd).grid(row=row, column=2, padx=(8, 0), pady=4)
        return e

    _field_row(fields, 0, "Excel fájl:",          var=table_filename,  browse_cmd=select_excel_file)
    _field_row(fields, 1, "Mellékletek mappája:",  var=attachment_dir,  browse_cmd=select_attachment_dir)
    sheet_name_entry = _field_row(fields, 2, "Munkalap neve:")
    subject_entry    = _field_row(fields, 3, "Email tárgy:")

    # ── Editor section ────────────────────────────────────────────────────
    editor_lf = ttk.LabelFrame(outer, text="  Email törzs  ", padding=(12, 8))
    editor_lf.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
    editor_lf.rowconfigure(1, weight=1)
    editor_lf.columnconfigure(0, weight=1)

    # Formatting toolbar — sits directly above the editor
    toolbar = tk.Frame(editor_lf, bg="#e4e4e9", bd=0)
    toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))

    bold_font      = tkfont.Font(family="Verdana", size=11, weight="bold")
    italic_font    = tkfont.Font(family="Verdana", size=11, slant="italic")
    underline_font = tkfont.Font(family="Verdana", size=11, underline=True)
    normal_font    = tkfont.Font(family="Verdana", size=10)

    _BTN = dict(relief="flat", bd=0, padx=10, pady=4,
                bg="#e4e4e9", activebackground="#c8c8d4", cursor="arrow")

    tk.Button(toolbar, text="B", font=bold_font,
              command=lambda: html_body_text.toggle_format("bold"),      **_BTN).pack(side="left", padx=(2, 0), pady=3)
    tk.Button(toolbar, text="I", font=italic_font,
              command=lambda: html_body_text.toggle_format("italic"),    **_BTN).pack(side="left", pady=3)
    tk.Button(toolbar, text="U", font=underline_font,
              command=lambda: html_body_text.toggle_format("underline"), **_BTN).pack(side="left", pady=3)

    tk.Frame(toolbar, bg="#b0b0b8", width=1).pack(side="left", fill="y", padx=8, pady=4)

    tk.Button(toolbar, text="⊞  Táblázat", font=normal_font,
              command=lambda: insert_table(html_body_text),              **_BTN).pack(side="left", pady=3)

    # Rich text editor + scrollbar
    html_body_text = RichTextEditor(editor_lf, wrap='word', font=('Verdana', 10),
                                    relief="flat", bd=1, highlightthickness=1,
                                    highlightbackground="#c8c8d0",
                                    highlightcolor="#5e5ce6")
    html_body_text.grid(row=1, column=0, sticky="nsew")
    sb = ttk.Scrollbar(editor_lf, command=html_body_text.yview, orient=VERTICAL)
    html_body_text.config(yscrollcommand=sb.set)
    sb.grid(row=1, column=1, sticky="ns")

    # ── Action buttons ────────────────────────────────────────────────────
    actions = ttk.Frame(outer)
    actions.grid(row=2, column=0, sticky="ew")
    actions.columnconfigure((0, 1, 2), weight=1)

    ttk.Button(actions, text="▶  Email-ek generálása", style="Primary.TButton",
               command=generate_cmd).grid(row=0, column=0, sticky="ew", padx=(0, 5), ipady=5)
    ttk.Button(actions, text="⏹  Leállítás",
               command=email_generation.stop_email_generation).grid(row=0, column=1, sticky="ew", padx=2, ipady=5)
    ttk.Button(actions, text="✕  Ablakok bezárása",
               command=email_generation.close_all_open_email_windows).grid(row=0, column=2, sticky="ew", padx=(5, 0), ipady=5)

    # ── Status bar ────────────────────────────────────────────────────────
    status_bar = tk.Frame(root, bg="#dcdce4", height=24)
    status_bar.pack(side="bottom", fill="x")
    tk.Label(status_bar, textvariable=status_var,
             bg="#dcdce4", fg="#555566", font=("Verdana", 9),
             anchor="w").pack(side="left", padx=10, pady=2)

    # ── Load saved settings ───────────────────────────────────────────────
    settings.apply_settings(
        settings.load_settings(), table_filename, attachment_dir,
        sheet_name_entry, subject_entry, html_body_text,
    )

    root.mainloop()


if __name__ == "__main__":
    create_gui()
