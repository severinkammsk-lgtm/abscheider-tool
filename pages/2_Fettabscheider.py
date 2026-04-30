import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io
import math

# 1. Seiteneinstellungen
st.set_page_config(page_title="Fettabscheider-Bemessung PRO", layout="centered")

# 2. CSS für die Optik
st.markdown("""
    <style>
    input[::-webkit-outer-spin-button],
    input[::-webkit-inner-spin-button] { -webkit-appearance: none !important; margin: 0 !important; }
    input[type=number] { -moz-appearance: textfield !important; }
    .stNumberInput div div input { text-align: center !important; font-size: 18px !important; }
    </style>
""", unsafe_allow_html=True)

# Hilfsfunktion für Nenngrößen-Standards (Fett)
def get_next_ns_fett(val):
    standards = [1, 2, 4, 7, 10, 15, 20, 25]
    for s in standards:
        if s >= val: return s
    return val

# --- PROJEKTDATEN ---
st.title("🍳 Fettabscheider-Bemessung (DIN 4040-100)")
kunden_name = st.text_input("Name Projekt / Kunde", placeholder="Vollständiger Name")
kunden_strasse = st.text_input("Straße und Hausnummer", placeholder="Musterstraße 1")
kunden_ort = st.text_input("PLZ und Ort", placeholder="12345 Musterstadt")

st.divider()

# --- 1. SCHMUTZWASSER (Qs) ---
st.header("1. Schmutzwasseranfall (Qs)")

methode = st.radio("Berechnungsgrundlage wählen:", ["Küchenbetrieb (Einrichtungsgegenstände)", "Fleischverarbeitungsbetrieb"])

qs = 0.0

if methode == "Küchenbetrieb (Einrichtungsgegenstände)":
    st.subheader("Ermittlung nach Ausstattung")
    with st.expander("ℹ️ Hilfe: Abflusswerte (qi) pro Einrichtung"):
        st.markdown("""
        Die Werte basieren auf **DIN EN 1825-2 (Tabelle 1)**:
        *   **Spülbecken (DN 50):** 0,8 l/s
        *   **Großküchen-Spülmaschine:** 1,5 l/s (Pauschalwert)
        *   **Kippbratpfanne:** 1,0 l/s
        *   **Kippkessel:** 2,0 l/s
        *   **Bodenablauf (DN 70):** 1,5 l/s
        """)
    
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        n_spuele = st.number_input("Spülbecken (DN 50)", min_value=0, step=1)
        n_spuelm = st.number_input("Großküchen-Spülmaschine", min_value=0, step=1)
        n_boden = st.number_input("Bodenabläufe (DN 70 / 100)", min_value=0, step=1)
    with col_k2:
        n_kessel = st.number_input("Kippkessel", min_value=0, step=1)
        n_pfanne = st.number_input("Kippbratpfanne", min_value=0, step=1)

    # Berechnung Qs = Summe(qi * n) * Gleichzeitigkeitsfaktor
    sum_qi = (n_spuele * 0.8) + (n_spuelm * 1.5) + (n_boden * 1.5) + (n_kessel * 2.0) + (n_pfanne * 1.0)
    
    # Gleichzeitigkeitsfaktor n (vereinfacht nach DIN EN 1825-2)
    gleichzeitigkeit = 0.5 if sum_qi > 0 else 0.0
    qs = sum_qi * gleichzeitigkeit
    st.info(f"Berechneter Spitzenabfluss **Qs = {qs:.2f} l/s** (Gleichzeitigkeit: 0,5)")

else:
    st.subheader("Fleischverarbeitungsbetrieb")
    art = st.radio("Art der Fleischverarbeitung:", ["Schlächterei / Zerlegung (ohne Wurst)", "Wurstherstellung / Fleischwarenfabriken"])
    
    with st.expander("ℹ️ Info zur Bemessung bei Fleischverarbeitung"):
        st.markdown("""
        Die Bemessung erfolgt hier über die Menge der verarbeiteten Einheiten (Großvieheinheiten GVE).
        *   **Ohne Wurst:** Geringerer Fettanfall pro Einheit.
        *   **Mit Wurst:** Höherer Fettanfall durch Kochen, Pökeln und Räuchern.
        """)
    
    gve_pro_tag = st.number_input("Anzahl Großvieheinheiten (GVE) pro Tag", min_value=0, step=1)
    
    # Vereinfachte normative Berechnung: (GVE * Liter) / (Arbeitszeit in s)
    # Faktor: Ohne Wurst ca. 5 l/s Spitzenlast-Äquivalent | Mit Wurst ca. 7 l/s
    faktor = 5.0 if "ohne Wurst" in art else 7.0
    qs = (gve_pro_tag * faktor) / 8 / 3.6  # Annahme 8h Betrieb, Umrechnung auf l/s
    st.info(f"Berechneter Spitzenabfluss **Qs = {qs:.2f} l/s**")

st.divider()

# --- 2. FAKTOREN ---
st.header("2. Faktoren")
col_f1, col_f2 = st.columns(2)

with col_f1:
    temp_wahl = st.selectbox("Wassertemperatur (ft)", ["bis 60°C", "über 60°C"])
    ft = 1.0 if temp_wahl == "bis 60°C" else 1.3
    
    dichte_wahl = st.selectbox("Dichte des Fettes (fd)", ["<= 0,94 g/cm³", "> 0,94 g/cm³"])
    fd = 1.0 if "<=" in dichte_wahl else 1.5

with col_f2:
    emul = st.selectbox("Einsatz von Reinigungsmitteln (fe)", ["Ja (reinigungsmittelempfindlich)", "Nein (rein mechanisch)"])
    fe = 1.3 if "Ja" in emul else 1.0
    st.caption("Reinigungsmittel/Emulgatoren erschweren die Fettabscheidung, daher wird der Faktor 1,3 gewählt.")

st.divider()

# --- 3. ERGEBNIS NS ---
st.header("3. Ergebnis Nenngröße")
# Formel: NS = Qs * ft * fd * fe
ns_raw = qs * ft * fd * fe
ns_standard = get_next_ns_fett(ns_raw)

st.latex(rf"NS = {qs:.2f} \cdot {ft} \cdot {fd} \cdot {fe} = {ns_raw:.2f}")
st.success(f"### Erforderliche Nenngröße: **NS {ns_standard}**")

st.divider()

# --- 4. SCHLAMMFANG ---
st.header("4. Schlammfangvolumen")

# Schlammfang-Faktor: 100*NS für Küchen, 200*NS für Fleischverarbeitung
sf_faktor = 200 if methode == "Fleischverarbeitungsbetrieb" else 100
v_min = ns_standard * sf_faktor

st.info(f"**Einstufung:** {'Großer Schlammanfall (Fleischverarbeitung)' if sf_faktor == 200 else 'Mittlerer Schlammanfall (Küche)'}")
st.metric("Erforderliches Mindestvolumen V", f"{v_min} Liter")

st.divider()

# --- PDF GENERIERUNG ---
def create_pdf_fett():
    pdf = FPDF()
    pdf.add_page()
    def t(s): return s.encode('latin-1', 'replace').decode('latin-1')

    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, t("BEMESSUNGSPROTOKOLL: FETTABSCHEIDER"), ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 6, t("Gemäß DIN 4040-100 / DIN EN 1825-2"), ln=True, align='C')
    pdf.ln(10)
    
    # Projektdaten
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, t(" 1. Projektinformationen"), ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    for label, val in [("Kunde:", kunden_name), ("Anschrift:", kunden_strasse), ("Ort:", kunden_ort)]:
        pdf.cell(40, 8, t(label), border='B')
        pdf.cell(150, 8, t(f" {val if val else '---'}"), border='B', ln=True)
    pdf.ln(5)
    
    # Schmutzwasser
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, t(" 2. Schmutzwasser (Qs)"), ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(190, 7, t(f"Methode: {methode}\nBerechneter Spitzenabfluss Qs: {qs:.2f} l/s"))
    pdf.ln(3)

    # Faktoren & Ergebnis
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, t(" 3. Faktoren & Nenngröße"), ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 7, t(f"Temperaturfaktor ft: {ft} | Dichtefaktor fd: {fd} | Erschwernisfaktor fe: {fe}"), ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(100, 10, t(" ERFORDERLICHE NENNGRÖSSE:"))
    pdf.cell(90, 10, f"NS {ns_standard}", ln=True, align='R')
    pdf.ln(5)

    # Schlammfang
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, t(" 4. Schlammfangvolumen"), ln=True, fill=True)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 10, t(" MINDESTVOLUMEN V:"))
    pdf.cell(90, 10, f"{v_min} Liter", ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1')

if kunden_name and kunden_strasse and kunden_ort:
    pdf_bytes = create_pdf_fett()
    st.download_button(label="📄 PDF Protokoll herunterladen", data=pdf_bytes, file_name=f"Fettabscheider_{kunden_name}.pdf", mime="application/pdf")
else:
    st.info("Bitte Projektdaten eingeben, um das PDF zu aktivieren.")
