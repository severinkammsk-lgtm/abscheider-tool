import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io

# 1. Seiteneinstellungen
st.set_page_config(page_title="Abscheider-Bemessung PRO", layout="centered")

# 2. CSS für ein sauberes Design (entfernt +/- Buttons bei Zahlenfeldern)
st.markdown("""
    <style>
    input::-webkit-outer-spin-button, input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
    input[type=number] { -moz-appearance: textfield; }
    .stNumberInput div div input { text-align: center; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- PROJEKTDATEN ---
st.title("📋 Abscheider-Bemessung (DIN 1999-100)")
col_k1, col_k2 = st.columns(2)
with col_k1:
    kunden_name = st.text_input("Bauvorhaben / Kunde", placeholder="Name")
with col_k2:
    kunden_adresse = st.text_input("Standort", placeholder="Ort")

st.divider()

# --- 1. REGENABFLUSS (Qr) [cite: 3, 11] ---
st.header("1. Regenabfluss ($Q_r$)")
r_spende = st.number_input("Regenspende $i$ [$l/(s \cdot ha)$]", value=300.0, format="%.1f")

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

a_tank, lt, bt = flaeche_zeile("Tankfläche", "tank")
a_hof, lh, bh = flaeche_zeile("Hof- / Freifläche", "hof")
a_wasch, lw, bw = flaeche_zeile("Waschplatz (außen)", "wasch")
a_lager, ll, bl = flaeche_zeile("Lager- / Abstellfläche", "lager")
a_wand, lwa, bwa = flaeche_zeile("Wandfläche (Schlagregen 50%)", "wand", wind_faktor=0.5)

total_area = a_tank + a_hof + a_wasch + a_lager + a_wand
qr = (r_spende * total_area) / 10000
st.info(f"Gesamtfläche: {total_area:.2f} m² | $Q_r$ = {qr:.2f} l/s [cite: 15]")

st.divider()

# --- 2. SCHMUTZWASSER (Qs) [cite: 3, 19] ---
st.header("2. Schmutzwasser ($Q_s$)")
col_s1, col_s2 = st.columns(2)
with col_s1:
    v15 = st.number_input("Anzahl Ventile DN 15 (0,5 l/s)", min_value=0)
    v20 = st.number_input("Anzahl Ventile DN 20 (1,0 l/s)", min_value=0)
    v25 = st.number_input("Anzahl Ventile DN 25 (1,7 l/s)", min_value=0)
with col_s2:
    wasch_typ = st.selectbox("Waschanlage", ["Keine", "Portalwaschanlage", "Waschstraße"])
    anz_hd = st.number_input("Anzahl HD-Reiniger", min_value=0)

is_wash = wasch_typ in ["Portalwaschanlage", "Waschstraße"]
qs_w = 2.0 if is_wash else 0.0
qs_hd = anz_hd * 1.0 if is_wash else (2.0 + (anz_hd - 1) * 1.0 if anz_hd > 0 else 0.0)
qs = (v15 * 0.5) + (v20 * 1.0) + (v25 * 1.7) + qs_w + qs_hd
st.info(f"Gesamt $Q_s$ = {qs:.2f} l/s [cite: 23]")

st.divider()

# --- 3. FAKTOREN & ANLAGENTYP [cite: 39, 49] ---
st.header("3. Faktoren & Anlagentyp")
at = st.selectbox("Gewählter Anlagentyp", ["S-II-P", "S-I-P", "S-II-I-P"])
fx = 2.0 if (a_wasch > 0 or is_wash or anz_hd > 0) else 1.0 [cite: 28, 29]

dichte = st.selectbox("Dichte der Leichtflüssigkeit ($g/cm³$)", ["bis 0,85", "über 0,85", "über 0,90-0,95"])
fd_map = {
    "bis 0,85": {"S-II-P": 1.0, "S-I-P": 1.0, "S-II-I-P": 1.0},
    "über 0,85": {"S-II-P": 2.0, "S-I-P": 1.5, "S-II-I-P": 1.0},
    "über 0,90-0,95": {"S-II-P": 3.0, "S-I-P": 2.0, "S-II-I-P": 1.0}
}
fd = fd_map[dichte][at] [cite: 39]

fame = st.selectbox("Biodiesel-Anteil (FAME)", ["bis 5 %", "über 5 - 10 %", "über 10 %"])
ff_map = {
    "bis 5 %": {"S-II-P": 1.25, "S-I-P": 1.0, "S-II-I-P": 1.0},
    "über 5 - 10 %": {"S-II-P": 1.50, "S-I-P": 1.25, "S-II-I-P": 1.0},
    "über 10 %": {"S-II-P": 1.75, "S-I-P": 1.50, "S-II-I-P": 1.25}
}
ff = ff_map[fame][at] [cite: 49]

st.divider()

# --- 4. ERGEBNIS NS [cite: 55, 56] ---
st.header("4. Ergebnis Nenngröße")
ns = (qr + fx * qs) * fd * ff
st.latex(rf"NS = (Q_r + f_x \cdot Q_s) \cdot f_d \cdot f_f = {ns:.2f}")
st.success(f"### Erforderliche Nenngröße: NS {ns:.2f}")

st.divider()

# --- 5. SCHLAMMFANGVOLUMEN [cite: 3, 63, 64] ---
st.header("5. Schlammfangvolumen")

if is_wash:
    v_sf_calc = 5000.0
    bewertung = "Fahrzeugwaschanlagen (Mindestwert 5.000 l) [cite: 71]"
    st.warning(f"Bewertung: {bewertung}")
else:
    anfall = st.radio("Erwarteter Schlammanfall auswählen:", ["Kein", "Gering", "Mittel", "Groß"], index=0)
    
    texte = {
        "Kein": "Kondensat ",
        "Gering": "Prozessabwasser mit definierten geringen Schlammmengen; alle Regenauffangflächen mit geringem Schmutzanfall (z.B. Auffangtassen auf Tankfeldern) ",
        "Mittel": "Tankstellen, PKW-Wäsche von Hand, Teilewäsche, Omnibus-Waschstände, Reparaturwerkstätten, Fahrzeugabstellflächen, Kraftwerke ",
        "Groß": "Waschplätze für Baustellenfahrzeuge, Baumaschinen, landwirtschaftliche Maschinen, LKW-Waschanlagen/-stände "
    }
    
    faktor = {"Kein": 0, "Gering": 100, "Mittel": 200, "Groß": 300}[anfall]
    v_sf_calc = (faktor * ns) / fd if fd > 0 else 0
    st.info(f"**Einstufung:** {texte[anfall]}")

# Mindestvolumina prüfen [cite: 70]
v_min = 600.0 if ns <= 3 else 2500.0
if is_wash: v_min = 5000.0
v_final = max(v_sf_calc, v_min) if ns > 0 else 0.0

st.metric("Berechnetes Schlammfangvolumen", f"{v_final:.2f} Liter")

st.divider()

# --- PDF EXPORT ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "Bemessungsprotokoll: Abscheideranlage", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"Kunde: {kunden_name} | Standort: {kunden_adresse}", ln=True)
    pdf.cell(0, 8, f"Datum: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Ergebnisse:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(100, 8, f"Nenngroesse (NS):")
    pdf.cell(0, 8, f"{ns:.2f}", ln=True, align='R')
    pdf.cell(100, 8, f"Schlammfangvolumen (V):")
    pdf.cell(0, 8, f"{v_final:.2f} Liter", ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1')

if kunden_name and kunden_adresse:
    pdf_bytes = create_pdf()
    st.download_button("📄 PDF Protokoll herunterladen", data=pdf_bytes, file_name=f"Bemessung_{kunden_name}.pdf", mime="application/pdf")
else:
    st.info("Bitte Projektname und Standort eingeben, um das PDF zu aktivieren.")
