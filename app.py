import streamlit as st
import pandas as pd

# 1. Grundkonfiguration
st.set_page_config(page_title="Abscheider-Bemessung PRO", layout="centered")

# 2. CSS-HACK: ENTFERNT + UND - BUTTONS UND OPTIMIERT MOBILE EINGABE
st.markdown("""
    <style>
    /* Entfernt die Pfeile (Spin-Buttons) in allen Browsern */
    input::-webkit-outer-spin-button,
    input[::-webkit-inner-spin-button] {
        -webkit-appearance: none;
        margin: 0;
    }
    input[type=number] {
        -moz-appearance: textfield;
    }
    /* Macht die Eingabefelder auf dem Handy besser lesbar */
    .stNumberInput div div input {
        text-align: center;
        font-size: 18px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- PROJEKTDATEN ---
st.title("📋 Abscheider-Bemessung (DIN 1999-100)")
col_p1, col_p2 = st.columns(2)
with col_p1:
    kunden_name = st.text_input("Bauvorhaben / Kunde", placeholder="Name")
with col_p2:
    kunden_adresse = st.text_input("Standort / Adresse", placeholder="Ort")

st.divider()

# --- 1. REGENABFLUSS (QR) ---
st.header("1. Regenabfluss (Qr)")
st.caption("Nur unüberdachte Flächen angeben. Eingabe direkt per Tastatur.")

r_spende = st.number_input("Regenspende [l/(s * ha)]", value=300.0, format="%.1f")

def flaeche_zeile(label, key_suffix, wind_faktor=1.0):
    st.markdown(f"**{label}**")
    c1, c2, c3 = st.columns([3, 3, 2])
    with c1:
        l = st.number_input("Länge [m]", key=f"l_{key_suffix}", min_value=0.0, format="%.2f", step=0.0)
    with c2:
        b = st.number_input("Breite [m]", key=f"b_{key_suffix}", min_value=0.0, format="%.2f", step=0.0)
    ergebnis = l * b * wind_faktor
    with c3:
        st.markdown(f"<div style='padding-top:35px'>= <b>{ergebnis:.2f} m²</b></div>", unsafe_allow_html=True)
    return ergebnis

a_tank = flaeche_zeile("Tankfläche", "tank")
a_hof = flaeche_zeile("Hof- / Freifläche", "hof")
a_wasch = flaeche_zeile("Waschplatz (außen)", "wasch")
a_lager = flaeche_zeile("Lager- / Abstellfläche", "lager")
a_wand = flaeche_zeile("Wandfläche (Schlagregen 50%)", "wand", wind_faktor=0.5)

total_area = a_tank + a_hof + a_wasch + a_lager + a_wand
qr = (r_spende * total_area) / 10000
st.info(f"**Gesamt Qr = {qr:.2f} l/s**")

st.divider()

# --- 2. SCHMUTZWASSER (QS) ---
st.header("2. Schmutzwasser (Qs)")
col_s1, col_s2 = st.columns(2)
with col_s1:
    dn15 = st.number_input("Ventil DN 15 (0,5 l/s)", min_value=0, step=0) * 0.5
    dn20 = st.number_input("Ventil DN 20 (1,0 l/s)", min_value=0, step=0) * 1.0
    dn25 = st.number_input("Ventil DN 25 (1,7 l/s)", min_value=0, step=0) * 1.7
with col_s2:
    portal = st.checkbox("Portalwaschanlage")
    anz_hd = st.number_input("Anzahl HD-Reiniger", min_value=0, step=0)

# Logik Schmutzwasser
qs_portal = 2.0 if portal else 0.0
if portal:
    qs_hd = anz_hd * 1.0
else:
    qs_hd = 2.0 + (anz_hd - 1) * 1.0 if anz_hd > 0 else 0.0

qs = dn15 + dn20 + dn25 + qs_portal + qs_hd
