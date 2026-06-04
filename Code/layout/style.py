from .theme import *

def widget_block(selector, rules):
    body = "\n".join(f"    {key}:{value};" for key, value in rules.items())
    return f"{selector} {{\n{body}\n}}"


PAGE_STYLE = widget_block("QWidget", {
    "background": BG,
    "color": TEXT,
})

CARD_STYLE = f"""
{widget_block("QFrame", {
    "background": CARD,
    "border": f"1px solid {BORDER}",
    "border-radius": "18px",
})}

QFrame:hover {{
    background:#171832;
    border:1px solid {PRIMARY};
}}
"""

INPUT_STYLE = widget_block("QLineEdit", {
    "background": CARD2,
    "border": f"1px solid {BORDER}",
    "border-radius": "12px",
    "padding": "10px",
    "color": TEXT,
})

BUTTON_STYLE = f"""
{widget_block("QPushButton", {
    "background": PRIMARY,
    "color": "white",
    "border": "none",
    "border-radius": "12px",
    "padding": "10px",
    "font-weight": "bold",
})}

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
    except Exception:
        pass
