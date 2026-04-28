import streamlit as st
import pandas as pd

# 1. Seiteneinstellungen
st.set_page_config(page_title="Abscheider-Bemessung PRO", layout="centered")

# 2. CSS-HACK: ENTFERNT + UND - BUTTONS UND OPTIMIERT DIE EINGABE
st.markdown("""
    <style>
    /* Versteckt die Pfeile in Chrome, Safari, Edge, Opera */
    input::-webkit-outer-spin-button,
    input[::-webkit-inner-spin-button] {
        -webkit-appearance: none !important;
        margin: 0 !important;
    }
    /* Versteckt die Pfeile in Firefox */
    input[type=number] {
        -moz-appearance: textfield !important;
    }
    /* Zentriert den Text und vergrößert die Schrift für mobile Geräte */
    .stNumberInput div div input {
        text-align: center !important;
        font-size: 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- KUNDENDATEN ---
st.title("📋 Abscheider-Bemessung (DIN 1999-100)")
st.subheader("Projektdaten")
col_k1, col_k2 = st.columns(2)
with col_k1:
    kunden_name = st.text_input("Bauvorhaben / Kunde", placeholder="Name")
with col_k2:
    kunden_adresse = st.text_input("Standort", placeholder="Ort")

st.divider()

# --- 1. REGENABFLUSS (QR) ---
st.header("1. Regenabfluss (Qr)")
st.warning("Hinweis: Nur unüberdachte Flächen angeben, auf die Regen fallen kann!")

r_spende = st.number_input("Regenspende [l/(s * ha)]", value=300.0, format="%.1f")

def flaeche_zeile(label, key_suffix, wind_faktor=1.0):
    st.markdown(f"**{label}**")
    c1, c2, c3 = st.columns([3, 3, 2])
    with c1:
        l = st.number_input("Länge [m]", key=f"l_{key_suffix}", min_value=0.0, format="%.2f")
    with c2:
        b = st.number_input("Breite [m]", key=f"b_{key_suffix}", min_value=0.0, format="%.2f")
    ergebnis = l * b * wind_faktor
    with c3:
        st.markdown(f"<div style='padding-top:35px'>= <b>{ergebnis:.2f} m²</b></div>", unsafe_allow_html=True)
    return ergebnis

a_tank = flaeche_zeile("Tankfläche", "tank")
a_hof = flaeche_zeile("Hof- / Freifläche", "hof")
a_wasch = flaeche_zeile("Waschplatz (außen)", "wasch")
a_lager = flaeche_zeile("Lager- / Abstellfläche", "lager")
a_wand = flaeche_zeile("Wandfläche (Schlagregen 50%)", "wand", wind_faktor=0.5)

total_area = a_tank + a_hof + a_wasch + a_lager + a_wand
qr = (r_spende * total_area) / 10000
st.info(f"Gesamtfläche: {total_area:.2f} m² | Qr = {qr:.2f} l/s")

st.divider()

# --- 2. SCHMUTZWASSER (QS) ---
st.header("2. Schmutzwasser (Qs)")
col_s1, col_s2 = st.columns(2)
with col_s1:
    dn15 = st.number_input("Ventil DN 15 (0,5 l/s) [Anzahl]", min_value=0) * 0.5
    dn20 = st.number_input("Ventil DN 20 (1,0 l/s) [Anzahl]", min_value=0) * 1.0
    dn25 = st.number_input("Ventil DN 25 (1,7 l/s) [Anzahl]", min_value=0) * 1.7
with col_s2:
    wasch_typ = st.selectbox("Waschanlage", ["Keine", "Portalwaschanlage", "Waschstraße"])
    anz_hd = st.number_input("Anzahl HD-Reiniger", min_value=0)

is_wash_plant = wasch_typ in ["Portalwaschanlage", "Waschstraße"]
qs_w = 2.0 if is_wash_plant else 0.0
if is_wash_plant:
    qs_hd = anz_hd * 1.0
else:
    qs_hd = 2.0 + (anz_hd - 1) * 1.0 if anz_hd > 0 else 0.0

qs = dn15 + dn20 + dn25 + qs_w + qs_hd
st.info(f"Gesamt Qs = {qs:.2f} l/s")

st.divider()

# --- 3. FAKTOREN ---
st.header("3. Faktoren & Anlagentyp")
anlagentyp = st.selectbox("Gewählter Anlagentyp", ["S-II-P", "S-I-P", "S-II-I-P"])
fx = 2.0 if (a_wasch > 0 or is_wash_plant or anz_hd > 0) else 1.0

dichte = st.selectbox("Dichte (g/cm³)", ["bis 0,85", "0,85 - 0,90", "0,90 - 0,95"])
fd_map = {
    "bis 0,85": {"S-II-P": 1.0, "S-I-P": 1.0, "S-II-I-P": 1.0},
    "0,85 - 0,90": {"S-II-P": 2.0, "S-I-P": 1.5, "S-II-I-P": 1.0},
    "0,90 - 0,95": {"S-II-P": 3.0, "S-I-P": 2.0, "S-II-I-P": 1.0}
}
fd = fd_map[dichte][anlagentyp]

fame = st.selectbox("FAME-Anteil (%)", ["bis 5 %", "5 - 10 %", "über 10 %"])
ff_map = {
    "bis 5 %": {"S-II-P": 1.25, "S-I-P": 1.0, "S-II-I-P": 1.0},
    "5 - 10 %": {"S-II-P": 1.50, "S-I-P": 1.25, "S-II-I-P": 1.0},
    "über 10 %": {"S-II-P": 1.75, "S-I-P": 1.50, "S-II-I-P": 1.25}
}
ff = ff_map[fame][anlagentyp]

st.write(f"**Faktoren:** fx = {fx} | fd = {fd} | ff = {ff}")

st.divider()

# --- 4. ERGEBNIS NS ---
st.header("4. Ergebnis Nenngröße")
ns = (qr + fx * qs) * fd * ff
st.latex(rf"NS = ({qr:.2f} + {fx} \cdot {qs:.2f}) \cdot {fd} \cdot {ff} = {ns:.2f}")
st.success(f"Erforderliche Nenngröße: NS {ns:.2f}")

st.divider()

# --- 5. SCHLAMMFANGVOLUMEN ---
st.header("5. Schlammfangvolumen")

if is_wash_plant:
    v_sf = 5000.0
    st.warning("⚠️ Waschstraße / Portalwaschanlage erkannt: **Mindestschlammvolumen 5.000 Liter**")
else:
    anfall = st.radio("Erwarteter Schlammanfall auswählen:", ["Kein", "Gering", "Mittel", "Groß"], index=1)
    
    if anfall == "Kein":
        st.info("**Bewertung:** Kondensat. Kein Schlammfang erforderlich.")
        v_sf = 0.0
    elif anfall == "Gering":
        st.info("**Bewertung:** - alle Regenauffangflächen, auf denen nur geringe Mengen an Schmutz durch Straßenverkehr oder Ähnliches anfällt, z.B. Auffangtassen auf Tankfeldern und überdachten Tankstellen")
        v_sf = (100 * ns) / (fd * ff)
    elif anfall == "Mittel":
        st.info("**Bewertung:** - Tankstellen, PKW-Wäsche von Hand, Teilewäsche, Omnibus-Waschstände, Abwasser aus Reparaturwerkstätten, Fahrzeugabstellflächen, Kraftwerke, Maschinenbaubetriebe")
        # Formel: 200 * NS / fd / ff | Mindestvolumen 600l
        v
