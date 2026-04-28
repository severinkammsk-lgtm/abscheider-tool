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
    input[::-webkit-outer-spin-button],
    input[::-webkit-inner-spin-button] { -webkit-appearance: none !important; margin: 0 !important; }
    input[type=number] { -moz-appearance: textfield !important; }
    .stNumberInput div div input { text-align: center !important; font-size: 20px !important; }
    </style>
""", unsafe_allow_html=True)

# Hilfsfunktion für die Ventilberechnung nach Tabelle 1 
def calculate_valve_flow(count, values):
    if count <= 0:
        return 0.0
    flow = 0.0
    for i in range(1, count + 1):
        if i == 1: flow += values[0] # 1. Ventil
        elif i == 2: flow += values[1] # 2. Ventil
        elif i == 3: flow += values[2] # 3. Ventil
        elif i == 4: flow += values[3] # 4. Ventil
        else: flow += values[4] # 5. Ventil und jedes weitere
    return flow

# --- PROJEKTDATEN ---
st.title("📋 Abscheider-Bemessung (DIN 1999-100)")
col_k1, col_k2 = st.columns(2)
with col_k1:
    kunden_name = st.text_input("Bauvorhaben / Kunde", placeholder="Vollständiger Name")
with col_k2:
    kunden_adresse = st.text_input("Standort / Ort", placeholder="Straße, PLZ, Ort")

st.divider()

# --- 1. REGENABFLUSS ---
st.header("1. Regenabfluss (Qr)")
r_spende = st.number_input("Regenspende [l/(s * ha)]", value=300.0, format="%.1f")

def flaeche_zeile(label, key_suffix, wind_faktor=1.0):
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

a_tank, l_tank, b_tank = flaeche_zeile("Tankfläche", "tank")
a_hof, l_hof, b_hof = flaeche_zeile("Hof- / Freifläche", "hof")
a_wasch, l_wasch, b_wasch = flaeche_zeile("Waschplatz (außen)", "wasch")
a_lager, l_lager, b_lager = flaeche_zeile("Lager- / Abstellfläche", "lager")
a_wand, l_wand, b_wand = flaeche_zeile("Wandfläche (Schlagregen 50%)", "wand", wind_faktor=0.5)

total_area = a_tank + a_hof + a_wasch + a_lager + a_wand
qr = (r_spende * total_area) / 10000
st.info(f"Gesamtfläche: {total_area:.2f} m² | Qr = {qr:.2f} l/s")

st.divider()

# --- 2. SCHMUTZWASSER ---
st.header("2. Schmutzwasser (Qs)")
col_s1, col_s2 = st.columns(2)
with col_s1:
    v15_count = st.number_input("Anzahl Ventile DN 15", min_value=0, step=1)
    v20_count = st.number_input("Anzahl Ventile DN 20", min_value=0, step=1)
    v25_count = st.number_input("Anzahl Ventile DN 25", min_value=0, step=1)

# Abflusswerte nach Tabelle 1 
# Format: [1. Ventil, 2. Ventil, 3. Ventil, 4. Ventil, 5.+ Ventil]
qs1_15 = calculate_valve_flow(v15_count, [0.5, 0.5, 0.35, 0.25, 0.1])
qs1_20 = calculate_valve_flow(v20_count, [1.0, 1.0, 0.7, 0.5, 0.2])
qs1_25 = calculate_valve_flow(v25_count, [1.7, 1.7, 1.2, 0.85, 0.3])
qs1_total = qs1_15 + qs1_20 + qs1_25

with col_s2:
    wasch_typ = st.selectbox("Waschanlage", ["Keine", "Portalwaschanlage", "Waschstraße"])
    anz_hd = st.number_input("Anzahl HD-Reiniger", min_value=0, step=1)

is_wash = wasch_typ in ["Portalwaschanlage", "Waschstraße"]
qs_w = 2.0 if is_wash else 0.0 # 
qs_hd = 0.0
if anz_hd > 0:
    # Erstgerät 2,0 l/s, Folgegeräte 1,0 l/s 
    # In Verbindung mit Waschanlage: Erstes HD-Gerät bereits 1,0 l/s 
    if is_wash:
        qs_hd = anz_hd * 1.0
    else:
        qs_hd = 2.0 + (anz_hd - 1) * 1.0
        
qs = qs1_total + qs_w + qs_hd # [cite: 19-22]
st.info(f"Gesamt Schmutzwasser Qs = {qs:.2f} l/s")

st.divider()

# --- 3. FAKTOREN ---
st.header("3. Faktoren & Anlagentyp")
at = st.selectbox("Gewählter Anlagentyp", ["S-II-P", "S-I-P", "S-II-I-P"])
# fx=2.0 bei Schmutzwasserbehandlung [cite: 28]
fx = 2.0 if (a_wasch > 0 or is_wash or anz_hd > 0 or qs1_total > 0) else 1.0 # [cite: 28, 29]

dichte = st.selectbox("Dichte der Leichtflüssigkeit (g/cm³)", ["bis 0,85", "0,85 - 0,90", "0,90 - 0,95"])
fd_map = {
    "bis 0,85": {"S-II-P": 1.0, "S-I-P": 1.0, "S-II-I-P": 1.0},
    "0,85 - 0,90": {"S-II-P": 2.0, "S-I-P": 1.5, "S-II-I-P": 1.0},
    "0,90 - 0,95": {"S-II-P": 3.0, "S-I-P": 2.0, "S-II-I-P": 1.0}
}
fd = fd_map[dichte][at] # [cite: 39]

fame = st.selectbox("Biodiesel-Anteil (FAME)", ["bis 5 %", "5 - 10 %", "über 10 %"])
ff_map = {
    "bis 5 %": {"S-II-P": 1.25, "S-I-P": 1.0, "S-II-I-P": 1.0},
    "5 - 10 %": {"S-II-P": 1.50, "S-I-P": 1.25, "S-II-I-P": 1.0},
    "über 10 %": {"S-II-P": 1.75, "S-I-P": 1.50, "S-II-I-P": 1.25}
}
ff = ff_map[fame][at] # [cite: 49]

st.divider()

# --- 4. ERGEBNIS NS ---
st.header("4. Ergebnis Nenngröße")
ns = (qr + fx * qs) * fd * ff # [cite: 56]
st.latex(rf"NS = ({qr:.2f} + {fx} \cdot {qs:.2f}) \cdot {fd} \cdot {ff} = {ns:.2f}")
st.success(f"### Erforderliche Nenngröße: NS {ns:.2f}")

st.divider()

# --- 5. SCHLAMMFANGVOLUMEN ---
st.header("5. Schlammfangvolumen")

if is_wash:
    v_sf = 5000.0 # Mindestvolumen Waschanlage [cite: 71]
    bewertung_text = "Waschstraße / Portalwaschanlage (Mindestvolumen 5000 l nach DIN 1999-100)"
    st.warning(f"Bewertung: {bewertung_text}")
else:
    anfall = st.radio("Erwarteter Schlammanfall auswählen:", ["Kein", "Gering", "Mittel", "Groß"], index=0)
    
    if anfall == "Kein":
        bewertung_text = "Kondensat"
        v_sf = 0.0
    elif anfall == "Gering":
        bewertung_text = "alle Regenauffangflächen, auf denen nur geringe Mengen an Schmutz durch Straßenverkehr oder Ähnliches anfällt, z.B. Auffangtassen auf Tankfeldern und überdachten Tankstellen"
        # 100 * NS / fd 
        v_sf = (100 * ns) / fd if fd > 0 else 0
    elif anfall == "Mittel":
        bewertung_text = "Tankstellen, PKW-Wäsche von Hand, Teilewäsche, Omnibus-Waschstände, Abwasser aus Reparaturwerkstätten, Fahrzeugabstellflächen, Kraftwerke, Maschinenbaubetriebe"
        # 200 * NS / fd 
        v_sf = (200 * ns) / fd if fd > 0 else 0
    elif anfall == "Groß":
        bewertung_text = "Waschplätze für Baustellenfahrzeuge, Baumaschinen, landwirtschaftliche Maschinen, LKW-Waschstände"
        # 300 * NS / fd 
        v_sf = (300 * ns) / fd if fd > 0 else 0
    
    # Mindestschlammfangvolumina einhalten [cite: 70]
    if ns > 0:
        v_min = 600.0 if ns <= 3 else 2500.0
        if v_sf < v_min:
            v_sf = v_min
            bewertung_text += f" (Erhöht auf Mindestvolumen {v_min} l)"

    st.info(f"**Bewertung:** {bewertung_text}")

# Deckelung auf 5000 Liter (Optional, falls gewünscht - Norm erlaubt mehr)
# if v_sf > 5000.0: v_sf = 5000.0

st.metric("Berechnetes Volumen", f"{v_sf:.2f} Liter")

st.divider()

# --- PDF GENERIERUNG ---
def create_detailed_pdf():
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "Berechnungsprotokoll: Leichtflussigkeitsabscheider", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 6, "Gemaess DIN 1999-100 / DIN EN 858-2", ln=True, align='C')
    pdf.ln(10)
    
    # Projektdaten
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, " Projektinformationen", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(50, 8, "Bauvorhaben:", border='B')
    pdf.cell(140, 8, f" {kunden_name if kunden_name else '---'}", border='B', ln=True)
    pdf.cell(50, 8, "Standort:", border='B')
    pdf.cell(140, 8, f" {kunden_adresse if kunden_adresse else '---'}", border='B', ln=True)
    pdf.cell(50, 8, "Datum:", border='B')
    pdf.cell(140, 8, f" {datetime.now().strftime('%d.%m.%Y')}", border='B', ln=True)
    pdf.ln(10)
    
    # Regenwasser Detail
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, " 1. Regenwasser-Berechnung (Qr)", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    flaechen = [
        ("Tankflaeche", l_tank, b_tank, a_tank),
        ("Hof-/Freiflaeche", l_hof, b_hof, a_hof),
        ("Waschplatz", l_wasch, b_wasch, a_wasch),
        ("Lagerflaeche", l_lager, b_lager, a_lager),
        ("Wandflaeche (50%)", l_wand, b_wand, a_wand)
    ]
    for n, l, b, q in flaechen:
        if q > 0:
            pdf.cell(100, 7, f"- {n}: {l}m x {b}m")
            pdf.cell(90, 7, f"= {q:.2f} m2", ln=True, align='R')
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 10, "Gesamt Regenabfluss (Qr):")
    pdf.cell(90, 10, f"{qr:.2f} l/s", ln=True, align='R')
    pdf.ln(5)

    # Schmutzwasser Detail
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, " 2. Schmutzwasser-Berechnung (Qs)", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 7, f"- Auslaufventile (Gleichzeitigkeit beruecksichtigt):")
    pdf.cell(90, 7, f"{qs1_total:.2f} l/s", ln=True, align='R')
    if qs_w > 0:
        pdf.cell(100, 7, f"- Waschanlage ({wasch_typ}):")
        pdf.cell(90, 7, f"{qs_w:.2f} l/s", ln=True, align='R')
    if qs_hd > 0:
        pdf.cell(100, 7, f"- Hochdruckreiniger ({anz_hd} Stk.):")
        pdf.cell(90, 7, f"{qs_hd:.2f} l/s", ln=True, align='R')
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 10, "Gesamt Schmutzwasser (Qs):")
    pdf.cell(90, 10, f"{qs:.2f} l/s", ln=True, align='R')
    pdf.ln(5)

    # Ergebnisse
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 50, 150)
    pdf.cell(190, 12, " BERECHNUNGSERGEBNIS", ln=True, align='C', border=1)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, " Erforderliche Nenngroesse:")
    pdf.cell(90, 10, f"NS {ns:.2f}", ln=True, align='R')
    pdf.cell(100, 10, " Erforderliches Schlammvolumen:")
    pdf.cell(90, 10, f"{v_sf:.2f} Liter", ln=True, align='R')
    pdf.ln(5)
    
    # Schlammfang Bewertung vollstaendig
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, " Bewertungsgrundlage Schlammanfall:", ln=True)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(190, 6, bewertung_text)
    
    return pdf.output(dest='S').encode('latin-1')

if kunden_name and kunden_adresse:
    pdf_bytes = create_detailed_pdf()
    st.download_button(
        label="📄 Professionelles PDF-Protokoll erstellen",
        data=pdf_bytes,
        file_name=f"Bemessung_{kunden_name}.pdf",
        mime="application/pdf"
    )
else:
    st.info("Bitte geben Sie Projektname und Standort oben ein, um das detaillierte PDF-Protokoll zu generieren.")
