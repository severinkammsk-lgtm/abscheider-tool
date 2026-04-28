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

# Hilfsfunktion zur Ventilberechnung nach DIN 1999-100 (Tabelle 1)
def calc_valve_flow(count, values):
    res = 0.0
    for i in range(count):
        if i == 0: res += values[0]
        elif i == 1: res += values[1]
        elif i == 2: res += values[2]
        elif i == 3: res += values[3]
        else: res += values[4]
    return res

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
        l = st.number_input("Lange Seite [m]", key=f"l_{key_suffix}", min_value=0.0, format="%.2f")
    with c2:
        h = st.number_input("Dachhöhe [m]", key=f"h_{key_suffix}", min_value=0.0, format="%.2f")
    res = l * (h * 0.6)
    with c3:
        st.markdown(f"<div style='padding-top:35px'>= <b>{res:.2f} m²</b></div>", unsafe_allow_html=True)
    return res

a_tank = flaeche_zeile("Tankfläche", "tank", info="Hinweis: Nur unüberdachte Bodenfläche messen.")
a_hof = flaeche_zeile("Hof- / Freifläche", "hof")
a_wasch = flaeche_zeile("Waschplatz (außen)", "wasch")
a_lager = flaeche_zeile("Lager- / Abstellfläche", "lager")
a_schlag = schlagregen_zeile("Schlagregen (Wandfläche)", "schlag")

total_area = a_tank + a_hof + a_wasch + a_lager + a_schlag
qr_raw = (r_spende * total_area) / 10000
# Immer aufrunden auf 2 Dezimalstellen
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

qs1_15 = calc_valve_flow(v15_c, [0.5, 0.5, 0.35, 0.25, 0.1])
qs1_20 = calc_valve_flow(v20_c, [1.0, 1.0, 0.7, 0.5, 0.2])
qs1_25 = calc_valve_flow(v25_c, [1.7, 1.7, 1.2, 0.85, 0.3])
qs1_total = qs1_15 + qs1_20 + qs1_25

with col_s2:
    wasch_typ = st.selectbox("Waschanlage", ["Keine", "Portalwaschanlage", "Waschstraße"])
    anz_hd = st.number_input("Anzahl HD-Reiniger", min_value=0, step=1)

is_wash = wasch_typ in ["Portalwaschanlage", "Waschstraße"]
qs_w = 2.0 if is_wash else 0.0
# HD-Logik: 2,0 l/s wenn keine Waschanlage, sonst 1,0 l/s 
if anz_hd > 0:
    qs_hd = anz_hd * 1.0 if is_wash else (2.0 + (anz_hd - 1) * 1.0)
else:
    qs_hd = 0.0
        
qs = qs1_total + qs_w + qs_hd
st.info(f"Gesamt Schmutzwasser **Qs = {qs:.2f} l/s**")

st.divider()

# --- 3. FAKTOREN ---
st.header("3. Faktoren & Anlagentyp")
at = st.selectbox("Anlagentyp", ["S-II-P", "S-I-P", "S-II-I-P"])
fx = 2.0 if (a_wasch > 0 or is_wash or anz_hd > 0 or qs1_total > 0) else 1.0
dichte = st.selectbox("Dichte der Leichtflüssigkeit (g/cm³)", ["bis 0,85", "0,85 - 0,90", "0,90 - 0,95"])
fd_map = {"bis 0,85": 1.0, "0,85 - 0,90": {"S-II-P": 2.0, "S-I-P": 1.5, "S-II-I-P": 1.0}, "0,90 - 0,95": {"S-II-P": 3.0, "S-I-P": 2.0, "S-II-I-P": 1.0}}
fd = fd_map[dichte] if dichte == "bis 0,85" else fd_map[dichte][at]
fame = st.selectbox("Biodiesel (FAME)", ["bis 5 %", "über 5 - 10 %", "über 10 %"])
ff_map = {"bis 5 %": {"S-II-P": 1.25, "S-I-P": 1.0, "S-II-I-P": 1.0}, "über 5 - 10 %": {"S-II-P": 1.50, "S-I-P": 1.25, "S-II-I-P": 1.0}, "über 10 %": {"S-II-P": 1.75, "S-I-P": 1.50, "S-II-I-P": 1.25}}
ff = ff_map[fame][at]

st.divider()

# --- 4. ERGEBNIS NS ---
st.header("4. Ergebnis Nenngröße")
ns = (qr + fx * qs) * fd * ff
st.latex(rf"NS = ({qr:.2f} + {fx} \cdot {qs:.2f}) \cdot {fd} \cdot {ff} = {ns:.2f}")
st.success(f"### Erforderliche Nenngröße: **NS {ns:.2f}**")

st.divider()

# --- 5. SCHLAMMFANGVOLUMEN ---
st.header("5. Schlammfangvolumen")

anfall_opt = {"Kein" + " "*15 + "0%": 0, "Gering" + " "*10 + "100%": 100, "Mittel" + " "*10 + "200%": 200, "Groß" + " "*12 + "300%": 300}
selection = st.radio("Schlammanfall auswählen:", list(anfall_opt.keys()), index=0)
sf_faktor = anfall_opt[selection]

# Striktes Rechnen nach Faktoren 
v_final = (sf_faktor * ns) / fd if (fd > 0 and sf_faktor > 0) else 0.0

bew_map = {
    0: "Kondensat",
    100: "Regenauffangflächen mit geringem Schmutzanfall (z. B. Auffangtassen auf Tankfeldern)",
    200: "Tankstellen, PKW-Wäsche von Hand, Teilewäsche, Omnibus-Waschstände, Reparaturwerkstätten, Fahrzeugabstellflächen, Kraftwerke, Maschinenbaubetriebe",
    300: "Waschplätze für Baustellenfahrzeuge, Baumaschinen, landwirtschaftliche Maschinen, LKW-Waschstände, automatische Waschanlagen"
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

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt("Bemessungsprotokoll: Abscheideranlage (DIN 1999-100)"), ln=True, align='C')
    pdf.ln(2)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(190, 6, txt(" Projektinformationen"), ln=True, fill=True)
    pdf.set_font("Arial", '', 8)
    for label, val in [("Name Kunde:", kunden_name), ("Straße/Nr:", kunden_strasse), ("PLZ / Ort:", kunden_ort)]:
        pdf.cell(40, 5, txt(label), border='B')
        pdf.cell(150, 5, txt(f" {val if val else '---'}"), border='B', ln=True)
    pdf.cell(40, 5, txt("Datum:"), border='B')
    pdf.cell(150, 5, f" {datetime.now().strftime('%d.%m.%Y')}", border='B', ln=True)
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(190, 6, txt(" 1. Regenwasser-Berechnung (Qr)"), ln=True, fill=True)
    pdf.set_font("Arial", '', 7.5)
    pdf.multi_cell(190, 3.5, txt(f"Regenspende i: {r_spende} l/(s*ha) gemaess DIN 1986-100 (D=5, T=2). Aufgerundet fuer maximale Sicherheit."))
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(100, 5, txt("Maximaler Regenabfluss (aufgerundet):"))
    pdf.cell(90, 5, f"Qr = {qr:.2f} l/s", ln=True, align='R')

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(190, 6, txt(" 2. Schmutzwasser-Berechnung (Qs)"), ln=True, fill=True)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(100, 5, txt("Gesamt Schmutzwasser (Qs):"))
    pdf.cell(90, 5, f"{qs:.2f} l/s", ln=True, align='R')

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(190, 6, txt(" 3. Faktoren und Anlagentyp (DIN 1999-100)"), ln=True, fill=True)
    pdf.set_font("Arial", '', 7.5)
    pdf.multi_cell(190, 3.5, txt(f"Anlagentyp: {at} | fx={fx} (Erschwernisfaktor) | fd={fd} (Dichte {dichte}) | ff={ff} (FAME {fame})."))

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(190, 6, txt(" 4. Ergebnis Nenngröße (NS)"), ln=True, fill=True)
    pdf.set_font("Arial", 'B', 9.5)
    pdf.cell(100, 7, txt(" Erforderliche Nenngröße:"))
    pdf.cell(90, 7, f"NS {ns:.2f}", ln=True, align='R')
    pdf.set_font("Arial", '', 7.5)
    pdf.multi_cell(190, 3.5, txt("Sichert die notwendige Verweilzeit gemaess DIN EN 858-2 zur Abscheidung von Leichtfluessigkeiten."))

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(190, 6, txt(" 5. Schlammfangvolumen (V)"), ln=True, fill=True)
    pdf.set_font("Arial", 'B', 9.5)
    pdf.cell(100, 7, txt(" Gewähltes Schlammvolumen:"))
    pdf.cell(90, 7, f"{v_final:.2f} Liter", ln=True, align='R')
    pdf.set_font("Arial", '', 7.5)
    pdf.multi_cell(190, 3.5, txt(f"Berechnung: (Faktor {sf_faktor}% * NS) / fd. Bewertungsgrundlage: {bew_t}."))
    
    return pdf.output(dest='S').encode('latin-1')

if kunden_name and kunden_strasse and kunden_ort:
    pdf_bytes = create_pdf()
    st.download_button(label="📄 PDF Protokoll herunterladen", data=pdf_bytes, file_name=f"Bemessung_{kunden_name}.pdf", mime="application/pdf")
else:
    st.info("Bitte Kundendaten eingeben, um das PDF zu aktivieren.")
