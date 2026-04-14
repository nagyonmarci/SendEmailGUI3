import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, Label, Entry, Button, Text, Scrollbar, VERTICAL, Frame
from tkinter import ttk
import threading
import settings
import email_generation

IS_MAC = sys.platform == 'darwin'


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
        """Toggle a formatting tag on/off for the current selection."""
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
        """Insert raw HTML at the cursor, displayed in grey monospace."""
        start = self.index(tk.INSERT)
        self.insert(tk.INSERT, html_text)
        self.tag_add("raw_html", start, self.index(tk.INSERT))

    def get_html(self):
        """Serialise widget content (with tags) to an HTML string."""
        result  = []
        raw_on  = False
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
        """Parse a simple HTML string and render it with visual formatting tags."""
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


def make_text_bold(html_body_text):
    if hasattr(html_body_text, 'toggle_format'):
        html_body_text.toggle_format("bold")
        return
    try:
        selected_text = html_body_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        html_body_text.delete(tk.SEL_FIRST, tk.SEL_LAST)
        html_body_text.insert(tk.INSERT, f"<b>{selected_text}</b>")
    except tk.TclError:
        pass


def insert_table(html_body_text):
    dialog = tk.Toplevel()
    dialog.title("Táblázat beszúrása")
    dialog.resizable(False, False)
    dialog.grab_set()

    ttk.Label(dialog, text="Sorok száma:").grid(row=0, column=0, padx=10, pady=8, sticky="w")
    rows_var = tk.IntVar(value=3)
    ttk.Spinbox(dialog, from_=1, to=50, textvariable=rows_var, width=6).grid(row=0, column=1, padx=10, pady=8)

    ttk.Label(dialog, text="Oszlopok száma:").grid(row=1, column=0, padx=10, pady=8, sticky="w")
    cols_var = tk.IntVar(value=3)
    ttk.Spinbox(dialog, from_=1, to=20, textvariable=cols_var, width=6).grid(row=1, column=1, padx=10, pady=8)

    def on_ok():
        rows = rows_var.get()
        cols = cols_var.get()
        cell        = '<td style="border:1px solid #000000;padding:5px;">&nbsp;</td>'
        header_cell = '<th style="border:1px solid #000000;padding:5px;background-color:#d9e1f2;">&nbsp;</th>'
        header_row  = "<tr>" + header_cell * cols + "</tr>"
        data_row    = "<tr>" + cell * cols + "</tr>"
        table_html  = (
            '\n<table border="1" cellpadding="5" cellspacing="0" '
            'style="border-collapse:collapse;width:100%;">\n'
            + "  " + header_row + "\n"
            + ("  " + data_row + "\n") * (rows - 1)
            + "</table>\n"
        )
        if hasattr(html_body_text, 'insert_raw'):
            html_body_text.insert_raw(table_html)
        else:
            html_body_text.insert(tk.INSERT, table_html)
        dialog.destroy()

    ttk.Button(dialog, text="Beszúrás", command=on_ok).grid(row=2, column=0, columnspan=2, pady=10)
    dialog.bind("<Return>", lambda e: on_ok())


def start_email_generation_thread(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    email_thread = threading.Thread(
        target=email_generation.generate_emails,
        args=(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)
    )
    email_thread.start()


def create_gui():
    global table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text

    root = tk.Tk()
    root.title("Tömeges emailküldés")
    root.geometry("800x700")
    root.eval('tk::PlaceWindow . center')
    root.configure(bg='#f0f0f0')

    style = ttk.Style()
    style.configure('TButton', font=('Verdana', 10), background='#169dcb')
    style.configure('TLabel',  font=('Verdana', 10), background='#f0f0f0')
    style.configure('TEntry',  font=('Verdana', 10))
    style.configure('TFrame',  padding=10, background='#f0f0f0')

    menubar       = tk.Menu(root)
    settings_menu = tk.Menu(menubar, tearoff=0)
    settings_menu.add_command(label="Beállítások mentése",
        command=lambda: settings.save_settings(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text))
    settings_menu.add_command(label="Beállítások mentése másként",
        command=lambda: settings.save_settings_as(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text))
    settings_menu.add_command(label="Beállítások betöltése",
        command=lambda: settings.apply_settings(settings.load_settings_gui() or {}, table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text))
    settings_menu.add_command(label="Beállítások alaphelyzetbe állítása",
        command=lambda: settings.reset_settings_to_default(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text))
    settings_menu.add_separator()
    settings_menu.add_command(label="Kilépés", command=root.quit)
    menubar.add_cascade(label="Beállítások", menu=settings_menu)
    root.config(menu=menubar)

    table_filename = tk.StringVar()
    attachment_dir = tk.StringVar()

    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    main_frame.rowconfigure(4, weight=1)
    main_frame.columnconfigure(1, weight=1)

    ttk.Label(main_frame, text="Excel fájl:").grid(row=0, column=0, sticky="w", pady=5)
    ttk.Entry(main_frame, textvariable=table_filename, state='readonly', width=50).grid(row=0, column=1, pady=5)
    ttk.Button(main_frame, text="Tallózás...", command=select_excel_file).grid(row=0, column=2, pady=5)

    ttk.Label(main_frame, text="Mellékletek mappája:").grid(row=1, column=0, sticky="w", pady=5)
    ttk.Entry(main_frame, textvariable=attachment_dir, state='readonly', width=50).grid(row=1, column=1, pady=5)
    ttk.Button(main_frame, text="Tallózás...", command=select_attachment_dir).grid(row=1, column=2, pady=5)

    ttk.Label(main_frame, text="Munkalap név:").grid(row=2, column=0, sticky="w", pady=5)
    sheet_name_entry = ttk.Entry(main_frame, width=50)
    sheet_name_entry.grid(row=2, column=1, pady=5)

    ttk.Label(main_frame, text="Email tárgy:").grid(row=3, column=0, sticky="w", pady=5)
    subject_entry = ttk.Entry(main_frame, width=50)
    subject_entry.grid(row=3, column=1, pady=5)

    ttk.Label(main_frame, text="Email HTML törzs:").grid(row=4, column=0, sticky="nw", pady=5)
    html_body_text = RichTextEditor(main_frame, height=20, width=70, wrap='word', font=('Verdana', 10))
    html_body_text.grid(row=4, column=1, columnspan=2, pady=5, sticky="nsew")
    scrollbar = ttk.Scrollbar(main_frame, command=html_body_text.yview, orient=VERTICAL)
    html_body_text.config(yscrollcommand=scrollbar.set)
    scrollbar.grid(row=4, column=3, sticky='ns', pady=5)

    format_frame = ttk.Frame(main_frame)
    format_frame.grid(row=5, column=0, columnspan=3, pady=10)
    ttk.Button(format_frame, text="Félkövér",  command=lambda: html_body_text.toggle_format("bold")).grid(row=0, column=0, padx=5)
    ttk.Button(format_frame, text="Dőlt",      command=lambda: html_body_text.toggle_format("italic")).grid(row=0, column=1, padx=5)
    ttk.Button(format_frame, text="Aláhúzás",  command=lambda: html_body_text.toggle_format("underline")).grid(row=0, column=2, padx=5)
    ttk.Button(format_frame, text="Táblázat",  command=lambda: insert_table(html_body_text)).grid(row=0, column=3, padx=5)

    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=6, column=0, columnspan=3, pady=10)

    ttk.Button(button_frame, text="Email-ek generálása",
        command=lambda: start_email_generation_thread(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)
    ).grid(row=0, column=0, padx=5, pady=5)
    ttk.Button(button_frame, text="Generálás leállítása",
        command=email_generation.stop_email_generation).grid(row=0, column=1, padx=5, pady=5)
    ttk.Button(button_frame, text="E-mail-ek bezárása",
        command=email_generation.close_all_open_email_windows).grid(row=0, column=2, padx=5, pady=5)

    ttk.Button(button_frame, text="Beállítások mentése",
        command=lambda: settings.save_settings(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)
    ).grid(row=1, column=0, padx=5, pady=5)
    ttk.Button(button_frame, text="Mentés másként",
        command=lambda: settings.save_settings_as(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)
    ).grid(row=1, column=1, padx=5, pady=5)
    ttk.Button(button_frame, text="Beállítások betöltése",
        command=lambda: settings.apply_settings(settings.load_settings_gui() or {}, table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)
    ).grid(row=1, column=2, padx=5, pady=5)
    ttk.Button(button_frame, text="Alaphelyzetbe állítás",
        command=lambda: settings.reset_settings_to_default(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)
    ).grid(row=1, column=3, padx=5, pady=5)

    settings.apply_settings(settings.load_settings(), table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)

    root.mainloop()


def select_excel_file():
    if IS_MAC:
        r = subprocess.run(
            ["osascript", "-e",
             'set f to choose file with prompt "Válassza ki az Excel fájlt" of type {"xlsx","xls"}\nreturn POSIX path of f'],
            capture_output=True, text=True
        )
        filepath = r.stdout.strip() if r.returncode == 0 else None
    else:
        filepath = filedialog.askopenfilename(
            title="Válassza ki a cifzetteket tartalmazó Excel fájlt",
            filetypes=[("Excel files", "*.xlsx;*.xls")]
        )
    if filepath:
        table_filename.set(filepath)


def select_attachment_dir():
    if IS_MAC:
        r = subprocess.run(
            ["osascript", "-e",
             'set d to choose folder with prompt "Válassza ki a mellékletek mappáját"\nreturn POSIX path of d'],
            capture_output=True, text=True
        )
        directory = r.stdout.strip().rstrip("/") if r.returncode == 0 else None
    else:
        directory = filedialog.askdirectory(title="Válassza ki a mellékletek mappáját")
    if directory:
        attachment_dir.set(directory)


if __name__ == "__main__":
    create_gui()
