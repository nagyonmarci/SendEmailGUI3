# SendEmailGUI3

Bulk email sender application for Microsoft Outlook — runs on both Windows and macOS.

> [Magyar verzió](README.hu.md)

## Inspiration

This project was inspired by [Sven-Bo/create-distribute-excel-files](https://github.com/Sven-Bo/create-distribute-excel-files) and the accompanying [YouTube tutorial](https://www.youtube.com/watch?v=RGR048I5ZDE).

## Features

- Reads recipients from an Excel file (name, email, CC, attachments)
- WYSIWYG HTML editor:
  - Bold, italic, underline
  - Font family, font size (8–36 pt), font color
  - Paragraph alignment (left, center, right)
  - Embedded editable tables
- Menu bar with keyboard shortcuts (Cmd/Ctrl + S/O/B/I/U/Return)
- Hungarian and English UI (switchable from the menu)
- Save/load settings to/from a JSON file
- Generation can be stopped mid-run

## Requirements

| Platform | Requirement |
|----------|-------------|
| Windows  | Python 3.x, Microsoft Outlook, `pywin32`, `openpyxl` |
| macOS    | Python 3.x, Microsoft Outlook for Mac, `openpyxl` |

## Installation

```bash
pip install openpyxl
# Windows only:
pip install pywin32
```

## Running

```bash
python3 main.py
```

## Excel file format

The first row is a header (skipped). The following columns are required:

| Column | Content |
|--------|---------|
| A | Attachment filename(s), semicolon-separated (e.g. `doc1.pdf;doc2.xlsx`) |
| B | Recipient name |
| C | Recipient email address |
| D | CC email address (optional) |

## Settings

On startup the app automatically loads `settings.json` if it exists. A different file can be opened or saved from the File menu.

## File structure

```
main.py              # Entry point
gui.py               # UI and WYSIWYG editor
email_generation.py  # Email generation (Windows: COM, macOS: AppleScript)
settings.py          # Save/load settings
i18n.py              # Translations (Hungarian / English)
```

## Build (standalone executable)

The build must be run on the target platform — cross-compilation is not possible.

### Prerequisites

```bash
pip install pyinstaller openpyxl
# Windows only:
pip install pywin32
```

### Build

```bash
pyinstaller SendEmailGUI3.spec
```

### Output

| Platform | File |
|----------|------|
| Windows  | `dist\SendEmailGUI3.exe` |
| macOS    | `dist/SendEmailGUI3.app` |

The settings file (`settings.json`) is stored in the user data directory:
- **Windows**: `%APPDATA%\SendEmailGUI3\settings.json`
- **macOS**: `~/Library/Application Support/SendEmailGUI3/settings.json`
