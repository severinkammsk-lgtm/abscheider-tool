import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io

# 1. Seiteneinstellungen
st.set_page_config(page_title="Abscheider-Bemessung PRO", layout="centered")

# 2. CSS: Entfernt die + / - Buttons und optimiert die Eingabe
st.markdown("""
    <style>
    input[::-webkit-outer-spin-button],
    input[::-webkit-inner-spin-button] { -webkit-appearance: none !important; margin: 0 !important; }
    input[type=number] { -moz-appearance: textfield !important; }
    .stNumberInput div div input { text-align: center !important; font-size: 20px !important; }
    </style>
""", unsafe_allow_html=True)

# --- PROJEKTDATEN ---
st.title("📋 Abscheider-Bemessung (DIN 1999-100)")
col_k1, col_k2 = st.columns(2)
with col_k1:
    kunden_name = st.text_input("Bauvorhaben / Kunde", placeholder="Name des Objekts")
with col_k2:
    kunden_adresse = st.text_input("Standort / Ort", placeholder="Anschrift")

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
    v15 = st.number_input("Ventil DN 15 (0,5 l/s)", min_value=0)
    v20 = st.number_input("Ventil DN 20 (1,0 l/s)", min_value=0)
    v25 = st.number_input("Ventil DN 25 (1,7 l/s)", min_value=0)
with col_s2:
    wasch_typ = st.selectbox("Waschanlage", ["Keine", "Portalwaschanlage", "Waschstraße"])
    anz_hd = st.number_input("Anzahl HD-Reiniger", min_value=0)

is_wash = wasch_typ in ["Portalwaschanlage", "Waschstraße"]
qs_w = 2.0 if is_wash else 0.0
qs_hd = anz_hd * 1.0 if is_wash else (2.0 + (anz_hd - 1) * 1.0 if anz_hd > 0 else 0.0)
qs = (v15 * 0.5) + (v20 * 1.0) + (v25 * 1.7) + qs_w + qs_hd
st.info(f"Gesamt Qs = {qs:.2f} l/s")

st.divider()

# --- 3. FAKTOREN ---
st.header("3. Faktoren & Anlagentyp")
anlagentyp = st.selectbox("Gewählter Anlagentyp", ["S-II-P", "S-I-P", "S-II-I-P"])
fx = 2.0 if (a_wasch > 0 or is_wash or anz_hd > 0) else 1.0

dichte = st.selectbox("Dichte der Leichtflüssigkeit (g/cm³)", ["bis 0,85", "0,85 - 0,90", "0,90 - 0,95"])
fd_map = {
    "bis 0,85": {"S-II-P": 1.0, "S-I-P": 1.0, "S-II-I-P": 1.0},
    "0,85 - 0,90": {"S-II-P": 2.0, "S-I-P": 1.5, "S-II-I-P": 1.0},
    "0,90 - 0,95": {"S-II-P": 3.0, "S-I-P": 2.0, "S-II-I-P": 1.0}
}
fd = fd_map[dichte][anlagentyp]

fame = st.selectbox("Biodiesel-Anteil (FAME)", ["bis 5 %", "5 - 10 %", "über 10 %"])
ff_map = {
    "bis 5 %": {"S-II-P": 1.25, "S-I-P": 1.0, "S-II-I-P": 1.0},
    "5 - 10 %": {"S-II-P": 1.50, "S-I-P": 1.25, "S-II-I-P": 1.0},
    "über 10 %": {"S-II-P": 1.75, "S-I-P": 1.50, "S-II-I-P": 1.25}
}
ff = ff_map[fame][anlagentyp]

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
    v_sf = 5000.0
    bewertung_text = "Waschstraße / Portalwaschanlage (Festwert)"
    st.warning(f"Bewertung: {bewertung_text}")
else:
    anfall = st.radio("Erwarteter Schlammanfall:", ["Kein", "Gering", "Mittel", "Groß"], index=0)
    if anfall == "Kein":
        bewertung_text = "Kondensat"
        v_sf = 0.0
    elif anfall == "Gering":
        bewertung_text = "Regenauffangflächen mit geringem Schmutzanfall (Auffangtassen, etc.)"
        v_sf = (100 * ns) / (fd * ff)
    elif anfall == "Mittel":
        bewertung_text = "Tankstellen, PKW-Wäsche, Werkstätten, Abstellflächen"
        v_sf = (200 * ns) / (fd * ff)
    elif anfall == "Groß":
        bewertung_text = "Waschplätze für LKW, Baumaschinen, landwirtschaftliche Maschinen"
        v_sf = (300 * ns) / (fd * ff)
    st.info(f"Bewertung: {bewertung_text}")

if v_sf > 5000.0:
    v_sf = 5000.0

st.metric("Berechnetes Volumen", f"{v_sf:.2f} Liter")

st.divider()

# --- PDF GENERIERUNG (DETAILREICH) ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "Berechnungsprotokoll: Leichtflussigkeitsabscheider", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 10, f"Erstellt am: {datetime.now().strftime('%d.%m.%Y')}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, " Projektinformationen", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"Bauvorhaben: {kunden_name if kunden_name else 'Nicht angegeben'}", ln=True)
    pdf.cell(0, 8, f"Standort: {kunden_adresse if kunden_adresse else 'Nicht angegeben'}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, " Ergebnisse", ln=True, fill=True)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 10, " Erforderliche Nenngrosse:")
    pdf.cell(90, 10, f"NS {ns:.2f}", ln=True, align='R')
    pdf.cell(100, 10, " Erforderliches Schlammfangvolumen:")
    pdf.cell(90, 10, f"{v_sf:.2f} Liter", ln=True, align='R')
    pdf.ln(5)
    
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(190, 6, f"Bewertung Schlammanfall: {bewertung_text}")
    
    return pdf.output(dest='S').encode('latin-1')

if kunden_name and kunden_adresse:
    pdf_data = create_pdf()
    st.download_button(label="📄 PDF Protokoll herunterladen", data=pdf_data, file_name=f"Bemessung_{kunden_name}.pdf", mime="application/pdf")
else:
    st.info("Bitte Projektname und Standort oben eingeben, um das PDF zu erstellen.")
