import tkinter as tk
from tkinter import filedialog, Label, Entry, Button, Text, Scrollbar, VERTICAL, Frame
from tkinter import ttk
import threading
import settings
import email_generation

def make_text_bold(html_body_text):
    try:
        selected_text = html_body_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        html_body_text.delete(tk.SEL_FIRST, tk.SEL_LAST)
        html_body_text.insert(tk.INSERT, f"<b>{selected_text}</b>")
    except tk.TclError:
        print("Nincs kiválasztott szöveg.")


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
        cell = '<td style="border:1px solid #000000;padding:5px;">&nbsp;</td>'
        header_cell = '<th style="border:1px solid #000000;padding:5px;background-color:#d9e1f2;">&nbsp;</th>'
        header_row = "<tr>" + header_cell * cols + "</tr>"
        data_row = "<tr>" + cell * cols + "</tr>"
        table_html = (
            '\n<table border="1" cellpadding="5" cellspacing="0" '
            'style="border-collapse:collapse;width:100%;">\n'
            + "  " + header_row + "\n"
            + ("  " + data_row + "\n") * (rows - 1)
            + "</table>\n"
        )
        html_body_text.insert(tk.INSERT, table_html)
        dialog.destroy()

    ttk.Button(dialog, text="Beszúrás", command=on_ok).grid(row=2, column=0, columnspan=2, pady=10)
    dialog.bind("<Return>", lambda e: on_ok())

def start_email_generation_thread(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text):
    global stop_generation
    stop_requested = False
    email_thread = threading.Thread(target=email_generation.generate_emails, args=(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text))
    email_thread.start()

def create_gui():
    global table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text

    root = tk.Tk()
    root.title("Tömeges emailküldés")
    root.geometry("800x700")
    root.eval('tk::PlaceWindow . center')

    # Háttérszín beállítása
    root.configure(bg='#f0f0f0')

    style = ttk.Style()
    style.configure('TButton', font=('Verdana', 10), background='#169dcb')
    style.configure('TLabel', font=('Verdana', 10), background='#f0f0f0')
    style.configure('TEntry', font=('Verdana', 10))
    style.configure('TText', font=('Verdana', 10))
    style.configure('TFrame', padding=10, background='#f0f0f0')

    # Menüsáv hozzáadása
    menubar = tk.Menu(root)
    settings_menu = tk.Menu(menubar, tearoff=0)
    settings_menu.add_command(label="Beállítások mentése", command=lambda: settings.save_settings(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text))
    settings_menu.add_command(label="Beállítások mentése másként", command=lambda: settings.save_settings_as(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text))
    settings_menu.add_command(label="Beállítások betöltése", command=lambda: settings.apply_settings(settings.load_settings_gui(), table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text))
    settings_menu.add_command(label="Beállítások alaphelyzetbe állítása", command=lambda: settings.reset_settings_to_default(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text))
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

    ttk.Label(main_frame, text="Email HTML törzs:").grid(row=4, column=0, sticky="w", pady=5)
    html_body_text = tk.Text(main_frame, height=20, width=70, wrap='word', font=('Verdana', 10))
    html_body_text.grid(row=4, column=1, columnspan=2, pady=5, sticky="nsew")
    scrollbar = ttk.Scrollbar(main_frame, command=html_body_text.yview, orient=VERTICAL)
    html_body_text.config(yscrollcommand=scrollbar.set)
    scrollbar.grid(row=4, column=3, sticky='ns', pady=5)

    format_frame = ttk.Frame(main_frame)
    format_frame.grid(row=5, column=0, columnspan=3, pady=10)
    ttk.Button(format_frame, text="Félkövér", command=lambda: make_text_bold(html_body_text)).grid(row=0, column=0, padx=5)
    ttk.Button(format_frame, text="Táblázat beszúrása", command=lambda: insert_table(html_body_text)).grid(row=0, column=1, padx=5)

    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=6, column=0, columnspan=3, pady=10)

    ttk.Button(button_frame, text="Email-ek generálása", command=lambda: start_email_generation_thread(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)).grid(row=0, column=0, padx=5, pady=5)
    ttk.Button(button_frame, text="Generálás leállítása", command=email_generation.stop_email_generation).grid(row=0, column=1, padx=5, pady=5)
    ttk.Button(button_frame, text="E-mail-ek bezárása", command=email_generation.close_all_open_email_windows).grid(row=0, column=2, padx=5, pady=5)

    ttk.Button(button_frame, text="Beállítások mentése", command=lambda: settings.save_settings(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)).grid(row=1, column=0, padx=5, pady=5)
    ttk.Button(button_frame, text="Mentés másként", command=lambda: settings.save_settings_as(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)).grid(row=1, column=1, padx=5, pady=5)
    ttk.Button(button_frame, text="Beállítások betöltése", command=lambda: settings.apply_settings(settings.load_settings_gui(), table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)).grid(row=1, column=2, padx=5, pady=5)
    ttk.Button(button_frame, text="Alaphelyzetbe állítás", command=lambda: settings.reset_settings_to_default(table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)).grid(row=1, column=3, padx=5, pady=5)

    settings.apply_settings(settings.load_settings(), table_filename, attachment_dir, sheet_name_entry, subject_entry, html_body_text)

    root.mainloop()

def select_excel_file():
    filepath = filedialog.askopenfilename(title="Válassza ki a címzetteket tartalmazó Excel fájlt",
                                          filetypes=[("Excel files", "*.xlsx;*.xls")])
    if filepath:
        table_filename.set(filepath)

def select_attachment_dir():
    directory = filedialog.askdirectory(title="Válassza ki a mellékletek mappáját")
    if directory:
        attachment_dir.set(directory)

if __name__ == "__main__":
    create_gui()