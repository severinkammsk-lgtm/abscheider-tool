import streamlit as st
import pandas as pd

# Grundkonfiguration
st.set_page_config(page_title="Abscheider-Bemessung PRO", layout="centered")

# --- CSS-HACK: KEINE BUTTONS & MOBILE OPTIMIERUNG ---
st.markdown("""
    <style>
    input[::-webkit-outer-spin-button],
    input[::-webkit-inner-spin-button] { -webkit-appearance: none; margin: 0; }
    input[type=number] { -moz-appearance: textfield; }
    .stNumberInput div div input { text-align: center; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- PROJEKTDATEN ---
st.title("📋 Abscheider-Bemessung (DIN 1999-100)")
col_k1, col_k2 = st.columns(2)
with col_k1:
    kunden_name = st.text_input("Bauvorhaben / Kunde")
with col_k2:
    kunden_adresse = st.text_input("Standort / Adresse")

st.divider()

# --- 1. REGENABFLUSS ---
st.header("1. Regenabfluss (Qr)")
r_spende = st.number_input("Regenspende [l/(s * ha)]", value=300.0, format="%.1f")

def flaeche_zeile(label, key_suffix, wind_faktor=1.0):
    st.markdown(f"**{label}**")
    c1, c2, c3 = st.columns([3, 3, 2])
    with c1: l = st.number_input("Länge [m]", key=f"l_{key_suffix}", min_value=0.0, format="%.2f")
    with c2: b = st.number_input("Breite [m]", key=f"b_{key_suffix}", min_value=0.0, format="%.2f")
    ergebnis = l * b * wind_faktor
    with c3: st.markdown(f"<div style='padding-top:35px'>= <b>{ergebnis:.2f} m²</b></div>", unsafe_allow_html=True)
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

# --- 2. SCHMUTZWASSER ---
st.header("2. Schmutzwasser (Qs)")
col_s1, col_s2 = st.columns(2)
with col_s1:
    dn15 = st.number_input("Ventil DN 15 (0,5 l/s)", min_value=0) * 0.5
    dn20 = st.number_input("Ventil DN 20 (1,0 l/s)", min_value=0) * 1.0
    dn25 = st.number_input("Ventil DN 25 (1,7 l/s)", min_value=0) * 1.7
with col_s2:
    portal = st.checkbox("Portalwaschanlage")
    anz_hd = st.number_input("Anzahl HD-Reiniger", min_value=0)

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

# --- 4. ERGEBNISSE & FORMELN ---
st.header("4. Berechnungsergebnis")
ns = (qr + fx * qs) * fd * ff
st.latex(rf"NS = ({qr:.2f} + {fx} \cdot {qs:.2f}) \cdot {fd} \cdot {ff} = {ns:.2f}")
st.success(f"### Erforderliche Nenngröße: NS {ns:.2f}")

f_sf = st.radio("Schlammfangfaktor", [100, 200, 300], index=1, horizontal=True)
v_sf = f_sf * ns
st.metric("Schlammfangvolumen (V_SF)", f"{v_sf:.2f} Liter")

st.divider()

# --- 5. ÜBERHÖHUNG ---
st.header("5. Überprüfung Überhöhung")
h_ist = st.number_input("Vorhandene Überhöhung [mm]", min_value=0)
# Norm-Formel für Mindestüberhöhung (Beispielhaft für 0.85 Dichte)
h_soll = 0.2 * (1 - 0.85/1.0) * 1000 

if h_ist > 0:
    if h_ist >= h_soll:
        st.success(f"Überhöhung ausreichend (Soll: >{h_soll:.0f} mm)")
    else:
        st.error(f"Warnung: Überhöhung zu gering! (Soll: >{h_soll:.0f} mm)")

# --- EXPORT ---
if st.button("Protokoll-CSV erstellen"):
    df = pd.DataFrame([{"Projekt": kunden_name, "NS": ns, "V_SF": v_sf, "Faktoren": f"fx={fx}, fd={fd}, ff={ff}"}])
    st.import streamlit as st
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
