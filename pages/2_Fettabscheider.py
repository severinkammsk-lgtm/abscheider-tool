import streamlit as st
import math

st.set_page_config(page_title="Fettabscheider-Experte", layout="centered")

st.title("🍳 Fettabscheidertool PRO (DIN 4040-100)")

# --- PROJEKTDATEN ---
with st.container():
    kunden_name = st.text_input("Name Projekt / Kunde")
    col_adr1, col_adr2 = st.columns(2)
    with col_adr1: strasse = st.text_input("Straße / Hausnummer")
    with col_adr2: ort = st.text_input("PLZ / Ort")

st.divider()

# --- BEMESSUNGSGRUNDLAGE ---
st.header("1. Ermittlung des Abflusses (Qs)")
methode = st.radio("Berechnungsweg wählen:", 
                   ["Nach Einrichtungsgegenständen", "Nach Art des Betriebes (Mahlzeiten/GVE)"])

qs = 0.0

if methode == "Nach Einrichtungsgegenständen":
    st.subheader("Küchenausstattung")
    with st.expander("ℹ️ Hilfe zur Spülen-Messung"):
        st.write("Messen Sie den Ablauf (DN 50 oder DN 70). Eckventile/Armaturen müssen nicht separat gezählt werden.")
    
    col1, col2 = st.columns(2)
    with col1:
        s50 = st.number_input("Spülbecken DN 50 (0,8 l/s)", min_value=0)
        s70 = st.number_input("Spülbecken DN 70/100 (1,5 l/s)", min_value=0)
        gsm = st.number_input("Gastro-Spülmaschine (1,5 l/s)", min_value=0)
        ksm = st.number_input("Kartoffelschälmaschine (1,5 l/s)", min_value=0)
    with col2:
        k100 = st.number_input("Kippkessel bis 100l (1,0 l/s)", min_value=0)
        k200 = st.number_input("Kippkessel über 100l (2,0 l/s)", min_value=0)
        kpf = st.number_input("Kippbratpfanne (1,0 l/s)", min_value=0)
        ba70 = st.number_input("Bodenablauf DN 70 (1,5 l/s)", min_value=0)
        ba100 = st.number_input("Bodenablauf DN 100 (2,0 l/s)", min_value=0)
    
    # Qs Berechnung
    sum_qi = (s50*0.8 + s70*1.5 + gsm*1.5 + ksm*1.5 + k100*1.0 + k200*2.0 + kpf*1.0 + ba70*1.5 + ba100*2.0)
    qs = sum_qi * 0.5 if sum_qi > 0 else 0.0 # Gleichzeitigkeit 0,5
    st.info(f"Spitzenabfluss **Qs = {qs:.2f} l/s**")

else:
    st.subheader("Betriebstyp & Kapazität")
    typ = st.selectbox("Betriebsart auswählen:", 
                       ["Hotel", "Restaurant", "Kantine/Mensa", "Fleischerei ohne Wurst", "Fleischerei mit Wurst"])
    
    menge = st.number_input("Anzahl Mahlzeiten/GVE pro Tag:", min_value=0)
    
    # Norm-Parameter
    params = {
        "Hotel": {"Vm": 100, "t": 24, "F": 5},
        "Restaurant": {"Vm": 50, "t": 12, "F": 5},
        "Kantine/Mensa": {"Vm": 5, "t": 2, "F": 5},
        "Fleischerei ohne Wurst": {"Vm": 200, "t": 8, "F": 20},
        "Fleischerei mit Wurst": {"Vm": 300, "t": 8, "F": 20}
    }
    
    p = params[typ]
    if menge > 0:
        qs = (menge * p["Vm"]) / (p["F"] * p["t"] * 3600)
    
    st.info(f"Berechneter Abfluss **Qs = {qs:.2f} l/s**")

st.divider()

# --- FAKTOREN & ERGEBNIS ---
st.header("2. Faktoren & Nenngröße")
col_f1, col_f2 = st.columns(2)
with col_f1:
    ft = st.selectbox("Temperaturfaktor ft", [1.0, 1.3], help="1.3 bei > 60°C")
    fd = st.selectbox("Dichtefaktor fd", [1.0, 1.5], help="1.5 bei Dichte > 0,94 g/cm³")
with col_f2:
    fe = st.selectbox("Erschwerungsfaktor fe", [1.0, 1.3], help="1.3 bei Einsatz von Spülmitteln")

ns_raw = qs * ft * fd * fe
ns_final = next((s for s in [1, 2, 4, 7, 10, 15, 20, 25] if s >= ns_raw), ns_raw)

st.latex(rf"NS = Q_s \cdot f_t \cdot f_d \cdot f_e = {ns_raw:.2f}")
st.success(f"### Empfohlene Nenngröße: **NS {ns_final}**")

# Schlammfang
sf_faktor = 200 if "Fleischerei" in methode or (methode != "Nach Einrichtungsgegenständen" and "Fleischerei" in typ) else 100
st.info(f"Erforderlicher Schlammfang: **{ns_final * sf_faktor} Liter** (Faktor {sf_faktor})")
