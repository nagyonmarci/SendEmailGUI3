# SendEmailGUI3

[![Verzió](https://img.shields.io/badge/verzió-1.0.1-blue)](../../releases)
[![Licenc](https://img.shields.io/badge/licenc-Unlicense-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey)](#letöltés)
[![Security Scan](https://github.com/nagyonmarci/SendEmailGUI3/actions/workflows/security.yml/badge.svg)](https://github.com/nagyonmarci/SendEmailGUI3/actions/workflows/security.yml)
[![Release](https://github.com/nagyonmarci/SendEmailGUI3/actions/workflows/release.yml/badge.svg)](https://github.com/nagyonmarci/SendEmailGUI3/actions/workflows/release.yml)

Tömeges emailküldő alkalmazás Microsoft Outlookhoz — Windows és macOS platformon egyaránt fut.

> [English version](README.md)

## Inspiráció

Ez a projekt [Sven-Bo/create-distribute-excel-files](https://github.com/Sven-Bo/create-distribute-excel-files) repón és a kapcsolódó [YouTube-videón](https://www.youtube.com/watch?v=RGR048I5ZDE) alapul.

## Letöltés

Az előre lefordított futtatható fájlok elérhetők a [Releases oldalon](../../releases).

| Platform | Fájl |
|----------|------|
| macOS | `SendEmailGUI3-mac.zip` → lásd [macOS telepítés](#macos-telepítés) alább |
| Windows x64 | `SendEmailGUI3-win-x64.exe` → közvetlenül futtatható, telepítés nem szükséges |
| Windows ARM64 | `SendEmailGUI3-win-arm64.exe` → közvetlenül futtatható, telepítés nem szükséges |

## macOS telepítés

A macOS alapértelmezés szerint blokkolja az ismeretlen fejlesztőktől származó appokat. A mellékelt telepítőscript segítségével ez a korlátozás eltávolítható:

1. Csomagold ki a `SendEmailGUI3-mac.zip` fájlt
2. Nyiss **Terminal**t, és lépj be a kicsomagolt mappába:
   ```bash
   cd ~/Downloads/mac_release
   bash install.sh
   ```
   A script eltávolítja a karanténjelzőt, és opcionálisan az `/Applications` mappába helyezi az appot.

**Alternatíva (manuális):** Ha a scriptet nem szeretnéd használni, futtasd ezt a parancsot kicsomagolás után:
```bash
xattr -dr com.apple.quarantine SendEmailGUI3.app
```
Ezután a `SendEmailGUI3.app`-ot kézzel helyezd az `/Applications` mappába.

## Funkciók

- Excel-fájlból olvassa ki a címzetteket (név, email, CC, mellékletek)
- A munkalapok nevei automatikusan beolvasódnak a kiválasztott Excel-fájlból (legördülő lista)
- WYSIWYG HTML szerkesztő:
  - Félkövér, dőlt, aláhúzás
  - Betűtípus, betűméret (8–36 pt), betűszín
  - Bekezdés-igazítás (balra, középre, jobbra)
  - Beágyazott szerkeszthető táblázatok
- Menüsor billentyűparancsokkal (Cmd/Ctrl + S/O/B/I/U/Return)
- Magyar és angol felhasználói felület (menüből váltható)
- Bezáráskor automatikusan menti, újraindításkor visszaállítja a beállításokat
- Generálás folyamatban leállítható

## Rendszerkövetelmények

| Platform | Követelmény |
|----------|-------------|
| Windows  | Telepített Microsoft Outlook |
| macOS    | Telepített Microsoft Outlook for Mac |

> Forrásból való futtatáshoz Python 3.x és `openpyxl` is szükséges (lásd [Telepítés](#telepítés-és-indítás)).

## Telepítés és indítás

```bash
pip install openpyxl
# Windows esetén:
pip install pywin32

python3 main.py
```

## Használat

### 1. Az Excel-fájl előkészítése

- Az **első sor fejléc**, a program nem dolgozza fel
- Szükséges oszlopok:

| Oszlop | Tartalom |
|--------|----------|
| A | Melléklet fájlnév(ek), pontosvesszővel elválasztva (pl. `dok1.pdf;szerzodes.docx`) |
| B | Címzett neve |
| C | Címzett email-címe |
| D | CC email-cím (elhagyható, lehet üres) |

- Valamennyi mellékletfájlnak ugyanabban a mappában kell lennie

### 2. Adatok megadása az alkalmazásban

1. **Excel fájl** — tallózással vagy kézzel megadva; a munkalapok neve automatikusan betöltődik a legördülőbe
2. **Mellékletek mappája** — a csatolandó fájlok helye
3. **Munkalap neve** — legördülő listából választani
4. **Email tárgy** — szabad szöveg

### 3. Az email-törzs szerkesztése (WYSIWYG eszköztár)

| Elem | Funkció |
|------|---------|
| Betűtípus lenyíló | Verdana, Arial, Times New Roman, stb. |
| Betűméret lenyíló | 8–36 pt |
| **A** gomb | Betűszín kiválasztása |
| **B** / *I* / U | Félkövér / Dőlt / Aláhúzás |
| ← / ↔ / → | Balra / Középre / Jobbra igazítás |
| ⊞ Táblázat | Szerkeszthető táblázat beszúrása |

### 4. Emailek generálása

- **▶ Email-ek generálása** — az Outlook minden címzetthez megnyit egy vázlat-emailt; az emailek **nem kerülnek automatikusan elküldésre**, azokat Outlookban manuálisan kell elküldeni
- **⏹ Leállítás** — a generálás az aktuális sor után megáll
- **✕ Ablakok bezárása** — egyszerre bezárja az összes nyitott Outlook vázlatablakot

### 5. Billentyűparancsok

| Funkció | Mac | Windows |
|---------|-----|---------|
| Beállítások mentése | Cmd+S | Ctrl+S |
| Beállítások megnyitása | Cmd+O | Ctrl+O |
| Generálás indítása | Cmd+Return | Ctrl+Return |
| Félkövér | Cmd+B | Ctrl+B |
| Dőlt | Cmd+I | Ctrl+I |
| Aláhúzás | Cmd+U | Ctrl+U |

### 6. Beállítások kezelése

- Bezáráskor **automatikusan ment**, újraindításkor visszaállít
- **Mentés másként** (Fájl menü) — az aktuális konfiguráció mentése más JSON-fájlba (több kampány kezeléséhez hasznos)
- **Megnyitás** (Fájl menü) — korábban mentett konfiguráció betöltése
- **Alaphelyzetbe állítás** (Fájl menü) — minden mező törlése
- **Nyelv** (Fájl menü) — Magyar / English váltás

## Excel-fájl formátuma (részletesen)

Az első sor fejléc (nem kerül feldolgozásra). Példa:

| A | B | C | D |
|---|---|---|---|
| Mellékletek | Név | Email | CC |
| jelentes.pdf;osszefoglaló.xlsx | Kovács János | janos@pelda.hu | vezeto@pelda.hu |
| szamla.pdf | Nagy Éva | eva@pelda.hu | |

## Fájlstruktúra

```
main.py              # Belépési pont
gui.py               # Felhasználói felület, WYSIWYG szerkesztő
email_generation.py  # Email-generálás (Windows: COM, macOS: AppleScript)
settings.py          # Beállítások mentése/betöltése
i18n.py              # Fordítások (magyar / angol)
version.py           # Verziószám
```

## Build (önálló futtatható program)

A build az adott platformon futtatandó — cross-compile nem lehetséges.

### Előfeltételek

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

**macOS**
```bash
pyinstaller SendEmailGUI3.spec
```

**Windows x64** (PowerShell)
```powershell
.\buildenv\Scripts\pyinstaller.exe SendEmailGUI3-win-x64.spec
```

**Windows ARM64** (PowerShell)
```powershell
.\buildenv\Scripts\pyinstaller.exe SendEmailGUI3-win-arm64.spec
```

### Kimenet

| Platform | Fájl |
|----------|------|
| macOS         | `dist/SendEmailGUI3.app` |
| Windows x64   | `dist\SendEmailGUI3-win-x64.exe` |
| Windows ARM64 | `dist\SendEmailGUI3-win-arm64.exe` |

A beállítások fájlja (`settings.json`) az apphoz tartozó felhasználói mappában jön létre:
- **Windows**: `%APPDATA%\SendEmailGUI3\settings.json`
- **macOS**: `~/Library/Application Support/SendEmailGUI3/settings.json`

## CI/CD Pipeline

A projekt két GitHub Actions workflow-val automatizálja a biztonsági ellenőrzéseket és a keresztplatformos kiadásokat.

### Security Scan ([`security.yml`](.github/workflows/security.yml))

Minden push és pull request esetén lefut, bármely branch-en.

| Lépés | Eszköz | Mit ellenőriz |
|-------|--------|---------------|
| CVE-audit | `pip-audit` | Ismert sebezhetőségek a Python-függőségekben |
| SAST-scan | `bandit` (medium+ súlyosság) | Biztonsági problémák a forráskódban |

### Release Pipeline ([`release.yml`](.github/workflows/release.yml))

Verziótag pusholásával indul el (pl. `git tag v1.0.2 && git push --tags`).

```
tag push (v*)
      │
      ▼
┌─────────────────────────┐
│     Security gate       │  ubuntu-latest
│  • tag == VERSION fájl  │
│  • pip-audit            │
│  • bandit               │
└────────────┬────────────┘
             │ needs: security
   ┌─────────┼──────────────┐
   ▼         ▼              ▼
macOS      Win x64       Win ARM64
build       build          build
   └─────────┼──────────────┘
             │ needs: all builds
             ▼
     ┌────────────────┐
     │ GitHub Release │  ubuntu-latest
     │  (3 artifact)  │
     └────────────────┘
```

Minden build-job natívan fut a saját célplatformján:

| Job | Runner | Artifact |
|-----|--------|----------|
| macOS build | `macos-latest` | `SendEmailGUI3-mac.zip` (`.app` + telepítőscript) |
| Windows x64 build | `windows-latest` | `SendEmailGUI3-win-x64.exe` |
| Windows ARM64 build | `windows-11-arm` | `SendEmailGUI3-win-arm64.exe` |

Mindhárom artifact automatikusan csatolódik a GitHub Release-hez.
