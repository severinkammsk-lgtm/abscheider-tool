import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io

# 1. Seiteneinstellungen
st.set_page_config(page_title="Abscheider-Bemessung PRO", layout="centered")

# 2. CSS: Entfernt Buttons & optimiert mobile Ansicht
st.markdown("""
    <style>
    input::-webkit-outer-spin-button,
    input[::-webkit-inner-spin-button] { -webkit-appearance: none !important; margin: 0 !important; }
    input[type=number] { -moz-appearance: textfield !important; }
    .stNumberInput div div input { text-align: center !important; font-size: 20px !important; }
    </style>
""", unsafe_allow_html=True)

# Hilfsfunktion für die Ventilberechnung nach Tabelle 1
def get_valve_flows_detailed(v15, v20, v25):
    valves = []
    for _ in range(v25): valves.append(25)
    for _ in range(v20): valves.append(20)
    for _ in range(v15): valves.append(15)
    
    table = {
        15: [0.5, 0.5, 0.35, 0.25, 0.1],
        20: [1.0, 1.0, 0.7, 0.5, 0.2],
        25: [1.7, 1.7, 1.2, 0.85, 0.3]
    }
    
    results = []
    total_flow = 0.0
    for idx, size in enumerate(valves):
        pos = idx if idx < 4 else 4
        flow = table[size][pos]
        results.append({"DN": size, "Pos": idx + 1, "Flow": flow})
        total_flow += flow
    return results, total_flow

# --- PROJEKTDATEN ---
st.title("📋 Abscheider-Bemessung (DIN 1999-100)")
kunden_name = st.text_input("Name Kunde", placeholder="Vollständiger Name des Kunden")
col_adr1, col_adr2 = st.columns(2)
with col_adr1:
    kunden_strasse = st.text_input("Straße, Hausnummer", placeholder="Musterstraße 123")
with col_adr2:
    kunden_ort = st.text_input("Postleitzahl, Ort", placeholder="12345 Musterstadt")

st.divider()

# --- 1. REGENABFLUSS ---
st.header("1. Regenabfluss ($Q_r$)")
r_spende = st.number_input("Regenspende [l/(s * ha)]", value=300.0, format="%.1f")

def flaeche_zeile_full(label, key_suffix, wind_faktor=1.0):
    st.markdown(f"**{label}**")
    c1, c2, c3 = st.columns([3, 3, 2])
    with c1:
        l = st.number_input("Länge [m]", key=f"l_{key_suffix}", min_value=0.0, format="%.2f")
    with c2:
        b = st.number_input("Breite [m]", key=f"b_{key_suffix}", min_value=0.0, format="%.2f")
    res = l * b * wind_faktor
    with c3:
        st.markdown(f"<div style='padding-top:35px'>= <b>{res:.2f} m²</b></div>", unsafe_allow_html=True)
    return res, l, b

a_tank, lt_t, bt_t = flaeche_zeile_full("Tankfläche", "tank")
a_hof, lt_h, bt_h = flaeche_zeile_full("Hof- / Freifläche", "hof")
a_wasch, lt_w, bt_w = flaeche_zeile_full("Waschplatz (außen)", "wasch")
a_lager, lt_l, bt_l = flaeche_zeile_full("Lager- / Abstellfläche", "lager")
a_wand, lt_wa, bt_wa = flaeche_zeile_full("Wandfläche (Schlagregen 50%)", "wand", wind_faktor=0.5)

total_area = a_tank + a_hof + a_wasch + a_lager + a_wand
qr = (r_spende * total_area) / 10000
st.info(f"Gesamtfläche: {total_area:.2f} m² | $Q_r$ = {qr:.2f} l/s")

st.divider()

# --- 2. SCHMUTZWASSER ---
st.header("2. Schmutzwasser ($Q_s$)")
col_s1, col_s2 = st.columns(2)
with col_s1:
    v15_c = st.number_input("Anzahl Ventile DN 15", min_value=0, step=1)
    v20_c = st.number_input("Anzahl Ventile DN 20", min_value=0, step=1)
    v25_c = st.number_input("Anzahl Ventile DN 25", min_value=0, step=1)

valve_details, qs1_total = get_valve_flows_detailed(v15_c, v20_c, v25_c)

with col_s2:
    wasch_typ = st.selectbox("Waschanlage", ["Keine", "Portalwaschanlage", "Waschstraße"])
    anz_hd = st.number_input("Anzahl HD-Reiniger", min_value=0, step=1)

is_wash = wasch_typ in ["Portalwaschanlage", "Waschstraße"]
qs_w = 2.0 if is_wash else 0.0
qs_hd = 0.0
if anz_hd > 0:
    qs_hd = anz_hd * 1.0 if is_wash else (2.0 + (anz_hd - 1) * 1.0)
        
qs = qs1_total + qs_w + qs_hd
st.info(f"Gesamt Schmutzwasser $Q_s$ = {qs:.2f} l/s")

st.divider()

# --- 3. FAKTOREN ---
st.header("3. Faktoren & Anlagentyp")
at = st.selectbox("Gewählter Anlagentyp", ["S-II-P", "S-I-P", "S-II-I-P"])
fx = 2.0 if (a_wasch > 0 or is_wash or anz_hd > 0 or qs1_total > 0) else 1.0

dichte = st.selectbox("Dichte der Leichtflüssigkeit (g/cm³)", ["bis 0,85", "0,85 - 0,90", "0,90 - 0,95"])
fd_map = {
    "bis 0,85": {"S-II-P": 1.0, "S-I-P": 1.0, "S-II-I-P": 1.0},
    "0,85 - 0,90": {"S-II-P": 2.0, "S-I-P": 1.5, "S-II-I-P": 1.0},
    "0,90 - 0,95": {"S-II-P": 3.0, "S-I-P": 2.0, "S-II-I-P": 1.0}
}
fd = fd_map[dichte][at]

fame = st.selectbox("Biodiesel-Anteil (FAME)", ["bis 5 %", "5 - 10 %", "über 10 %"])
ff_map = {
    "bis 5 %": {"S-II-P": 1.25, "S-I-P": 1.0, "S-II-I-P": 1.0},
    "5 - 10 %": {"S-II-P": 1.50, "S-I-P": 1.25, "S-II-I-P": 1.0},
    "über 10 %": {"S-II-P": 1.75, "S-I-P": 1.50, "S-II-I-P": 1.25}
}
ff = ff_map[fame][at]

st.divider()

# --- 4. ERGEBNIS NS ---
st.header("4. Ergebnis Nenngröße")
ns = (qr + fx * qs) * fd * ff
st.latex(rf"NS = ({qr:.2f} + {fx} \cdot {qs:.2f}) \cdot {fd} \cdot {ff} = {ns:.2f}")
st.success(f"### Erforderliche Nenngröße: NS {ns:.2f}")

st.divider()

# --- 5. SCHLAMMFANGVOLUMEN ---
st.header("5. Schlammfangvolumen")

if is_wash:
    v_sf_calc = 5000.0
    bew_t = "Waschstraße / Portalwaschanlage"
    sf_faktor = 0
else:
    anfall = st.radio("Erwarteter Schlammanfall:", ["Kein", "Gering", "Mittel", "Groß"], index=0)
    sf_faktor = {"Kein": 0, "Gering": 100, "Mittel": 200, "Groß": 300}[anfall]
    v_sf_calc = (sf_faktor * ns) / fd if fd > 0 else 0
    bew_t = {
        "Kein": "Kondensat",
        "Gering": "Geringer Schmutzanfall (z. B. Auffangtassen)",
        "Mittel": "Tankstellen, PKW-Wäsche, Werkstätten",
        "Groß": "LKW-Waschplätze, Baumaschinen"
    }[anfall]

v_min = 0.0
if ns > 0:
    v_min = 5000.0 if is_wash else (600.0 if ns <= 3 else 2500.0)

v_final = max(v_sf_calc, v_min) if ns > 0 else 0.0
st.metric("Erforderliches Volumen", f"{v_final:.2f} Liter")

st.divider()

# --- PDF GENERIERUNG ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "Bemessungsprotokoll: Abscheideranlage".encode('latin-1').decode('latin-1'), ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 6, "Nach DIN 1999-100 / DIN EN 858-2".encode('latin-1').decode('latin-1'), ln=True, align='C')
    pdf.ln(10)
    
    # Projektdaten
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, " Projektinformationen".encode('latin-1').decode('latin-1'), ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(50, 8, "Name Kunde:".encode('latin-1').decode('latin-1'), border='B')
    pdf.cell(140, 8, f" {kunden_name if kunden_name else '---'}".encode('latin-1').decode('latin-1'), border='B', ln=True)
    pdf.cell(50, 8, "Straße/Nr:".encode('latin-1').decode('latin-1'), border='B')
    pdf.cell(140, 8, f" {kunden_strasse if kunden_strasse else '---'}".encode('latin-1').decode('latin-1'), border='B', ln=True)
    pdf.cell(50, 8, "PLZ / Ort:".encode('latin-1').decode('latin-1'), border='B')
    pdf.cell(140, 8, f" {kunden_ort if kunden_ort else '---'}".encode('latin-1').decode('latin-1'), border='B', ln=True)
    pdf.cell(50, 8, "Datum:", border='B')
    pdf.cell(140, 8, f" {datetime.now().strftime('%d.%m.%Y')}", border='B', ln=True)
    pdf.ln(5)
    
    # Regenwasser
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, " 1. Regenwasser-Berechnung (Qr)".encode('latin-1').decode('latin-1'), ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(190, 6, f"Festgelegte Regenspende i: {r_spende} l/(s*ha). Diese basiert auf örtlichen Wetterdaten (Regendauer D=5 min, Jährlichkeit T=2 Jahre) gemäß DIN 1986-100.".encode('latin-1').decode('latin-1'))
    pdf.ln(2)
    pdf.cell(100, 7, f"Gesamtfläche: {total_area:.2f} m²".encode('latin-1').decode('latin-1'))
    pdf.cell(90, 7, f"Qr = {qr:.2f} l/s", ln=True, align='R')
    pdf.ln(4)

    # Schmutzwasser
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, " 2. Schmutzwasser-Berechnung (Qs)".encode('latin-1').decode('latin-1'), ln=True, fill=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Auslaufventile (Gleichzeitigkeit berücksichtigt):".encode('latin-1').decode('latin-1'), ln=True)
    pdf.set_font("Arial", '', 10)
    for v in valve_details:
        pdf.cell(100, 6, f"- {v['Pos']}. Ventil: DN {v['DN']}")
        pdf.cell(90, 6, f"{v['Flow']:.2f} l/s", ln=True, align='R')
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(100, 8, "Summe Schmutzwasser (Qs):")
    pdf.cell(90, 8, f"{qs:.2f} l/s", ln=True, align='R')
    pdf.ln(4)

    # Schlammfang
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, " 3. Schlammfangvolumen (V)", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(190, 6, f"Einstufung: {bew_t}".encode('latin-1').decode('latin-1'))
    pdf.ln(2)
    if is_wash:
        pdf.cell(0, 7, "Waschanlagen erfordern einen Festwert von 5.000 Litern.".encode('latin-1').decode('latin-1'), ln=True)
    else:
        pdf.cell(0, 7, f"Berechnung: ({sf_faktor} * NS) / fd = ({sf_faktor} * {ns:.2f}) / {fd} = {v_sf_calc:.2f} l".encode('latin-1').decode('latin-1'), ln=True)
        pdf.cell(0, 7, f"Gesetzlicher Mindestwert gemäß NS {ns:.2f}: {v_min:.0f} l".encode('latin-1').decode('latin-1'), ln=True)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, "Gewähltes Schlammfangvolumen:".encode('latin-1').decode('latin-1'))
    pdf.cell(90, 10, f"{v_final:.2f} Liter", ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1')

if kunden_name and kunden_strasse and kunden_ort:
    pdf_bytes = create_pdf()
    st.download_button(label="📄 PDF Protokoll herunterladen", data=pdf_bytes, file_name=f"Bemessung_{kunden_name}.pdf", mime="application/pdf")
else:
    st.info("Bitte Kundendaten (Name, Straße, Ort) eingeben, um das PDF zu aktivieren.")
