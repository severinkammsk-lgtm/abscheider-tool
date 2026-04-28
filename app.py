import streamlit as st
import pandas as pd

st.set_page_config(page_title="Nenngrößenberechnung nach DIN 1999", layout="centered")

st.title("📋 Nenngrößenberechnung (DIN 1999-100)")
st.markdown("Basierend auf dem offiziellen Berechnungsblatt")

# --- ABSCHNITT 1: REGENABFLUSS ---
st.header("1. Regenabfluss (Qr)")
col1, col2 = st.columns(2)
with col1:
    r_spende = st.number_input("Festgelegte Regenspende [l/(s * ha)]", value=300.0, step=10.0)
with col2:
    st.info(f"Berechnung: Qr = r * A / 10.000")

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

# --- ABSCHNITT 2: SCHMUTZWASSER ---
st.header("2. Schmutzwasser (Qs)")
st.write("Auslaufventile / Waschanlagen")

col3, col4 = st.columns(2)
with col3:
    dn15 = st.number_input("Ventil DN 15 (1/2\") [Stück]", value=0) * 0.5
    dn20 = st.number_input("Ventil DN 20 (3/4\") [Stück]", value=0) * 1.0
    dn25 = st.number_input("Ventil DN 25 (1\") [Stück]", value=0) * 1.7
with col4:
    portal = st.number_input("Portalwaschanlage [l/s]", value=0.0)
    hd_reiniger = st.number_input("HD-Reiniger (Anzahl)", value=0) * 2.0 # Standardwert 2 l/s

qs = dn15 + dn20 + dn25 + portal + hd_reiniger
st.subheader(f"Summe Qs = {qs:.2f} l/s")

st.divider()

# --- ABSCHNITT 3: FAKTOREN ---
st.header("3. Faktoren")
col5, col6 = st.columns(2)

with col5:
    fx = st.selectbox("Erschwerungsfaktor (fx)", [1.0, 2.0], help="2.0 bei Waschstraßen/HD-Einsatz")
    
    dichte_klasse = st.selectbox("Dichtefaktor (fd)", ["bis 0,85 (fd=1)", "über 0,85 bis 0,90 (fd=1,5)", "über 0,90 (fd=2)"])
    fd = 1.0 if "bis 0,85" in dichte_klasse else 1.5 if "0,90" in dichte_klasse else 2.0

with col6:
    fame_klasse = st.selectbox("FAME-Anteil (ff)", ["bis 5% (ff=1)", "über 5% bis 10% (ff=1,2)", "über 10% (ff=1,5)"])
    ff = 1.0 if "bis 5%" in fame_klasse else 1.2 if "10%" in fame_klasse else 1.5

st.divider()

# --- ABSCHNITT 4: ERGEBNIS NENNGRÖSSE ---
st.header("4. Ergebnis Nenngröße (NS)")
ns_berechnet = (qr + fx * qs) * fd * ff

st.success(f"### Erforderliche Nenngröße (NS) = {ns_berechnet:.2f}")
st.write(f"Formel: NS = ({qr:.2f} + {fx} * {qs:.2f}) * {fd} * {ff}")

st.divider()

# --- ABSCHNITT 5: SCHLAMMFANG ---
st.header("5. Schlammfangprüfung")
schlamm_wahl = st.radio("Erwarteter Schlammanfall", ["Kein", "Gering (100 * NS)", "Mittel (200 * NS)", "Groß (300 * NS)", "Waschstraße (5000 l)"])

if "Gering" in schlamm_wahl: v_min = 100 * ns_berechnet
elif "Mittel" in schlamm_wahl: v_min = 200 * ns_berechnet
elif "Groß" in schlamm_wahl: v_min = 300 * ns_berechnet
elif "Waschstraße" in schlamm_wahl: v_min = 5000
else: v_min = 0

# Mindestvolumen-Regel nach Blatt 2
if ns_berechnet <= 3 and v_min > 0:
    v_min = max(v_min, 600)
elif ns_berechnet > 3 and v_min > 0:
    v_min = max(v_min, 2500)

st.metric("Mindestschlammvolumen", f"{v_min:.0f} Liter")

# --- ABSCHNITT 6: ÜBERHÖHUNG ---
st.header("6. Überprüfung Überhöhung")
h_max = st.number_input("Gemessene Überhöhung der Anlage [mm]", value=0)
h_soll = 0.2 * (1 - 0.85/1.0) * 1000 # Beispielrechnung in mm

if h_max > 0:
    if h_max >= h_soll:
        st.success(f"Überhöhung ausreichend (Soll: {h_soll:.0f} mm)")
    else:
        st.error(f"ACHTUNG: Überhöhung zu gering! (Soll: {h_soll:.0f} mm)")

# --- EXPORT ---
if st.button("Berechnung als CSV exportieren"):
    export_df = pd.DataFrame([{
        "Qr": qr, "Qs": qs, "NS_berechnet": ns_berechnet, "V_Schlamm": v_min, "Status_Überhöhung": h_max >= h_soll
    }])
    st.download_button("Download", export_df.to_csv(index=False), "Abscheider_Protokoll.csv")
