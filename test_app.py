"""Validacao headless do app Streamlit (usada por `make test`).

Checa quatro coisas: o app constroi sem excecao, nenhuma figura falta (o app so
emite ``st.info`` quando o PNG nao existe), cada figura traz a sua tabela de
dados (um expander por figura) — a garantia de que o numero nao esta so na
imagem — e a aba final (M9) continua existindo, porque e ela que da o arco
completo em uma tela.
"""
import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

EXPECTED_CHARTS = 14
EXPECTED_TABS = ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "Discovery"]

at = AppTest.from_file("app.py", default_timeout=120)
at.run()

if at.exception:
    print("FAIL: exception while running app.py")
    for exception in at.exception:
        print(" ", exception.value)
    raise SystemExit(1)

labels = [tab.label for tab in at.tabs]
if labels != EXPECTED_TABS:
    print(f"FAIL: tabs are {labels}, expected {EXPECTED_TABS}")
    raise SystemExit(1)

missing = [element.value for element in at.info]
if missing:
    print("FAIL: the app could not find a figure:")
    for message in missing:
        print("  -", message)
    raise SystemExit(1)

tables = len(at.dataframe)
if tables != EXPECTED_CHARTS:
    print(f"FAIL: {tables} data tables for {EXPECTED_CHARTS} figures")
    raise SystemExit(1)

# every figure must have an accessible description to show as its caption
alt = json.loads((Path("data") / "chart_alttext.json").read_text(encoding="utf-8"))
empty = [name for name, text in alt.items() if not text.strip()]
if empty:
    print("FAIL: figures without alt text:", ", ".join(empty))
    raise SystemExit(1)

print(f"OK - {len(labels)} tabs, {EXPECTED_CHARTS} figures, {tables} data tables, "
      f"{len(alt)} alt texts")
