import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io
import math
from geopy.geocoders import Nominatim

st.title("🛢️ Ölabscheidertool (DIN 1999-100)")

# Projektdaten
kunden_name = st.text_input("Name Kunde", placeholder="Vollständiger Name")
kunden_strasse = st.text_input("Straße und Hausnummer", placeholder="Musterstraße 1")
kunden_ort = st.text_input("PLZ und Ort", placeholder="12345 Musterstadt")

st.divider()

# 1. Regenabfluss
st.header("1. Regenabfluss (Qr)")
with st.expander("📍 KOSTRA-DWD Standortsuche"):
    if kunden_strasse and kunden_ort:
        try:
            geolocator = Nominatim(user_agent="abscheider_app_oil")
            loc = geolocator.geocode(f"{kunden_strasse}, {kunden_ort}")
            if loc:
                st.success(f"Koordinaten: {loc.latitude:.4f}, {loc.longitude:.4f}")
                st.markdown(f"[👉 KOSTRA-Karte öffnen](https://www.openko.de/maps/kostra_dwd_2020.html#15/{loc.latitude}/{loc.longitude})")
        except: st.error("Suche fehlgeschlagen.")

r_spende = st.number_input("Regenspende [l/(s * ha)]", value=300.0)
flaeche = st.number_input("Wirksame Fläche [m²]", min_value=0.0)
qr = math.ceil(((r_spende * flaeche) / 10000) * 100) / 100

# 2. Schmutzwasser
st.header("2. Schmutzwasser (Qs)")
with st.expander("⚠️ Richtige Ventildimension messen"):
    st.write("Messen Sie das Wandgewinde, nicht den Schlauchanschluss!")
v15 = st.number_input("Anzahl Ventile 1/2\" (DN 15)", min_value=0)
v20 = st.number_input("Anzahl Ventile 3/4\" (DN 20)", min_value=0)
v25 = st.number_input("Anzahl Ventile 1\" (DN 25)", min_value=0)
qs = (v15 * 0.5) + (v20 * 1.0) + (v25 * 1.7)

# 3. Nenngröße
st.header("3. Ergebnis")
fd = st.selectbox("Dichtefaktor fd", [1.0, 1.5, 2.0], help="Je nach Dichte der Leichtflüssigkeit")
ff = st.selectbox("FAME-Faktor ff", [1.0, 1.25, 1.5], help="Anteil Biodiesel")

ns_raw = (qr + 2.0 * qs) * fd * ff
st.latex(rf"NS = (Q_r + f_x \cdot Q_s) \cdot f_d \cdot f_f = {ns_raw:.2f}")
st.success(f"### Erforderliche Nenngröße: NS {math.ceil(ns_raw)}")
