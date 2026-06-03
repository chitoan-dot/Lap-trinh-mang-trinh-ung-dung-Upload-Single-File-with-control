from .theme import *

PAGE_STYLE = f"""
QWidget {{
    background:{BG};
    color:{TEXT};
}}
"""

CARD_STYLE = f"""
QFrame {{
    background:{CARD};
    border:1px solid {BORDER};
    border-radius:18px;
}}

QFrame:hover {{
    background:#171832;
    border:1px solid {PRIMARY};
}}
"""

INPUT_STYLE = f"""
QLineEdit {{
    background:{CARD2};
    border:1px solid {BORDER};
    border-radius:12px;
    padding:10px;
    color:{TEXT};
}}
"""

BUTTON_STYLE = f"""
QPushButton {{
    background:{PRIMARY};
    color:white;
    border:none;
    border-radius:12px;
    padding:10px;
    font-weight:bold;
}}

QPushButton:hover {{
    background:{PINK};
}}

QPushButton:pressed {{
    background:#c026d3;
}}
"""

def apply_style(app):
    try:
        app.setStyleSheet(APP_QSS)
    except:
        pass
