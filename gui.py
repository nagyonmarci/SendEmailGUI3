import re
import sys
import subprocess
import tkinter as tk
import tkinter.font as tkfont
import tkinter.messagebox as messagebox
from tkinter import colorchooser, filedialog, VERTICAL
from tkinter import ttk
import threading
import openpyxl
import i18n
import settings
import email_generation
from version import __version__

IS_MAC = sys.platform == 'darwin'


# ── Table HTML parser ─────────────────────────────────────────────────────────

def _parse_table_html(html):
    rows = []
    low  = html.lower()
    pos  = 0
    while True:
        tr_start = low.find("<tr", pos)
        if tr_start == -1:
            break
        tr_end = low.find("</tr>", tr_start)
        if tr_end == -1:
            break
        row_html = html[tr_start:tr_end]
        row_low  = row_html.lower()
        row = []
        cp = 0
        while True:
            td_p = row_low.find("<td", cp)
            th_p = row_low.find("<th", cp)
            if td_p == -1 and th_p == -1:
                break
            if td_p == -1:
                cs, tn = th_p, "th"
            elif th_p == -1:
                cs, tn = td_p, "td"
            else:
                cs, tn = (td_p, "td") if td_p < th_p else (th_p, "th")
            content_start = row_low.find(">", cs) + 1
            close         = f"</{tn}>"
            cell_end      = row_low.find(close, content_start)
            if cell_end == -1:
                cp = content_start
                continue
            val = row_html[content_start:cell_end].strip()
            val = val.replace("&nbsp;", "").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
            row.append(val)
            cp = cell_end + len(close)
        rows.append(row)
        pos = tr_end + 5
    return rows


# ── Embedded table widget ─────────────────────────────────────────────────────

class TableWidget(tk.Frame):
    def __init__(self, master, rows, cols, **kwargs):
        super().__init__(master, bg="#ffffff", bd=1, relief="solid", **kwargs)
        self.rows  = rows
        self.cols  = cols
        self.cells = []
        for r in range(rows):
            row_cells = []
            for c in range(cols):
                bg = "#d9e1f2" if r == 0 else "#ffffff"
                e  = tk.Entry(self, width=10, font=("Verdana", 9),
                              bg=bg, relief="solid", bd=1, highlightthickness=0)
                e.grid(row=r, column=c, padx=0, pady=0, ipadx=4, ipady=3, sticky="nsew")
                self.columnconfigure(c, weight=1)
                row_cells.append(e)
            self.cells.append(row_cells)

    def get_html(self):
        rows_html = []
        for r, row in enumerate(self.cells):
            cells_html = []
            for cell in row:
                raw = cell.get()
                val = (raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                       if raw else "&nbsp;")
                if r == 0:
                    cells_html.append(
                        f'<th style="border:1px solid #000000;padding:5px;'
                        f'background-color:#d9e1f2;">{val}</th>'
                    )
                else:
                    cells_html.append(
                        f'<td style="border:1px solid #000000;padding:5px;">{val}</td>'
                    )
            rows_html.append("  <tr>" + "".join(cells_html) + "</tr>")
        return (
            '\n<table border="1" cellpadding="5" cellspacing="0" '
            'style="border-collapse:collapse;width:100%;">\n'
            + "\n".join(rows_html)
            + "\n</table>\n"
        )

    def set_content(self, table_data):
        for r, row_data in enumerate(table_data[:self.rows]):
            for c, val in enumerate(row_data[:self.cols]):
                if r < len(self.cells) and c < len(self.cells[r]):
                    self.cells[r][c].delete(0, tk.END)
                    self.cells[r][c].insert(0, val)


# ── WYSIWYG Rich Text Editor ──────────────────────────────────────────────────

class RichTextEditor(tk.Text):
    """WYSIWYG editor with bold/italic/underline, font, size, color, alignment.

    HTML is serialised via get_html() and deserialised via set_html().
    Tables are embedded as editable TableWidget frames.
    """

    def __init__(self, master, **kwargs):
        font   = kwargs.get("font", ("Verdana", 10))
        family = font[0] if isinstance(font, tuple) and len(font) >= 1 else "Verdana"
        size   = font[1] if isinstance(font, tuple) and len(font) >= 2 else 10
        super().__init__(master, **kwargs)
        self.tag_configure("bold",      font=(family, size, "bold"))
        self.tag_configure("italic",    font=(family, size, "italic"))
        self.tag_configure("underline", underline=True)
        self.tag_configure("raw_html",  foreground="#aaaaaa", font=("Courier", 9))
        self._embedded_tables = {}

    # ── Character formatting ──────────────────────────────────────────────

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

    def apply_font(self, family):
        try:
            sel_first = self.index(tk.SEL_FIRST)
            sel_last  = self.index(tk.SEL_LAST)
        except tk.TclError:
            return
        for tag in list(self.tag_names()):
            if tag.startswith("font_"):
                self.tag_remove(tag, sel_first, sel_last)
        if family:
            tag_name = f"font_{family.replace(' ', '_')}"
            if tag_name not in self.tag_names():
                self.tag_configure(tag_name, font=(family, 10))
            self.tag_add(tag_name, sel_first, sel_last)

    def apply_size(self, size):
        try:
            sel_first = self.index(tk.SEL_FIRST)
            sel_last  = self.index(tk.SEL_LAST)
        except tk.TclError:
            return
        for tag in list(self.tag_names()):
            if tag.startswith("size_"):
                self.tag_remove(tag, sel_first, sel_last)
        tag_name = f"size_{size}"
        if tag_name not in self.tag_names():
            self.tag_configure(tag_name, font=("Verdana", int(size)))
        self.tag_add(tag_name, sel_first, sel_last)

    def apply_color(self, hex_color):
        try:
            sel_first = self.index(tk.SEL_FIRST)
            sel_last  = self.index(tk.SEL_LAST)
        except tk.TclError:
            return
        for tag in list(self.tag_names()):
            if tag.startswith("color_"):
                self.tag_remove(tag, sel_first, sel_last)
        if hex_color:
            clean    = hex_color.lstrip("#").upper()
            tag_name = f"color_{clean}"
            if tag_name not in self.tag_names():
                self.tag_configure(tag_name, foreground=f"#{clean}")
            self.tag_add(tag_name, sel_first, sel_last)

    def apply_alignment(self, direction):
        try:
            sel_first = self.index(tk.SEL_FIRST + " linestart")
            sel_last  = self.index(tk.SEL_LAST  + " lineend+1c")
        except tk.TclError:
            sel_first = self.index("insert linestart")
            sel_last  = self.index("insert lineend+1c")
        for tag in ("align_center", "align_right"):
            self.tag_remove(tag, sel_first, sel_last)
        if direction in ("center", "right"):
            tag_name = f"align_{direction}"
            if tag_name not in self.tag_names():
                self.tag_configure(tag_name, justify=direction)
            self.tag_add(tag_name, sel_first, sel_last)

    # ── Raw HTML fallback ─────────────────────────────────────────────────

    def insert_raw(self, html_text):
        start = self.index(tk.INSERT)
        self.insert(tk.INSERT, html_text)
        self.tag_add("raw_html", start, self.index(tk.INSERT))

    # ── Table widget ──────────────────────────────────────────────────────

    def insert_table_widget(self, rows, cols):
        tw = TableWidget(self, rows, cols)
        self.window_create(tk.INSERT, window=tw)
        self._embedded_tables[str(tw)] = tw
        self.insert(tk.INSERT, "\n")

    # ── HTML serialisation ────────────────────────────────────────────────

    def get_html(self):
        result      = []
        active      = set()
        span_style  = [None]
        align_state = [None]
        raw_on      = [False]

        def inline_style():
            parts = []
            if "bold"      in active: parts.append("font-weight:bold")
            if "italic"    in active: parts.append("font-style:italic")
            if "underline" in active: parts.append("text-decoration:underline")
            for t in sorted(active):
                if t.startswith("font_"):
                    fam = t[5:].replace("_", " ")
                    parts.append(f'font-family:"{fam}"' if " " in fam else f"font-family:{fam}")
                elif t.startswith("size_"):
                    parts.append(f"font-size:{t[5:]}pt")
                elif t.startswith("color_"):
                    parts.append(f"color:#{t[6:]}")
            return ";".join(parts) or None

        def cur_align():
            for t in active:
                if t in ("align_center", "align_right"):
                    return t[6:]
            return None

        def close_span():
            if span_style[0]:
                result.append("</span>")
                span_style[0] = None

        def open_span(style):
            if style:
                result.append(f'<span style="{style}">')
                span_style[0] = style

        def sync():
            new_align = cur_align()
            new_style = inline_style()
            if new_align != align_state[0]:
                close_span()
                if align_state[0]:
                    result.append("</div>")
                if new_align:
                    result.append(f'<div style="text-align:{new_align};">')
                align_state[0] = new_align
                open_span(new_style)
            elif new_style != span_style[0]:
                close_span()
                open_span(new_style)

        for key, value, _ in self.dump("1.0", "end-1c", text=True, tag=True, window=True):
            if key == "tagon":
                active.add(value)
                raw_on[0] = "raw_html" in active
                if not raw_on[0]:
                    sync()
            elif key == "tagoff":
                active.discard(value)
                raw_on[0] = "raw_html" in active
                if not raw_on[0]:
                    sync()
            elif key == "text":
                if raw_on[0]:
                    result.append(value)
                else:
                    result.append(value.replace("\n", "<br>"))
            elif key == "window":
                tw = self._embedded_tables.get(value)
                if tw:
                    result.append(tw.get_html())

        close_span()
        if align_state[0]:
            result.append("</div>")
        return "".join(result)

    # ── HTML deserialisation ──────────────────────────────────────────────

    def set_html(self, html):
        for tw in self._embedded_tables.values():
            try:
                tw.destroy()
            except Exception:
                pass
        self._embedded_tables.clear()
        self.delete("1.0", tk.END)
        if not html:
            return

        tag_stack = []   # [(html_open_tag_name, [tk_tags])]

        def active_tags():
            return [t for _, tags in tag_stack for t in tags]

        def ensure_tag(tag):
            if tag in self.tag_names():
                return
            if   tag == "bold":      self.tag_configure(tag, font=("Verdana", 10, "bold"))
            elif tag == "italic":    self.tag_configure(tag, font=("Verdana", 10, "italic"))
            elif tag == "underline": self.tag_configure(tag, underline=True)
            elif tag.startswith("font_"):
                self.tag_configure(tag, font=(tag[5:].replace("_", " "), 10))
            elif tag.startswith("size_"):
                self.tag_configure(tag, font=("Verdana", int(tag[5:])))
            elif tag.startswith("color_"):
                self.tag_configure(tag, foreground=f"#{tag[6:]}")
            elif tag.startswith("align_"):
                self.tag_configure(tag, justify=tag[6:])

        def style_to_tags(inner):
            m = re.search(r'style=["\']([^"\']*)["\']', inner, re.IGNORECASE)
            if not m:
                return []
            tags = []
            for item in m.group(1).split(";"):
                item = item.strip()
                if ":" not in item:
                    continue
                k, v = item.split(":", 1)
                k, v = k.strip().lower(), v.strip().strip("\"'")
                if   k == "font-weight" and "bold"    in v: tags.append("bold")
                elif k == "font-style"  and "italic"  in v: tags.append("italic")
                elif k == "text-decoration" and "underline" in v: tags.append("underline")
                elif k == "font-family":
                    tags.append(f"font_{v.replace(' ', '_')}")
                elif k == "font-size":
                    s = v.rstrip("pt").rstrip("px").strip()
                    if s.isdigit():
                        tags.append(f"size_{s}")
                elif k == "color":
                    tags.append(f"color_{v.lstrip('#').upper()}")
                elif k == "text-align" and v in ("center", "right"):
                    tags.append(f"align_{v}")
            return tags

        def push_tag(html_name, tk_tags):
            for t in tk_tags:
                ensure_tag(t)
            tag_stack.append((html_name, tk_tags))

        def pop_tag(html_name):
            for idx in range(len(tag_stack) - 1, -1, -1):
                if tag_stack[idx][0] == html_name:
                    tag_stack.pop(idx)
                    return

        _SIMPLE = {"b": "bold", "strong": "bold", "i": "italic", "em": "italic", "u": "underline"}

        i = 0
        while i < len(html):
            if html[i] != "<":
                j     = html.find("<", i)
                chunk = html[i:] if j == -1 else html[i:j]
                if chunk:
                    s = self.index(tk.END + "-1c")
                    self.insert(tk.END, chunk)
                    e = self.index(tk.END + "-1c")
                    for t in active_tags():
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
                    for t in active_tags():
                        self.tag_add(t, s, e)
                elif name == "table":
                    end_idx = html.lower().find("</table>", i)
                    if end_idx != -1:
                        full_table = full + html[i:end_idx + 8]
                        table_data = _parse_table_html(full_table)
                        rows = len(table_data)
                        cols = max((len(r) for r in table_data), default=1) if rows else 0
                        if rows > 0 and cols > 0:
                            tw = TableWidget(self, rows, cols)
                            tw.set_content(table_data)
                            self.window_create(tk.END, window=tw)
                            self._embedded_tables[str(tw)] = tw
                            self.insert(tk.END, "\n")
                        i = end_idx + 8
                    else:
                        self.insert_raw(full)
                elif name in _SIMPLE:
                    push_tag(name, [_SIMPLE[name]])
                elif name.startswith("/") and name[1:] in _SIMPLE:
                    pop_tag(name[1:])
                elif name in ("span", "div", "p"):
                    push_tag(name, style_to_tags(inner))
                elif name.startswith("/") and name[1:] in ("span", "div", "p"):
                    pop_tag(name[1:])
                else:
                    if not name.startswith("/"):
                        self.insert_raw(full)


# ── Helper functions ──────────────────────────────────────────────────────────

def insert_table(html_body_text):
    dialog = tk.Toplevel()
    dialog.title(i18n.t("dlg_table_title"))
    dialog.resizable(False, False)
    dialog.grab_set()

    ttk.Label(dialog, text=i18n.t("dlg_rows")).grid(row=0, column=0, padx=14, pady=8, sticky="w")
    rows_var = tk.IntVar(value=3)
    ttk.Spinbox(dialog, from_=1, to=50, textvariable=rows_var, width=6).grid(row=0, column=1, padx=14, pady=8)

    ttk.Label(dialog, text=i18n.t("dlg_cols")).grid(row=1, column=0, padx=14, pady=8, sticky="w")
    cols_var = tk.IntVar(value=3)
    ttk.Spinbox(dialog, from_=1, to=20, textvariable=cols_var, width=6).grid(row=1, column=1, padx=14, pady=8)

    def on_ok():
        if hasattr(html_body_text, 'insert_table_widget'):
            html_body_text.insert_table_widget(rows_var.get(), cols_var.get())
        dialog.destroy()

    ttk.Button(dialog, text=i18n.t("dlg_insert"), command=on_ok).grid(row=2, column=0, columnspan=2, pady=12)
    dialog.bind("<Return>", lambda e: on_ok())


def start_email_generation_thread(root, table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    def on_done(missing_files):
        if missing_files:
            msg = i18n.t("warn_missing_files") + "\n\n" + "\n".join(missing_files)
            root.after(0, lambda: messagebox.showwarning(i18n.t("warn_missing_title"), msg))

    threading.Thread(
        target=email_generation.generate_emails,
        args=(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text),
        kwargs={"on_done": on_done},
        daemon=True,
    ).start()


def _load_sheets(path):
    """Populate the sheet-name combobox from the given Excel file."""
    try:
        wb = openpyxl.load_workbook(path, read_only=True)
        names = wb.sheetnames
        wb.close()
    except Exception:
        names = []
    sheet_name_entry['values'] = names
    current = sheet_name_entry.get()
    if names and current not in names:
        sheet_name_entry.set(names[0])


def select_excel_file():
    if IS_MAC:
        r = subprocess.run(
            ["osascript", "-e",
             f'set f to choose file with prompt "{i18n.t("fdlg_excel")}" of type {{"xlsx","xls"}}\nreturn POSIX path of f'],
            capture_output=True, text=True,
        )
        filepath = r.stdout.strip() if r.returncode == 0 else None
    else:
        filepath = filedialog.askopenfilename(
            title=i18n.t("fdlg_excel"),
            filetypes=[("Excel files", "*.xlsx;*.xls")],
        )
    if filepath:
        table_filename.set(filepath)
        _load_sheets(filepath)


def select_attachment_dir():
    if IS_MAC:
        r = subprocess.run(
            ["osascript", "-e",
             f'set d to choose folder with prompt "{i18n.t("fdlg_attachments")}"\nreturn POSIX path of d'],
            capture_output=True, text=True,
        )
        directory = r.stdout.strip().rstrip("/") if r.returncode == 0 else None
    else:
        directory = filedialog.askdirectory(title=i18n.t("fdlg_attachments"))
    if directory:
        attachment_dir.set(directory)


# ── GUI ───────────────────────────────────────────────────────────────────────

def create_gui():
    global table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text

    root = tk.Tk()
    root.geometry("960x760")
    root.eval('tk::PlaceWindow . center')
    root.configure(bg="#f2f2f7")

    style = ttk.Style()
    style.configure("TFrame",       background="#f2f2f7")
    style.configure("TLabel",       background="#f2f2f7", font=("Verdana", 10))
    style.configure("TEntry",       font=("Verdana", 10))
    style.configure("TButton",      font=("Verdana", 10))
    style.configure("TLabelframe",  background="#f2f2f7")
    style.configure("TLabelframe.Label", font=("Verdana", 10, "bold"),
                    background="#f2f2f7", foreground="#1a1a2e")
    style.configure("Primary.TButton", font=("Verdana", 10, "bold"))

    table_filename = tk.StringVar()
    attachment_dir = tk.StringVar()
    status_var     = tk.StringVar(value=settings.current_settings_file)

    _w           = {}
    _browse_btns = []
    _menubar     = [None]

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
            _load_sheets(table_filename.get())
            apply_language(i18n.get_lang())
            status_var.set(settings.current_settings_file)

    def reset_cmd():
        settings.reset_settings_to_default(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)

    def generate_cmd():
        start_email_generation_thread(root, table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)

    def _build_menubar():
        if _menubar[0] is not None:
            _menubar[0].destroy()
        mod     = "Cmd" if IS_MAC else "Ctrl"
        menubar = tk.Menu(root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=i18n.t("menu_save"),    accelerator=f"{mod}+S", command=save_cmd)
        file_menu.add_command(label=i18n.t("menu_save_as"),                         command=save_as_cmd)
        file_menu.add_command(label=i18n.t("menu_open"),    accelerator=f"{mod}+O", command=load_cmd)
        file_menu.add_command(label=i18n.t("menu_reset"),                           command=reset_cmd)
        file_menu.add_separator()
        lang_menu = tk.Menu(file_menu, tearoff=0)
        lang_menu.add_command(label="Magyar",  command=lambda: apply_language("hu"))
        lang_menu.add_command(label="English", command=lambda: apply_language("en"))
        file_menu.add_cascade(label=i18n.t("menu_language"), menu=lang_menu)
        file_menu.add_separator()
        file_menu.add_command(label=i18n.t("menu_quit"), command=root.quit)
        menubar.add_cascade(label=i18n.t("menu_file"), menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label=i18n.t("menu_bold"),         accelerator=f"{mod}+B",
                              command=lambda: html_body_text.toggle_format("bold"))
        edit_menu.add_command(label=i18n.t("menu_italic"),       accelerator=f"{mod}+I",
                              command=lambda: html_body_text.toggle_format("italic"))
        edit_menu.add_command(label=i18n.t("menu_underline"),    accelerator=f"{mod}+U",
                              command=lambda: html_body_text.toggle_format("underline"))
        edit_menu.add_separator()
        edit_menu.add_command(label=i18n.t("menu_insert_table"), command=lambda: insert_table(html_body_text))
        menubar.add_cascade(label=i18n.t("menu_edit"), menu=edit_menu)

        email_menu = tk.Menu(menubar, tearoff=0)
        email_menu.add_command(label=i18n.t("menu_generate"),      accelerator=f"{mod}+Return", command=generate_cmd)
        email_menu.add_command(label=i18n.t("menu_stop"),                                       command=email_generation.stop_email_generation)
        email_menu.add_separator()
        email_menu.add_command(label=i18n.t("menu_close_windows"),                              command=email_generation.close_all_open_email_windows)
        menubar.add_cascade(label=i18n.t("menu_email"), menu=email_menu)

        root.config(menu=menubar)
        _menubar[0] = menubar

    def apply_language(lang):
        i18n.set_lang(lang)
        root.title(f"{i18n.t('window_title')} v{__version__}")
        for key, widget in _w.items():
            widget.config(text=i18n.t(key))
        for btn in _browse_btns:
            btn.config(text=i18n.t("btn_browse"))
        _build_menubar()

    # ── Main container ────────────────────────────────────────────────────
    outer = ttk.Frame(root, padding=(18, 14))
    outer.pack(fill="both", expand=True)
    outer.rowconfigure(1, weight=1)
    outer.columnconfigure(0, weight=1)

    # ── Fields section ────────────────────────────────────────────────────
    fields_lf = ttk.LabelFrame(outer, text=i18n.t("section_data"), padding=(12, 8))
    fields_lf.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    fields_lf.columnconfigure(1, weight=1)
    _w["section_data"] = fields_lf

    def _field_row(parent, row, lbl_key, var=None, browse_cmd=None):
        lbl = ttk.Label(parent, text=i18n.t(lbl_key))
        lbl.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        _w[lbl_key] = lbl
        e = ttk.Entry(parent, textvariable=var, state='readonly') if var is not None else ttk.Entry(parent)
        e.grid(row=row, column=1, sticky="ew", pady=4)
        if browse_cmd:
            btn = ttk.Button(parent, text=i18n.t("btn_browse"), command=browse_cmd)
            btn.grid(row=row, column=2, padx=(8, 0), pady=4)
            _browse_btns.append(btn)
        return e

    _field_row(fields_lf, 0, "label_excel",      var=table_filename, browse_cmd=select_excel_file)
    _field_row(fields_lf, 1, "label_attachments", var=attachment_dir, browse_cmd=select_attachment_dir)

    lbl_sheet = ttk.Label(fields_lf, text=i18n.t("label_sheet"))
    lbl_sheet.grid(row=2, column=0, sticky="w", padx=(0, 10), pady=4)
    _w["label_sheet"] = lbl_sheet
    sheet_name_entry = ttk.Combobox(fields_lf, state="readonly", font=("Verdana", 10))
    sheet_name_entry.grid(row=2, column=1, sticky="ew", pady=4)

    subject_entry    = _field_row(fields_lf, 3, "label_subject")

    # ── Editor section ────────────────────────────────────────────────────
    editor_lf = ttk.LabelFrame(outer, text=i18n.t("section_body"), padding=(12, 8))
    editor_lf.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
    editor_lf.rowconfigure(1, weight=1)
    editor_lf.columnconfigure(0, weight=1)
    _w["section_body"] = editor_lf

    # ── Formatting toolbar ────────────────────────────────────────────────
    toolbar = tk.Frame(editor_lf, bg="#e4e4e9", bd=0)
    toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))

    bold_font      = tkfont.Font(family="Verdana", size=11, weight="bold")
    italic_font    = tkfont.Font(family="Verdana", size=11, slant="italic")
    underline_font = tkfont.Font(family="Verdana", size=11, underline=True)
    normal_font    = tkfont.Font(family="Verdana", size=10)

    _BTN = dict(relief="flat", bd=0, padx=8, pady=4,
                bg="#e4e4e9", activebackground="#c8c8d4", cursor="arrow")

    def _sep():
        tk.Frame(toolbar, bg="#b0b0b8", width=1).pack(side="left", fill="y", padx=6, pady=4)

    # Font family
    FONTS = ["Verdana", "Arial", "Times New Roman", "Courier New",
             "Georgia", "Calibri", "Trebuchet MS"]
    font_var = tk.StringVar(value="Verdana")
    font_cb  = ttk.Combobox(toolbar, textvariable=font_var, values=FONTS,
                            width=13, state="readonly", font=("Verdana", 9))
    font_cb.pack(side="left", padx=(4, 0), pady=4)
    font_cb.bind("<<ComboboxSelected>>",
                 lambda e: (html_body_text.apply_font(font_var.get()), html_body_text.focus_set()))

    # Font size
    SIZES = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36"]
    size_var = tk.StringVar(value="10")
    size_cb  = ttk.Combobox(toolbar, textvariable=size_var, values=SIZES,
                            width=4, state="readonly", font=("Verdana", 9))
    size_cb.pack(side="left", padx=(4, 0), pady=4)
    size_cb.bind("<<ComboboxSelected>>",
                 lambda e: (html_body_text.apply_size(size_var.get()), html_body_text.focus_set()))

    # Color picker
    _color = ["#184879"]
    color_btn = tk.Button(toolbar, text=" A ", font=underline_font,
                          fg=_color[0], command=lambda: None, **_BTN)
    color_btn.pack(side="left", padx=(4, 0), pady=4)

    def pick_color():
        res = colorchooser.askcolor(color=_color[0], title=i18n.t("toolbar_color"))
        if res[1]:
            _color[0] = res[1]
            color_btn.config(fg=res[1])
            html_body_text.apply_color(res[1])
            html_body_text.focus_set()

    color_btn.config(command=pick_color)

    _sep()

    # Bold / Italic / Underline
    tk.Button(toolbar, text="B", font=bold_font,
              command=lambda: html_body_text.toggle_format("bold"),      **_BTN).pack(side="left", pady=4)
    tk.Button(toolbar, text="I", font=italic_font,
              command=lambda: html_body_text.toggle_format("italic"),    **_BTN).pack(side="left", pady=4)
    tk.Button(toolbar, text="U", font=underline_font,
              command=lambda: html_body_text.toggle_format("underline"), **_BTN).pack(side="left", pady=4)

    _sep()

    # Alignment
    tk.Button(toolbar, text="←", font=normal_font,
              command=lambda: html_body_text.apply_alignment("left"),   **_BTN).pack(side="left", pady=4)
    tk.Button(toolbar, text="↔", font=normal_font,
              command=lambda: html_body_text.apply_alignment("center"), **_BTN).pack(side="left", pady=4)
    tk.Button(toolbar, text="→", font=normal_font,
              command=lambda: html_body_text.apply_alignment("right"),  **_BTN).pack(side="left", pady=4)

    _sep()

    # Table
    tbl_btn = tk.Button(toolbar, text=i18n.t("toolbar_table"), font=normal_font,
                        command=lambda: insert_table(html_body_text), **_BTN)
    tbl_btn.pack(side="left", pady=4)
    _w["toolbar_table"] = tbl_btn

    # ── Rich text editor + scrollbar ──────────────────────────────────────
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

    btn_gen = ttk.Button(actions, text=i18n.t("btn_generate"), style="Primary.TButton", command=generate_cmd)
    btn_gen.grid(row=0, column=0, sticky="ew", padx=(0, 5), ipady=5)
    _w["btn_generate"] = btn_gen

    btn_stp = ttk.Button(actions, text=i18n.t("btn_stop"), command=email_generation.stop_email_generation)
    btn_stp.grid(row=0, column=1, sticky="ew", padx=2, ipady=5)
    _w["btn_stop"] = btn_stp

    btn_cls = ttk.Button(actions, text=i18n.t("btn_close_windows"), command=email_generation.close_all_open_email_windows)
    btn_cls.grid(row=0, column=2, sticky="ew", padx=(5, 0), ipady=5)
    _w["btn_close_windows"] = btn_cls

    # ── Status bar ────────────────────────────────────────────────────────
    status_bar = tk.Frame(root, bg="#dcdce4", height=24)
    status_bar.pack(side="bottom", fill="x")
    tk.Label(status_bar, textvariable=status_var,
             bg="#dcdce4", fg="#555566", font=("Verdana", 9),
             anchor="w").pack(side="left", padx=10, pady=2)

    # ── Keyboard shortcuts ────────────────────────────────────────────────
    mod_key = "Command" if IS_MAC else "Control"
    root.bind(f"<{mod_key}-b>",      lambda e: html_body_text.toggle_format("bold"))
    root.bind(f"<{mod_key}-i>",      lambda e: html_body_text.toggle_format("italic"))
    root.bind(f"<{mod_key}-u>",      lambda e: html_body_text.toggle_format("underline"))
    root.bind(f"<{mod_key}-s>",      lambda e: save_cmd())
    root.bind(f"<{mod_key}-o>",      lambda e: load_cmd())
    root.bind(f"<{mod_key}-Return>", lambda e: generate_cmd())

    # ── Initial load ──────────────────────────────────────────────────────
    initial = settings.load_settings()
    settings.apply_settings(initial, table_filename, attachment_dir,
                            sheet_name_entry, subject_entry, html_body_text)
    _load_sheets(table_filename.get())
    apply_language(i18n.get_lang())

    def on_close():
        save_cmd()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    create_gui()
