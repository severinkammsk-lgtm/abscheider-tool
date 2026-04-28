import streamlit as st
import pandas as pd

# Grundkonfiguration
st.set_page_config(page_title="Abscheider-Bemessung PRO", layout="centered")

# --- CSS-HACK: ENTFERNT + UND - BUTTONS ---
st.markdown("""
    <style>
    /* Entfernt die Pfeile/Buttons in Chrome, Safari, Edge, Opera */
    input[::-webkit-outer-spin-button],
    input[::-webkit-inner-spin-button] {
        -webkit-appearance: none;
        margin: 0;
    }
    /* Entfernt die Pfeile in Firefox */
    input[type=number] {
        -moz-appearance: textfield;
    }
    /* Zentriert die Zahlen in den Feldern für bessere Optik am Handy */
    .stNumberInput div div input {
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- KUNDENDATEN ---
st.title("📋 Abscheider-Bemessung (DIN 1999-100)")
st.subheader("Projektdaten")
col_k1, col_k2 = st.columns(2)
with col_k1:
    kunden_name = st.text_input("Name des Kunden / Bauvorhaben", placeholder="z. B. Spedition Müller")
with col_k2:
    kunden_adresse = st.text_input("Adresse / Standort", placeholder="Musterstraße 1, 12345 Stadt")

st.divider()

# --- ABSCHNITT 1: REGENABFLUSS (QR) ---
st.header("1. Regenabfluss (Qr)")
st.caption("Hinweis: Nur unüberdachte Flächen angeben.")

r_spende = st.number_input("Regenspende [l/(s * ha)]", value=300.0, format="%.1f")

# Funktion für LxB Eingabe ohne Buttons
def flaeche_zeile(label, key_suffix, wind_faktor=1.0):
    st.markdown(f"**{label}**")
    c1, c2, c3 = st.columns([3, 3, 2])
    with c1:
        # step=None oder step=0.0 hilft zusätzlich beim Ausblenden der Buttons
        l = st.number_input("Länge [m]", key=f"l_{key_suffix}", min_value=0.0, format="%.2f", step=0.01)
    with c2:
        b = st.number_input("Breite [m]", key=f"b_{key_suffix}", min_value=0.0, format="%.2f", step=0.01)
    ergebnis = l * b * wind_faktor
    with c3:
        st.markdown(f"<div style='padding-top:35px'>= <b>{ergebnis:.2f} m²</b></div>", unsafe_allow_html=True)
    return ergebnis

a_tank = flaeche_zeile("Tankfläche", "tank")
a_hof = flaeche_zeile("Hof- / Freifläche", "hof")
a_wasch = flaeche_zeile("Waschplatz (außen)", "wasch")
a_lager = flaeche_zeile("Lager- / Abstellfläche", "lager")

st.write("---")
st.write("**Schlagregen-Berücksichtigung (Wind)**")
a_wand = flaeche_zeile("Wandfläche (Anrechnung 50%)", "wand", wind_faktor=0.5)

total_area = a_tank + a_hof + a_wasch + a_lager + a_wand
qr = (r_spende * total_area) / 10000
