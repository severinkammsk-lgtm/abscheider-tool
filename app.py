import streamlit as st
import pandas as pd

# 1. Grundkonfiguration
st.set_page_config(page_title="Abscheider-Bemessung PRO", layout="centered")

# 2. CSS: Entfernt die + / - Buttons und optimiert die Eingabe (KEINE Buttons mehr!)
st.markdown("""
    <style>
    /* Versteckt die Pfeile in Chrome, Safari, Edge, Opera */
    input[::-webkit-outer-spin-button],
    input[::-webkit-inner-spin-button] {
        -webkit-appearance: none !important;
        margin: 0 !important;
    }
    /* Versteckt die Pfeile in Firefox */
    input[type=number] {
        -moz-appearance: textfield !important;
    }
    /* Zentriert den Text und vergrößert die Schrift für Handys */
    .stNumberInput div div input {
        text-align: center !important;
        font-size: 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- PROJEKTDATEN ---
st.title("📋 Abscheider-Bemessung (DIN 1999-100)")
col_k1, col_k2 = st.columns(2)
with col_k1:
    kunden_name = st.text_input("Bauvorhaben / Kunde", placeholder="Name")
with col_k2:
    kunden_adresse = st.text_input("Standort", placeholder="Ort")

st.divider()

# --- 1. REGENABFLUSS ---
st.header("1. Regenabfluss (Qr)")
st.warning("Hinweis: Nur unüberdachte Flächen angeben, auf die Regen fallen kann!")

r_spende = st.number_input("Regenspende [l/(s * ha)]", value=300.0, format="%.1f")

def flaeche_zeile(label, key_suffix, wind_faktor=1.0):
    st.markdown(f"**{label}**")
    c1, c2, c3 = st.columns([3, 3, 2])
    with c1:
        l = st.number_input("Länge [m]", key=f"l_{key_
