import streamlit as st
import pandas as pd

st.set_page_config(page_title="Abscheider-Bemessung PRO", layout="centered")

# CSS-Hack, um die +/- Buttons (Spin-Buttons) bei allen Zahlenfeldern zu verstecken
st.markdown("""
    <style>
    /* Versteckt die Pfeile bei Chrome, Safari, Edge, Opera */
    input[::-webkit-outer-spin-button],
    input[::-webkit-inner-spin-button] {
        -webkit-appearance: none;
        margin: 0;
    }
    /* Versteckt die Pfeile bei Firefox */
    input[type=number] {
        -moz-appearance: textfield;
    }
    </style>
""", unsafe_allow_html=True)

# --- KUNDENDATEN ---
st.title("📋 Abscheider-Bemessung (DIN 1999-100)")
st.subheader("Projektdaten")
kunden_name = st.text_input("Name des Kunden / Bauvorhaben")
kunden_adresse = st.text_input("Adresse / Standort")

st.divider()

# --- ABSCHNITT 1: REGENABFLUSS (QR) ---
st.header("1. Regenabfluss (Qr)")
st.caption("Geben Sie nur unüberdachte Flächen an.")

# format="%.1f" sorgt für die Darstellung, step=None entfernt oft die Buttons in modernen Browsern zusätzlich
r_spende = st.number_input("Regenspende [l/(s * ha)]", value=300.0, format="%.1f")

def flaeche_zeile(label, wind_faktor=1.0):
    st.markdown(f"**{label}**")
    c1, c2, c3 = st.columns([3, 3, 2])
    with c1:
        # Durch den CSS-Hack oben sind die Buttons nun weg
        l = st.number_input("Länge [m]", key=f"l_{label}", min_value=0.0, format="%.2f")
    with c2:
        b = st.number_input("Breite [m]", key=f"b_{label}", min_value=0.0, format="%.2f")
    ergebnis = l * b * wind_faktor
    with c3:
        st.markdown(f"<div style='padding-top:35px'>= <b>{ergebnis:.2f} m²</b></div>", unsafe_allow_html=True)
    return ergebnis

a_tank = flaeche_zeile("Tankfläche")
a_hof = flaeche_zeile("Hof- / Freifläche")
a_wasch = flaeche_zeile("Waschplatz / Waschhalle (außen)")
a_lager = flaeche_zeile("Lager- / Abstellfläche")

st.write("---")
st.write("**Schlagregen-Berücksichtigung**")
a_wand = flaeche_zeile("Wandfläche (vertikal)", wind_faktor=0.5)

total_area = a_tank + a_hof + a_wasch + a_lager + a_wand
qr = (r_spende * total_area) / 10000
st.info(f"Gesamtfläche: {total_area:.2f} m² | **Qr = {qr:.2f} l/s**")

st.divider()

# --- ABSCHNITT 2: SCHMUTZWASSER (QS) ---
st.header("2. Schmutzwasser (Qs)")
col1, col2 = st.columns(2)
with col1:
    dn15 = st.number_input("Ventil DN 15 (1/2\") [Anzahl]", min_value=0) * 0.5
    dn20 = st.number_input("Ventil DN 20 (3/4\") [Anzahl]", min_value=0) * 1.0
    dn25 = st.number_input("Ventil DN 25 (1\") [Anzahl]", min_value=0) * 1.7
with col2:
    portal = st.checkbox("Portalwaschanlage vorhanden")
    anz_hd = st.number_input("Anzahl HD-Reiniger", min_value=0)

qs_portal = 2.0 if portal else 0.0
if portal:
    qs_hd = anz_hd * 1.0
else:
    qs_hd = 2.0 + (anz_hd - 1) * 1.0 if anz_hd > 0 else 0.0

qs = dn15 + dn20 + dn25 + qs_portal + qs_hd
st.info(f"**Qs = {qs:.2f} l/s**")

st.divider()

# --- ABSCHNITT 3: AUTOMATISCHE FAKTOREN ---
st.header("3. Faktoren & Anlage")
anlagentyp = st.selectbox("Anlagentyp", ["S-II-P", "S-I-P", "S-II-I-P"])

# Auto-fx Logik
wash_active = a_wasch > 0 or portal or anz_hd > 0
fx = 2.0 if wash_active else 1.0

dichte = st.selectbox("Dichte (g/cm³)", ["bis 0,85", "0,85 - 0,90", "0,90 - 0,95"])
fd_map = {"bis 0,85": {"S-II-P": 1.0, "S-I-P": 1.0, "S-II-I-P": 1.0},
          "0,85 - 0,90": {"S-II-P": 2.0, "S-I-P": 1.5, "S-II-I-P": 1.0},
          "0,90 - 0,95": {"S-II-P": 3.0, "S-I-P": 2.0, "S-II-I-P": 1.0}}
fd = fd_map[dichte][anlagentyp]

fame = st.selectbox("FAME-Anteil (%)", ["bis 5 %", "5 - 10 %", "über 10 %"])
ff_map = {"bis 5 %": {"S-II-P": 1.25, "S-I-P": 1.0, "S-II-I-P": 1.0},
          "5 - 10 %": {"S-II-P": 1.50, "S-I-P": 1.25, "S-II-I-P": 1.0},
          "über 10 %": {"S-II-P": 1.75, "S-I-P": 1.50, "S-II-I-P": 1.25}}
ff = ff_map[fame][anlagentyp]

st.write(f"**Faktoren:** fx={fx} | fd={fd} | ff={ff}")

st.divider()

# --- ABSCHNITT 4: ERGEBNIS ---
st.header("4. Ergebnis")
ns = (qr + fx * qs) * fd * ff
st.success(f"
