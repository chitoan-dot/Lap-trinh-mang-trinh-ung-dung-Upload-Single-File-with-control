BG = "#070014"

SIDEBAR = "#0d1020"

CARD = "#0f1024"
CARD2 = "#111827"

BORDER = "#26324a"

PRIMARY = "#a855f7"
PINK = "#ec4899"

TEXT = "#ffffff"
TEXT2 = "#94a3b8"

GREEN = "#00ff88"
RED = "#ff4d5a"

GRADIENT = """
qlineargradient(
    x1:0,y1:0,
    x2:1,y2:0,
    stop:0 #a855f7,
    stop:1 #ec4899
)
"""

APP_QSS = f"""
QWidget {{
    background:{BG};
    color:{TEXT};
    font-family:'Segoe UI';
}}

QFrame {{
    background:{CARD};
}}

QPushButton {{
    color:{TEXT};
}}

QLineEdit {{
    background:{CARD2};
    color:{TEXT};
    border:1px solid {BORDER};
    border-radius:12px;
    padding:8px;
}}

QComboBox {{
    background:{CARD2};
    color:{TEXT};
    border:1px solid {BORDER};
    border-radius:12px;
    padding:8px;
}}

QTableWidget {{
    background:{CARD};
    color:{TEXT};
    border:1px solid {BORDER};
}}
"""