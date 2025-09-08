A simple Tkinter desktop port of the Flask Profile cutter app.

How to run:

1. Make sure you have Python 3 installed (macOS usually has it). Prefer a virtualenv.

2. From the project folder run:

```bash
python3 desktop_app.py
```

Usage:
- Enter "Nowy profil" (default 6000 mm).
- Fill desired length/quantity pairs (up to 11 rows).
- Click "Tnij profile" to compute. Results appear in the text area.

Notes:
- The core algorithm was ported from `app.py` without functional changes.
- If you want a packaged macOS app, we can add pyinstaller instructions.
