import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io
import math
from geopy.geocoders import Nominatim

st.set_page_config(page_title="Ölabscheider-Bemessung", layout="centered")

def get_coords(address):
    try:
        geolocator = Nominatim(user_agent="abscheider_app_oil")
        location = geolocator.geocode(address)
        return (location.latitude, location.longitude) if location else (None, None)
    except: return (None, None)

def get_next_standard_ns(val):
    standards = [3, 6, 8, 10, 15, 20, 30, 40, 50, 65, 80, 100]
    for s in standards:
        if s >= val: return s
    return val

st.title("🛢️ Ölabscheidertool (DIN 1999-100)")

# Projektdaten
kunden_name = st.text_input("Name Kunde/Projekt")
kunden_strasse = st.text_input("Straße und Hausnummer")
kunden_ort = st.text_input("PLZ und Ort")

st.divider()

# 1. REGENABFLUSS
st.header("1. Regenabfluss (Qr)")
with st.expander("📍 KOSTRA-DWD Standortsuche"):
    if kunden_strasse and kunden_ort:
        lat, lon = get_coords(f"{kunden_strasse}, {kunden_ort}")
        if lat:
            st.success(f"Standort gefunden: {lat:.4f}, {lon:.4f}")
            st.markdown(f"[👉 KOSTRA-Karte öffnen](https://www.openko.de/maps/kostra_dwd_2020.html#15/{lat}/{lon})")

r_spende = st.number_input("Regenspende [l/(s * ha)]", value=300.0)

# Flächen
col_f1, col_f2 = st.columns(2)
with col_f1:
    l_hof = st.number_input("Länge Hof [m]", min_value=0.0)
    l_wasch = st.number_input("Länge Waschplatz [m]", min_value=0.0)
with col_f2:
    b_hof = st.number_input("Breite Hof [m]", min_value=0.0)
    b_wasch = st.number_input("Breite Waschplatz [m]", min_value=0.0)

a_grund = (l_hof * b_hof) + (l_wasch * b_wasch)

# Schlagregen-Logik
st.markdown("---")
st.subheader("Schlagregen (Dach/Wand)")
with st.expander("ℹ️ Warum Faktor 0,6?"):
    st.write("Bei Wind (30° Winkel) werden 60% der vertikalen Wandfläche als zusätzliche Regeneintragfläche gewertet.")

c1, c2 = st.columns(2)
with c1: l_wand = st.number_input("Lange Seite Wand [m]", min_value=0.0)
with c2: h_wand = st.number_input("Dachhöhe/Wandhöhe [m]", min_value=0.0)
a_schlag = l_wand * h_wand * 0.6

total_area = a_grund + a_schlag
qr = math.ceil(((r_spende * total_area) / 10000) * 100) / 100
st.info(f"Gesamtfläche: {total_area:.2f} m² | Qr = {qr:.2f} l/s")

st.divider()

# 2. SCHMUTZWASSER
st.header("2. Schmutzwasser (Qs)")
with st.expander("⚠️ Info: Ventildimension"):
    st.write("Messen Sie das Wandgewinde! 1/2\" (DN15) ist an der Wand oft 3/4\" am Schlauch.")

v15 = st.number_input("Anzahl Ventile 1/2\"", min_value=0)
v20 = st.number_input("Anzahl Ventile 3/4\"", min_value=0)
qs = (v15 * 0.5) + (v20 * 1.0)

# 3. ERGEBNIS
st.header("3. Nenngröße")
fd = st.selectbox("Dichtefaktor fd", [1.0, 1.5, 2.0])
ff = st.selectbox("FAME-Faktor ff", [1.0, 1.25, 1.5])
fx = 2.0 if a_wasch > 0 or qs > 0 else 1.0

ns_raw = (qr + fx * qs) * fd * ff
st.latex(rf"NS = (Q_r + f_x \cdot Q_s) \cdot f_d \cdot f_f = {ns_raw:.2f}")
st.success(f"### Erforderlich: NS {get_next_standard_ns(ns_raw)}")
