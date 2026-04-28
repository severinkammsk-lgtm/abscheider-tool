import streamlit as st
import pandas as pd

st.set_page_config(page_title="Nenngrößenberechnung DIN 1999", layout="centered")

st.title("📋 Intelligente Bemessung (DIN 1999-100)")

# --- ABSCHNITT 1: ANLAGEN-KONFIGURATION ---
st.header("1. Anlagen-Konfiguration")
anlagentyp = st.selectbox("Anlagen-Zusammenstellung", ["S-II-P", "S-I-P", "S-II-I-P"], 
                          help="S=Schlammfang, I/II=Abscheiderklasse, P=Probenahmeschacht")

# --- ABSCHNITT 2: REGENABFLUSS (QR) ---
st.header("2. Regenabfluss (Qr)")
r_spende = st.number_input("Regenspende [l/(s * ha)]", value=300.0)

col_a, col_b = st.columns(2)
with col_a:
    a_tank = st.number_input("Tankfläche [m²]", value=0.0)
    a_hof = st.number_input("Hof-/ Freifläche [m²]", value=0.0)
    a_wasch = st.number_input("Waschplatz / Waschhalle [m²]", value=0.0)
with col_b:
    a_lager = st.number_input("Lager-/Abstellfläche [m²]", value=0.0)
    a_dach = st.number_input("Schrägdach [m²]", value=0.0)

qr = (r_spende * (a_tank + a_hof + a_wasch + a_lager + a_dach)) / 10000
st.subheader(f"Summe Qr = {qr:.2f} l/s")

st.divider()

# --- ABSCHNITT 3: SCHMUTZWASSER (QS) ---
st.header("3. Schmutzwasser (Qs)")

col1, col2 = st.columns(2)
with col1:
    dn15 = st.number_input("Ventil DN 15 (1/2\") [Stück]", value=0) * 0.5
    dn20 = st.number_input("Ventil DN 20 (3/4\") [Stück]", value=0) * 1.0
    dn25 = st.number_input("Ventil DN 25 (1\") [Stück]", value=0) * 1.7

with col2:
    portal_vorhanden = st.checkbox("Portalwaschanlage vorhanden")
    anzahl_hd = st.number_input("Anzahl HD-Reiniger", min_value=0, value=0)

# Qs Logik
qs_portal = 2.0 if portal_vorhanden else 0.0
if portal_vorhanden:
    qs_hd = anzahl_hd * 1.0
else:
    qs_hd = 2.0 + (anzahl_hd - 1) * 1.0 if anzahl_hd > 0 else 0.0

qs = dn15 + dn20 + dn25 + qs_portal + qs_hd
st.subheader(f"Summe Qs = {qs:.2f} l/s")

st.divider()

# --- ABSCHNITT 4: AUTOMATISCHE FAKTOREN ---
st.header("4. Faktoren (Auto-Modus)")

# 4.1 Erschwernisfaktor fx
# Regel: 2.0 wenn Waschplatz, Waschhalle, Portal oder HD vorhanden. Sonst 1.0.
wash_active = a_wasch > 0 or portal_vorhanden or anzahl_hd > 0
fx = 2.0 if wash_active else 1.0
st.write(f"**Erschwernisfaktor ($f_x$): {fx}** ({'Waschbetrieb erkannt' if fx==2.0 else 'Nur Tankbetrieb'})")

# 4.2 Dichtefaktor fd nach deiner Tabelle
dichte_bereich = st.selectbox("Dichte der Leichtflüssigkeit (g/cm³)", 
                              ["bis 0,85", "über 0,85 bis 0,90", "über 0,90 bis 0,95"])

fd_map = {
    "bis 0,85": {"S-II-P": 1.0, "S-I-P": 1.0, "S-II-I-P": 1.0},
    "über 0,85 bis 0,90": {"S-II-P": 2.0, "S-I-P": 1.5, "S-II-I-P": 1.0},
    "über 0,90 bis 0,95": {"S-II-P": 3.0, "S-I-P": 2.0, "S-II-I-P": 1.0}
}
fd = fd_map[dichte_bereich][anlagentyp]
st.write(f"**Dichtefaktor ($f_d$): {fd}** (für {anlagentyp})")

# 4.3 FAME-Faktor ff nach deiner Tabelle
fame_bereich = st.selectbox("FAME-Anteil (%)", 
                             ["bis 5 %", "über 5 % bis 10 %", "über 10 %"])

ff_map = {
    "bis 5 %": {"S-II-P": 1.25, "S-I-P": 1.0, "S-II-I-P": 1.0},
    "über 5 % bis 10 %": {"S-II-P": 1.50, "S-I-P": 1.25, "S-II-I-P": 1.0},
    "über 10 %": {"S-II-P": 1.75, "S-I-P": 1.50, "S-II-I-P": 1.25}
}
ff = ff_map[fame_bereich][anlagentyp]
st.write(f"**FAME-Faktor ($f_f$): {ff}** (für {anlagentyp})")

st.divider()

# --- ABSCHNITT 5: ERGEBNISSE ---
st.header("5. Gesamtergebnis")

ns_berechnet = (qr + fx * qs) * fd * ff
st.success(f"### Erforderliche Nenngröße (NS) = {ns_berechnet:.2f}")

# Schlammfang (Genaue Berechnung)
schlamm_wahl = st.radio("Schlammfang-Faktor", ["100x NS", "200x NS", "300x NS"], index=1)
f_sf = 100 if "100" in schlamm_wahl else 300 if "300" in schlamm_wahl else 200
v_sf = f_sf * ns_berechnet

st.metric("Schlammfangvolumen (V_SF)", f"{v_sf:.2f} Liter")
