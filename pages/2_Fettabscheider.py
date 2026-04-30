import streamlit as st
from datetime import datetime
from fpdf import FPDF
import math

st.title("🍳 Fettabscheidertool (DIN 4040-100)")

# Projektdaten
kunden_name = st.text_input("Name Projekt")
kunden_strasse = st.text_input("Straße / Hausnummer")
kunden_ort = st.text_input("PLZ / Ort")

st.divider()

# 1. Schmutzwasser
st.header("1. Schmutzwasser (Qs)")
wahl = st.selectbox("Grundlage:", ["Küchenbetrieb", "Fleischverarbeitung"])

if wahl == "Küchenbetrieb":
    s1 = st.number_input("Spülbecken DN 50 (0,8 l/s)", min_value=0)
    s2 = st.number_input("Großküchen-Spülmaschine (1,5 l/s)", min_value=0)
    qs = (s1 * 0.8 + s2 * 1.5) * 0.5
else:
    art = st.radio("Art:", ["Ohne Wurstherstellung", "Mit Wurstherstellung"])
    gve = st.number_input("Großvieheinheiten (GVE) pro Tag", min_value=0)
    faktor = 5.0 if "Ohne" in art else 7.0
    qs = (gve * faktor) / 8 / 3600

# 2. Faktoren & Ergebnis
st.header("2. Nenngröße")
ft = st.selectbox("Temperaturfaktor ft", [1.0, 1.3])
fe = st.selectbox("Erschwerungsfaktor fe", [1.0, 1.3])

ns_raw = qs * ft * 1.0 * fe
st.latex(rf"NS = Q_s \cdot f_t \cdot f_d \cdot f_e = {ns_raw:.2f}")

ns_standards = [1, 2, 4, 7, 10, 15, 20]
ns_final = next((s for s in ns_standards if s >= ns_raw), ns_raw)
st.success(f"### Gewählte Nenngröße: NS {ns_final}")

# Schlammfang
sf_faktor = 200 if wahl == "Fleischverarbeitung" else 100
st.info(f"Schlammfangvolumen: {ns_final * sf_faktor} Liter")
