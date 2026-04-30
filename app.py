import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io
import math

# 1. Seiteneinstellungen
st.set_page_config(page_title="Abscheider-Bemessung PRO", layout="centered")

# 2. CSS: Optimierung für fette Ergebnisse und saubere Eingabe
st.markdown("""
    <style>
    input[::-webkit-outer-spin-button],
    input[::-webkit-inner-spin-button] { -webkit-appearance: none !important; margin: 0 !important; }
    input[type=number] { -moz-appearance: textfield !important; }
    .stNumberInput div div input { text-align: center !important; font-size: 18px !important; }
    </style>
""", unsafe_allow_html=True)

# Hilfsfunktion zur Ventilberechnung nach Tabelle 1 (DIN 1999-100)
def calc_valve_flow(count, values):
    res = 0.0
    for i in range(count):
        if i == 0: res += values[0]
        elif i == 1: res += values[1]
        elif i == 2: res += values[2]
        elif i == 3: res += values[3]
        else: res += values[4]
    return res

# Standard-Nenngrößen nach DIN
def get_next_standard_ns(val):
    standards = [3, 6, 8, 10, 15, 20, 30, 40, 50, 65, 80, 100]
    for s in standards:
        if s >= val: return s
    return val

# --- PROJEKTDATEN ---
st.title("📋 Abscheider-Bemessung (DIN 1999-100)")
kunden_name = st.text_input("Name Kunde", placeholder="Vollständiger Name")
col_adr1, col_adr2 = st.columns(2)
with col_adr1:
    kunden_strasse = st.text_input("Straße, Hausnummer", placeholder="Musterstraße 1")
with col_adr2:
    kunden_ort = st.text_input("Postleitzahl, Ort", placeholder="12345 Musterstadt")

st.divider()

# --- 1. REGENABFLUSS ---
st.header("1. Regenabfluss (Qr)")
r_spende = st.number_input("Regenspende [l/(s * ha)]", value=300.0, format="%.1f")

def flaeche_zeile(label, key_suffix, info=""):
    st.markdown(f"**{label}**")
    if info: st.caption(info)
    c1, c2, c3 = st.columns([3, 3, 2])
    with c1:
        l = st.number_input("Länge [m]", key=f"l_{key_suffix}", min_value=0.0, format="%.2f")
    with c2:
        b = st.number_input("Breite [m]", key=f"b_{key_suffix}", min_value=0.0, format="%.2f")
    res = l * b
    with c3:
        st.markdown(f"<div style='padding-top:35px'>= <b>{res:.2f} m²</b></div>", unsafe_allow_html=True)
    return res

def schlagregen_zeile(label, key_suffix):
    st.markdown(f"**{label}**")
    st.caption("Berechnung: Lange Dachseite * (Dachhöhe * 0,6) gemäß DIN 1999-100")
    c1, c2, c3 = st.columns([3, 3, 2])
    with c1:
        l = st.number_input("Länge [m]", key=f"l_{key_suffix}", min_value=0.0, format="%.2f")
    with c2:
        h = st.number_input("Dachhöhe [m]", key=f"h_{key_suffix}", min_value=0.0, format="%.2f")
    res = l * (h * 0.6)
    with c3:
        st.markdown(f"<div style='padding-top:35px'>= <b>{res:.2f} m²</b></div>", unsafe_allow_html=True)
    return res

a_hof = flaeche_zeile("Hof- / Freifläche", "hof")
a_wasch = flaeche_zeile("Waschplatz (außen)", "wasch")
a_lager = flaeche_zeile("Lager- / Abstellfläche", "lager")
a_schlag = schlagregen_zeile("Schlagregen (Wandfläche)", "schlag")

total_area = a_hof + a_wasch + a_lager + a_schlag
qr_raw = (r_spende * total_area) / 10000
qr = math.ceil(qr_raw * 100) / 100 
st.info(f"Gesamtfläche: {total_area:.2f} m² | **Qr = {qr:.2f} l/s**")

st.divider()

# --- 2. SCHMUTZWASSER ---
st.header("2. Schmutzwasser (Qs)")
col_s1, col_s2 = st.columns(2)
with col_s1:
    v15_c = st.number_input("Anzahl Ventile DN 15", min_value=0, step=1)
    v20_c = st.number_input("Anzahl Ventile DN 20", min_value=0, step=1)
    v25_c = st.number_input("Anzahl Ventile DN 25", min_value=0, step=1)

qs1_total = calc_valve_flow(v15_c, [0.5, 0.5, 0.35, 0.25, 0.1]) + \
            calc_valve_flow(v20_c, [1.0, 1.0, 0.7, 0.5, 0.2]) + \
            calc_valve_flow(v25_c, [1.7, 1.7, 1.2, 0.85, 0.3])

with col_s2:
    wasch_typ = st.selectbox("Waschanlage", ["Keine", "Portalwaschanlage", "Waschstraße"])
    anz_hd = st.number_input("Anzahl HD-Reiniger", min_value=0, step=1)

is_wash = wasch_typ in ["Portalwaschanlage", "Waschstraße"]
qs_w = 2.0 if is_wash else 0.0
if anz_hd > 0:
    qs_hd = anz_hd * 1.0 if is_wash else (2.0 + (anz_hd - 1) * 1.0)
else:
    qs_hd = 0.0
        
qs = qs1_total + qs_w + qs_hd
st.info(f"Gesamt Schmutzwasser **Qs = {qs:.2f} l/s**")

st.divider()

# --- 3. FAKTOREN & ANLAGENTYP ---
st.header("3. Faktoren & Anlagentyp")

t1 = "Schlammfang - Benzinabscheider - Probenahmeschacht"
t2 = "Schlammfang - Koaleszenzabscheider - Probenahmeschacht"
t3 = "Schlammfang - Benzin- & Koaleszenzabscheider - Probenahmeschacht"

at = st.selectbox("Anlagentyp", [t1, t2, t3])

fx = 2.0 if (a_wasch > 0 or is_wash or anz_hd > 0 or qs1_total > 0) else 1.0

# --- NEU: INFO ZUR DICHTE ---
dichte = st.selectbox("Dichte der Leichtflüssigkeit (g/cm³)", ["bis 0,85", "0,85 - 0,90", "0,90 - 0,95"])

with st.expander("ℹ️ Hilfe zur Auswahl der Dichte"):
    st.markdown("""
    Die Dichte bestimmt den Faktor **fd**. Je schwerer die Flüssigkeit, desto größer muss der Abscheider sein:
    *   **bis 0,85 g/cm³:**
        *   **Benzin:** ca. 0,72 – 0,78 g/cm³
        *   **Diesel / Heizöl EL:** ca. 0,82 – 0,85 g/cm³
        *   *Standardfall für fast alle Tankstellen und Werkstätten.*
    *   **0,85 - 0,90 g/cm³:**
        *   **Biodiesel (RME):** ca. 0,88 g/cm³
        *   **Schwerere Schmieröle:** z.B. bestimmte Hydrauliköle.
    *   **0,90 - 0,95 g/cm³:**
        *   **Spezielle Schweröle** oder chemische Leichtflüssigkeiten.
    """)

fd_map = {
    "bis 0,85": 1.0, 
    "0,85 - 0,90": {t1: 2.0, t2: 1.5, t3: 1.0}, 
    "0,90 - 0,95": {t1: 3.0, t2: 2.0, t3: 1.0}
}
fd = fd_map[dichte] if dichte == "bis 0,85" else fd_map[dichte][at]

fame = st.selectbox("Biodiesel (FAME)", ["bis 5 %", "über 5 - 10 %", "über 10 %"])

with st.expander("ℹ️ Hilfe zur Auswahl der Treibstoffsorte (Bio-Anteil)"):
    st.markdown("""
    Die Auswahl richtet sich nach dem Anteil an **Fettsäuremethylester (FAME)** im Kraftstoff:
    *   **bis 5 %:** Super E5, Super Plus, HVO/GTL (synthetisch).
    *   **über 5 - 10 %:** **Diesel (B7)** (Standard in DE), Diesel (B10), Super E10.
    *   **über 10 %:** B20, B30, B100 (reiner Biodiesel).
    """)

ff_map = {
    "bis 5 %": {t1: 1.25, t2: 1.0, t3: 1.0}, 
    "über 5 - 10 %": {t1: 1.50, t2: 1.25, t3: 1.0}, 
    "über 10 %": {t1: 1.75, t2: 1.50, t3: 1.25}
}
ff = ff_map[fame][at]

st.divider()

# --- 4. ERGEBNIS NENNGRÖSSE ---
st.header("4. Ergebnis Nenngröße")
ns_raw = (qr + fx * qs) * fd * ff
ns = math.ceil(ns_raw * 100) / 100 
standard_ns = get_next_standard_ns(ns)

# Rechenformel gemäß Vorgabe
st.latex(rf"NS = ({qr:.2f} + {fx} \cdot {qs:.2f}) \cdot {fd} \cdot {ff} = {ns:.2f}")
st.success(f"### Erforderliche Nenngröße: **NS {ns:.2f}**")

st.divider()

# --- 5. SCHLAMMFANGVOLUMEN ---
st.header("5. Schlammfangvolumen")

anfall_opt = {"Kein" + " "*15 + "0%": 0, "Gering" + " "*10 + "100%": 100, "Mittel" + " "*10 + "200%": 200, "Groß" + " "*12 + "300%": 300}
selection = st.radio("Schlammanfall auswählen:", list(anfall_opt.keys()), index=0)
sf_faktor = anfall_opt[selection]
v_final = (sf_faktor * ns) / fd if (fd > 0 and sf_faktor > 0) else 0.0

bew_map = {
    0: "Kondensat",
    100: "Regenauffangflächen mit geringem Schmutzanfall",
    200: "Teilewäsche, Werkstätten, Fahrzeugabstellflächen, Kraftwerke",
    300: "Waschplätze für Baumaschinen, LKW-Waschstände, automatische Waschanlagen"
}
bew_t = bew_map[sf_faktor]
st.info(f"**Bewertung:** {bew_t}")

st.metric("Erforderliches Volumen", f"**{v_final:.2f} Liter**")

st.divider()

# --- PDF GENERIERUNG ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    def txt(s): return s.encode('latin-1', 'replace').decode('latin-1')

    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt("BEMESSUNGSPROTOKOLL: ABSCHEIDERANLAGE"), ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 6, txt("Gemäß DIN 1999-100 / DIN EN 858-2"), ln=True, align='C')
    pdf.ln(10)
    
    # 1. Projektdaten
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt(" 1. Projektinformationen"), ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    for label, val in [("Kunde:", kunden_name), ("Anschrift:", kunden_strasse), ("Ort:", kunden_ort), ("Datum:", datetime.now().strftime('%d.%m.%Y'))]:
        pdf.cell(40, 8, txt(label), border='B')
        pdf.cell(150, 8, txt(f" {val if val else '---'}"), border='B', ln=True)
    pdf.ln(5)
    
    # 2. Regenwasser
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt(" 2. Regenwasserabfluss (Qr)"), ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(190, 6, txt(f"Regenspende i: {r_spende} l/(s*ha) gemäß DIN 1986-100. Das Ergebnis wurde aufgerundet."))
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 8, txt(" Maximaler Regenabfluss (aufgerundet):"))
    pdf.cell(90, 8, f"{qr:.2f} l/s", ln=True, align='R')
    pdf.ln(3)

    # 3. Schmutzwasser
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt(" 3. Schmutzwasserabfluss (Qs)"), ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 6, txt(f" Ventile: {qs1_total:.2f} l/s | Waschanlage/HD: {qs_w+qs_hd:.2f} l/s"))
    pdf.ln(6)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 8, txt(" Gesamt-Schmutzwasserabfluss:"), border=0)
    pdf.cell(90, 8, f"{qs:.2f} l/s", ln=True, align='R')
    pdf.ln(3)

    # 4. Faktoren
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt(" 4. Bemessungsparameter"), ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(190, 6, txt(f"Anlagentyp: {at}\nDichte: {dichte} | Biodiesel: {fame}\nErschwernisfaktor fx: {fx} | fd: {fd} | ff: {ff}"))
    pdf.ln(3)

    # 5. Nenngröße
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt(" 5. Erforderliche Nenngröße (NS)"), ln=True, fill=True)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, txt(" BERECHNETE NENNGRÖSSE (aufgerundet):"))
    pdf.cell(90, 10, f"NS {ns:.2f}", ln=True, align='R')
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 8, txt(" Empfohlene Standard-Nenngröße:"))
    pdf.cell(90, 8, f"NS {standard_ns}", ln=True, align='R')
    pdf.ln(3)

    # 6. Schlammfang
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt(" 6. Schlammfangvolumen (V)"), ln=True, fill=True)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, txt(" ERFORDERLICHES SCHLAMMVOLUMEN:"))
    pdf.cell(90, 10, f"{v_final:.2f} Liter", ln=True, align='R')
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(190, 6, txt(f"Berechnung: (Faktor {sf_faktor}% * NS) / fd | Einstufung: {bew_t}"))
    
    return pdf.output(dest='S').encode('latin-1')

if kunden_name and kunden_strasse and kunden_ort:
    pdf_bytes = create_pdf()
    st.download_button(label="📄 PDF Protokoll herunterladen", data=pdf_bytes, file_name=f"Bemessung_{kunden_name}.pdf", mime="application/pdf")
else:
    st.info("Bitte Kundendaten eingeben, um das PDF zu aktivieren.")
