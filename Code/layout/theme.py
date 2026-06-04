PALETTE = {
    "bg": "#070014",
    "sidebar": "#0d1020",
    "card": "#0f1024",
    "card_2": "#111827",
    "border": "#26324a",
    "primary": "#a855f7",
    "pink": "#ec4899",
    "text": "#ffffff",
    "text_2": "#94a3b8",
    "green": "#00ff88",
    "red": "#ff4d5a",
}

BG = PALETTE["bg"]
SIDEBAR = PALETTE["sidebar"]
CARD = PALETTE["card"]
CARD2 = PALETTE["card_2"]
BORDER = PALETTE["border"]
PRIMARY = PALETTE["primary"]
PINK = PALETTE["pink"]
TEXT = PALETTE["text"]
TEXT2 = PALETTE["text_2"]
GREEN = PALETTE["green"]
RED = PALETTE["red"]

GRADIENT = """
qlineargradient(
    x1:0, y1:0,
    x2:1, y2:0,
    stop:0 #a855f7,
    stop:1 #ec4899
)
"""

FONT_FAMILY = "'Segoe UI'"

APP_QSS = f"""
QWidget {{
    background:{BG};
    color:{TEXT};
    font-family:{FONT_FAMILY};
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
