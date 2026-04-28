import streamlit as st
import pandas as pd

# 1. Seiteneinstellungen
st.set_page_config(page_title="Abscheider-Bemessung PRO", layout="centered")

# 2. CSS-BLOCK: Buttons entfernen & Mobile-Optimierung
# Dieser Block sorgt dafür, dass nur das Eingabefeld ohne Pfeile erscheint.
st.markdown("""
    <style>
    /* Chrome, Safari, Edge, Opera */
    input::-webkit-outer-spin-button,
    input[::-webkit-inner-spin-button] {
        -webkit-appearance: none;
        margin: 0;
    }
    /* Firefox */
    input[type=number] {
        -moz-appearance: textfield;
    }
    /* Optimierung für mobile Tastatur und Zentrierung */
    .stNumberInput div div input {
        text-align: center;
        font-size: 18px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- KUNDENDATEN ---
st.title("📋 Abscheider-Bemessung (DIN 1999-100)")
st.subheader("Projektdaten")
col_k1, col_k2 = st.columns(2)
with col_k1:
    kunden_name = st.text_input("Bauvorhaben / Kunde", placeholder="Name")
with col_k2:
    kunden_adresse = st.text_input("Standort / Adresse", placeholder="Ort")

st.divider()

# --- 1. REGENABFLUSS (QR) ---
st.header("1. Regenabfluss (Qr)")
st.caption("Flächenmaße direkt per Tastatur eingeben.")

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
st.info(f"Gesamtfläche: {total_area:.2f} m² | **Qr = {qr:.2f} l/s**")

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

# Logik Qs
qs_portal = 2.0 if portal else 0.0
if portal:
    qs_hd = anz_hd * 1.0
else:
    qs_hd = 2.0 + (anz_hd - 1) * 1.0 if anz_hd > 0 else 0.0

qs = dn15 + dn20 + dn25 + qs_portal + qs_hd
st.info(f"**Gesamt Qs = {qs:.2f} l/s**")

st.divider()

# --- 3. FAKTOREN AUTOMATIK ---
st.header("3. Faktoren & Anlagentyp")
anlagentyp = st.selectbox("Anlagentyp", ["S-II-P", "S-I-P", "S-II-I-P"])
fx = 2.0 if (a_wasch > 0 or portal or anz_hd > 0) else 1.0

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

st.divider()

# --- 4. ERGEBNISSE ---
st.header("4. Berechnungsergebnis")
ns = (qr + fx * qs) * fd * ff

# Anzeige der Rechenformeln
st.latex(rf"NS = (Q_r + f_x \cdot Q_s) \cdot f_d \cdot f_f")
st.latex(rf"NS = ({qr:.2f} + {fx} \cdot {qs:.2f}) \cdot {fd} \cdot {ff} = {ns:.2f}")

st.success(f"### Erforderliche Nenngröße: NS {ns:.2f}")

f_sf = st.radio("Schlammfangfaktor", [100, 200, 300], index=1, horizontal=True)
v_sf = f_sf * ns
st.metric("Schlammfangvolumen (V_SF)", f"{v_sf:.2f} Liter")

# Export
if st.button("Ergebnis als CSV speichern"):
    df_export = pd.DataFrame([{
        "Bauvorhaben": kunden_name, 
        "NS": round(ns, 2), 
        "V_SF": round(v_sf, 2),
        "fx": fx, "fd": fd, "ff": ff
    }])
    st.download_button("Download CSV", df_export.to_csv(index=False), f"Bemessung_{kunden_name}.csv")
