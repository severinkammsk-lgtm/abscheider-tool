import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io
import math
from geopy.geocoders import Nominatim

# 1. Seiteneinstellungen
st.set_page_config(page_title="Abscheider-Bemessung PRO", layout="centered")

# Geocoding Hilfsfunktion
def get_coords(address):
    try:
        geolocator = Nominatim(user_agent="abscheider_app")
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        return None, None
    except:
        return None, None

# 2. CSS: Optimierung für fette Ergebnisse und saubere Eingabe
st.markdown("""
    <style>
    input[::-webkit-outer-spin-button],
    input[::-webkit-inner-spin-button] { -webkit-appearance: none !important; margin: 0 !important; }
    input[type=number] { -moz-appearance: textfield !important; }
    .stNumberInput div div input { text-align: center !important; font-size: 18px !important; }
    </style>
""", unsafe_allow_html=True)

# Hilfsfunktionen
def calc_valve_flow(count, values):
    res = 0.0
    for i in range(count):
        if i == 0: res += values[0]
        elif i == 1: res += values[1]
        elif i == 2: res += values[2]
        elif i == 3: res += values[3]
        else: res += values[4]
    return res

def get_next_standard_ns(val):
    standards = [3, 6, 8, 10, 15, 20, 30, 40, 50, 65, 80, 100]
    for s in standards:
        if s >= val: return s
    return val

# --- PROJEKTDATEN ---
st.title("📋 Abscheider-Bemessung (DIN 1999-100)")
kunden_name = st.text_input("Name Kunde", placeholder="Vollständiger Name")

# Adressfelder untereinander
kunden_strasse = st.text_input("Straße, Hausnummer", placeholder="Musterstraße 1")
kunden_ort = st.text_input("Postleitzahl, Ort", placeholder="12345 Musterstadt")

st.divider()

# --- 1. REGENABFLUSS ---
st.header("1. Regenabfluss (Qr)")

# KOSTRA-DWD Integration mit kombinierter Adresse
with st.expander("📍 Regenspende über Adresse ermitteln (KOSTRA-DWD)"):
    st.write("Suche den Standort, um den passenden KOSTRA-Link zu generieren.")
    # Kombiniert Straße und Ort für eine präzise Suche
    default_search = f"{kunden_strasse}, {kunden_ort}".strip(", ")
    search_addr = st.text_input("Standort für KOSTRA-Abfrage", value=default_search)
    
    if search_addr:
        lat, lon = get_coords(search_addr)
        if lat:
            kostra_url = f"https://www.openko.de/maps/kostra_dwd_2020.html#15/{lat}/{lon}"
            st.success(f"Standort gefunden: {lat:.4f}, {lon:.4f}")
            st.markdown(f"[👉 **KOSTRA-Daten für diesen Standort auf OpenKO.de öffnen**]({kostra_url})")
            st.info("Hinweis: Bitte trage den dort ermittelten Wert für die Regenspende unten manuell ein.")
        else:
            st.warning("Adresse konnte nicht genau aufgelöst werden. Bitte manuell prüfen.")

r_spende = st.number_input("Regenspende [l/(s * ha)]", value=300.0, format="%.1f")

# --- Flächenberechnung ---
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

dichte = st.selectbox("Dichte der Leichtflüssigkeit (g/cm³)", ["bis 0,85", "0,85 - 0,90", "0,90 - 0,95"])
with st.expander("ℹ️ Hilfe zur Auswahl der Dichte"):
    st.markdown("Dichte bestimmt Faktor **fd**: Bis 0,85 (Benzin/Diesel), 0,85-0,90 (Biodiesel RME), 0,90-0,95 (Schweröle).")

fd_map = {"bis 0,85": 1.0, "0,85 - 0,90": {t1: 2.0, t2: 1.5, t3: 1.0}, "0,90 - 0,95": {t1: 3.0, t2: 2.0, t3: 1.0}}
fd = fd_map[dichte] if dichte == "bis 0,85" else fd_map[dichte][at]

fame = st.selectbox("Biodiesel (FAME)", ["bis 5 %", "über 5 - 10 %", "über 10 %"])
with st.expander("ℹ️ Hilfe zur Auswahl des Bio-Anteils"):
    st.markdown("Bis 5% (Super E5), 5-10% (Diesel B7, Super E10), über 10% (B20/B100).")

ff_map = {"bis 5 %": {t1: 1.25, t2: 1.0, t3: 1.0}, "über 5 - 10 %": {t1: 1.50, t2: 1.25, t3: 1.0}, "über 10 %": {t1: 1.75, t2: 1.50, t3: 1.25}}
ff = ff_map[fame][at]

st.divider()

# --- 4. ERGEBNIS NENNGRÖSSE ---
st.header("4. Ergebnis Nenngröße")
ns_raw = (qr + fx * qs) * fd * ff
ns = math.ceil(ns_raw * 100) / 100 
standard_ns = get_next_standard_ns(ns)

# Rechenformel als LaTeX gemäß Anweisung
st.latex(rf"NS = ({qr:.2f} + {fx} \cdot {qs:.2f}) \cdot {fd} \cdot {ff} = {ns:.2f}")
st.success(f"### Erforderliche Nenngröße: **NS {ns:.2f}**")

st.divider()

# --- 5. SCHLAMMFANGVOLUMEN ---
st.header("5. Schlammfangvolumen")
anfall_opt = {"Kein 0%": 0, "Gering 100%": 100, "Mittel 200%": 200, "Groß 300%": 300}
selection = st.radio("Schlammanfall auswählen:", list(anfall_opt.keys()), index=0)
sf_faktor = anfall_opt[selection]
v_final = (sf_faktor * ns) / fd if (fd > 0 and sf_faktor > 0) else 0.0

bew_map = {0: "Kondensat", 100: "Geringer Schmutzanfall", 200: "Werkstätten, Fahrzeugabstellflächen", 300: "Waschplätze, Baumaschinen"}
st.info(f"**Bewertung:** {bew_map[sf_faktor]}")
st.metric("Erforderliches Volumen", f"{v_final:.2f} Liter")

st.divider()

# --- PDF GENERIERUNG ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    def txt(s): return s.encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt("BEMESSUNGSPROTOKOLL: ABSCHEIDERANLAGE"), ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 6, txt("Gemäß DIN 1999-100 / DIN EN 858-2"), ln=True, align='C')
    pdf.ln(10)
    
    # Projektdaten im PDF
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt(" 1. Projektinformationen"), ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    for label, val in [("Kunde:", kunden_name), ("Anschrift:", kunden_strasse), ("Ort:", kunden_ort), ("Datum:", datetime.now().strftime('%d.%m.%Y'))]:
        pdf.cell(40, 8, txt(label), border='B')
        pdf.cell(150, 8, txt(f" {val if val else '---'}"), border='B', ln=True)
    
    # ... Restliche PDF-Logik ...
    return pdf.output(dest='S').encode('latin-1')

if kunden_name and kunden_strasse and kunden_ort:
    pdf_bytes = create_pdf()
    st.download_button(label="📄 PDF Protokoll herunterladen", data=pdf_bytes, file_name=f"Bemessung_{kunden_name}.pdf", mime="application/pdf")
else:
    st.info("Bitte Kundendaten eingeben, um das PDF zu aktivieren.")
