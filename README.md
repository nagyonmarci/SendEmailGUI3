# SendEmailGUI2

Tömeges emailküldő alkalmazás Microsoft Outlookhoz — Windows és macOS platformon egyaránt fut.

## Funkciók

- Excel-fájlból olvassa ki a címzetteket (név, email, CC, mellékletek)
- WYSIWYG HTML szerkesztő: félkövér, dőlt, aláhúzás, beágyazott szerkeszthető táblázatok
- Menüsor billentyűparancsokkal (Cmd/Ctrl + S/O/B/I/U/Return)
- Beállítások mentése/betöltése JSON fájlba
- Generálás folyamatban leállítható

## Rendszerkövetelmények

| Platform | Követelmény |
|----------|-------------|
| Windows  | Python 3.x, Microsoft Outlook, `pywin32`, `openpyxl` |
| macOS    | Python 3.x, Microsoft Outlook for Mac, `openpyxl` |

## Telepítés

```bash
pip install openpyxl
# Windows esetén:
pip install pywin32
```

## Indítás

```bash
python3 main.py
```

## Excel-fájl formátuma

Az első sor fejléc (nem kerül feldolgozásra). A következő oszlopok szükségesek:

| Oszlop | Tartalom |
|--------|----------|
| A | Melléklet fájlnév(ek), pontosvesszővel elválasztva (pl. `dok1.pdf;dok2.xlsx`) |
| B | Címzett neve |
| C | Címzett email-címe |
| D | CC email-cím (elhagyható) |

## Beállítások

Az alkalmazás indításkor automatikusan betölti a `settings.json` fájlt (ha létezik). A Fájl menüből más fájl is megnyitható vagy menthető.

## Fájlstruktúra

```
main.py              # Belépési pont
gui.py               # Felhasználói felület, WYSIWYG szerkesztő
email_generation.py  # Email-generálás (Windows: COM, macOS: AppleScript)
settings.py          # Beállítások mentése/betöltése
```
