# SendEmailGUI3

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey)

Bulk email sender application for Microsoft Outlook — runs on both Windows and macOS.

> [Magyar verzió](README.hu.md)

## Inspiration

This project was inspired by [Sven-Bo/create-distribute-excel-files](https://github.com/Sven-Bo/create-distribute-excel-files) and the accompanying [YouTube tutorial](https://www.youtube.com/watch?v=RGR048I5ZDE).

## Download

Pre-built binaries are available on the [Releases page](../../releases).

| Platform | File |
|----------|------|
| macOS    | `SendEmailGUI3-mac.zip` → extract and move `SendEmailGUI3.app` to Applications |
| Windows  | `SendEmailGUI3.exe` → run directly, no installation needed |

## Features

- Reads recipients from an Excel file (name, email, CC, attachments)
- Sheet names auto-loaded from the selected Excel file (dropdown selector)
- WYSIWYG HTML editor:
  - Bold, italic, underline
  - Font family, font size (8–36 pt), font color
  - Paragraph alignment (left, center, right)
  - Embedded editable tables
- Menu bar with keyboard shortcuts (Cmd/Ctrl + S/O/B/I/U/Return)
- Hungarian and English UI (switchable from the menu)
- Settings saved automatically on close and restored on next launch
- Generation can be stopped mid-run

## Requirements

| Platform | Requirement |
|----------|-------------|
| Windows  | Microsoft Outlook installed |
| macOS    | Microsoft Outlook for Mac installed |

> When running from source, Python 3.x and `openpyxl` are also required (see [Installation](#installation--running)).

## Installation & Running

```bash
pip install openpyxl
# Windows only:
pip install pywin32

python3 main.py
```

## Usage

### 1. Prepare the Excel file

- The **first row is a header** and will be skipped
- Required columns:

| Column | Content |
|--------|---------|
| A | Attachment filename(s), semicolon-separated (e.g. `doc1.pdf;contract.docx`) |
| B | Recipient name |
| C | Recipient email address |
| D | CC email address (optional, can be empty) |

- All attachment files must be in the same folder

### 2. Enter data in the app

1. **Excel file** — browse or type the path; sheet names are loaded automatically into the dropdown
2. **Attachments folder** — the folder containing the files to attach
3. **Sheet name** — select from the dropdown
4. **Email subject** — free text

### 3. Edit the email body (WYSIWYG toolbar)

| Control | Function |
|---------|----------|
| Font dropdown | Verdana, Arial, Times New Roman, etc. |
| Size dropdown | 8–36 pt |
| **A** button | Font color picker |
| **B** / *I* / U | Bold / Italic / Underline |
| ← / ↔ / → | Left / Center / Right alignment |
| ⊞ Table | Insert an editable table |

### 4. Generate emails

- **▶ Generate emails** — Outlook opens a draft for each recipient; emails are **not sent automatically**, you review and send them manually in Outlook
- **⏹ Stop** — stops generation after the current row finishes
- **✕ Close windows** — closes all open Outlook draft windows at once

### 5. Keyboard shortcuts

| Action | Mac | Windows |
|--------|-----|---------|
| Save settings | Cmd+S | Ctrl+S |
| Open settings | Cmd+O | Ctrl+O |
| Start generation | Cmd+Return | Ctrl+Return |
| Bold | Cmd+B | Ctrl+B |
| Italic | Cmd+I | Ctrl+I |
| Underline | Cmd+U | Ctrl+U |

### 6. Managing settings

- Settings are **saved automatically on close** and restored on next launch
- **Save As** (File menu) — save the current configuration to a different JSON file (useful for managing multiple campaigns)
- **Open** (File menu) — load a previously saved configuration
- **Reset to Default** (File menu) — clear all fields
- **Language** (File menu) — switch between Magyar and English

## Excel file format (detailed)

The first row is a header (skipped during processing). Example:

| A | B | C | D |
|---|---|---|---|
| Attachments | Name | Email | CC |
| report.pdf;summary.xlsx | John Smith | john@example.com | manager@example.com |
| invoice.pdf | Jane Doe | jane@example.com | |

## File structure

```
main.py              # Entry point
gui.py               # UI and WYSIWYG editor
email_generation.py  # Email generation (Windows: COM, macOS: AppleScript)
settings.py          # Save/load settings
i18n.py              # Translations (Hungarian / English)
version.py           # Version number
```

## Build (standalone executable)

The build must be run on the target platform — cross-compilation is not possible.

### Prerequisites

**macOS / Linux**
```bash
pip install pyinstaller openpyxl
```

**Windows** (PowerShell)
```powershell
python -m venv buildenv
.\buildenv\Scripts\pip.exe install pyinstaller openpyxl pywin32
```

### Build

**macOS / Linux**
```bash
pyinstaller SendEmailGUI3.spec
```

**Windows** (PowerShell)
```powershell
.\buildenv\Scripts\pyinstaller.exe SendEmailGUI3.spec
```

### Output

| Platform | File |
|----------|------|
| Windows  | `dist\SendEmailGUI3.exe` |
| macOS    | `dist/SendEmailGUI3.app` |

The settings file (`settings.json`) is stored in the user data directory:
- **Windows**: `%APPDATA%\SendEmailGUI3\settings.json`
- **macOS**: `~/Library/Application Support/SendEmailGUI3/settings.json`
