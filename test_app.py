"""Validacao headless do app Streamlit (usada por `just test`)."""
from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app.py", default_timeout=60)
at.run()
if at.exception:
    print("FAIL:", at.exception)
    raise SystemExit(1)
print("OK")
