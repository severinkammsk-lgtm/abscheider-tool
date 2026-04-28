import streamlit as st
import pandas as pd

st.set_page_config(page_title="Nenngrößenberechnung DIN 1999", layout="centered")

st.title("📋 Nenngrößenberechnung (DIN 1999-100)")

# --- ABSCHNITT 1: REGENABFLUSS (QR) ---
st.header("1. Regenabfluss (Qr)")
r_spende = st.number_input("Festgelegte Regenspende [l/(s * ha)]", value=300.0, step=10.0)

areas = {
    "Tankfläche": st.number_input("Tankfläche [m²]", value=0.0),
    "Hof-/ Freifläche": st.number_input("Hof-/ Freifläche [m²]", value=0.0),
    "Waschplatz": st.number_input("Waschplatz [m²]", value=0.0),
    "Lager-/Abstellfläche": st.number_input("Lager-/Abstellfläche [m²]", value=0.0),
    "Schrägdach": st.number_input("Schrägdach (Dach) [m²]", value=0.0),
}

total_area = sum(areas.values())
qr = (r_spende * total_area) / 10000
st.subheader(f"Summe Qr = {qr:.2f} l/s")

st.divider()

# --- ABSCHNITT 2: SCHMUTZWASSER (QS) ---
st.header("2. Schmutzwasser (Qs)")

# Ventile
col1, col2 = st.columns(2)
with col1:
    dn15 = st.number_input("Ventil DN 15 (1/2\") [Stück]", value=0) * 0.5
    dn20 = st.number_input("Ventil DN 20 (3/4\") [Stück]", value=0) * 1.0
    dn25 = st.number_input("Ventil DN 25 (1\") [Stück]", value=0) * 1.7

# Neue Logik für Waschautomaten und HD-Reiniger
st.write("---")
portal_vorhanden = st.checkbox("Portalwaschanlage vorhanden?")
anzahl_hd = st.number_input("Anzahl HD-Reiniger", min_value=0, value=0, step=1)

qs_portal = 0.0
qs_hd = 0.0

if portal_vorhanden:
    qs_portal = 2.0
    # Wenn Portal vorhanden: jeder HD mit 1,0 l/s
    qs_hd = anzahl_hd * 1.0
else:
    # Wenn kein Portal: erster HD 2,0 l/s, jeder weitere 1,0 l/s
    if anzahl_hd > 0:
        qs_hd = 2.0 + (anzahl_hd - 1) * 1.0

qs = dn15 + dn20 + dn25 + qs_portal + qs_hd

st.info(f"Berechnung Qs: Portal ({qs_portal} l/s) + HD-Reiniger ({qs_hd} l/s) + Ventile")
st.subheader(f"Summe Qs = {qs:.2f} l/s")

st.divider()

# --- ABSCHNITT 3: FAKTOREN ---
st.header("3. Faktoren")
fx = st.selectbox("Erschwerungsfaktor (fx)", [1.0, 2.0], help="2.0 bei Waschstraßen/HD-Einsatz")
fd = st.selectbox("Dichtefaktor (fd)", [1.0, 1.5, 2.0], help="1.0 bis 0,85 g/cm³")

# FAME-Faktor fest auf 1.25 gesetzt bzw. als Vorgabe
ff = st.number_input("FAME-Faktor (ff)", value=1.25, step=0.01, help="Vorgabe: 1.25")

st.divider()

# --- ABSCHNITT 4: ERGEBNIS ---
st.header("4. Ergebnis Nenngröße (NS)")
ns_berechnet = (qr + fx * qs) * fd * ff

st.success(f"### Erforderliche Nenngröße (NS) = {ns_berechnet:.2f}")

# --- ABSCHNITT 5: SCHLAMMFANG ---
st.header("5. Schlammfang")
schlamm_wahl = st.radio("Schlammanfall", ["Gering (100*NS)", "Mittel (200*NS)", "Groß (300*NS)"], index=1)
f_sf = 100 if "Gering" in schlamm_wahl else 300 if "Groß" in schlamm_wahl else 200
v_min = f_sf * ns_berechnet

# Mindestvolumen-Logik
if ns_berechnet <= 3:
    v_min = max(v_min, 600)
else:
    v_min = max(v_min, 2500)

st.metric("Mindestschlammvolumen", f"{v_min:.0f} Liter")
