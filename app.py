import streamlit as st

st.set_page_config(page_title="Abscheider-Experte PRO", layout="centered")

st.title("📋 Willkommen beim Abscheider-Experten")
st.markdown("""
Dieses Tool unterstützt Sie bei der normgerechten Bemessung von Abscheideranlagen. 
Bitte wählen Sie in der **linken Seitenleiste** das gewünschte Fachmodul aus:

*   **Ölabscheidertool:** Bemessung nach **DIN 1999-100** (Regenwasser, Waschplätze, Werkstätten).
*   **Fettabscheidertool:** Bemessung nach **DIN 4040-100** (Gastronomie, Fleischverarbeitung).
""")

st.info("💡 Alle Berechnungen basieren auf den aktuell gültigen Normen und Sicherheitsfaktoren.")
