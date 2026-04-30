import streamlit as st
import math

st.set_page_config(page_title="Fettabscheider-Experte", layout="centered")

st.title("🍳 Fettabscheidertool PRO (DIN 4040-100)")

# --- PROJEKTDATEN ---
kunden_name = st.text_input("Name Projekt / Kunde")
kunden_strasse = st.text_input("Straße und Hausnummer")
kunden_ort = st.text_input("PLZ und Ort")

st.divider()

# --- BEMESSUNGSGRUNDLAGE ---
st.header("1. Ermittlung des Abflusses (Qs)")
methode = st.radio("Berechnungsweg wählen:", 
                   ["Nach Einrichtungsgegenständen", "Nach Art des Betriebes (Schlachtbetrieb/Küche)"])

qs = 0.0

if methode == "Nach Einrichtungsgegenständen":
    st.subheader("Küchenausstattung")
    col1, col2 = st.columns(2)
    with col1:
        s50 = st.number_input("Spülbecken DN 50 (0,8 l/s)", min_value=0)
        s70 = st.number_input("Spülbecken DN 70/100 (1,5 l/s)", min_value=0)
        gsm = st.number_input("Gastro-Spülmaschine (1,5 l/s)", min_value=0)
    with col2:
        k100 = st.number_input("Kippkessel bis 100l (1,0 l/s)", min_value=0)
        k200 = st.number_input("Kippkessel über 100l (2,0 l/s)", min_value=0)
        ba70 = st.number_input("Bodenablauf DN 70/100 (1,5 l/s)", min_value=0)
    
    sum_qi = (s50*0.8 + s70*1.5 + gsm*1.5 + k100*1.0 + k200*2.0 + ba70*1.5)
    qs = sum_qi * 0.5 if sum_qi > 0 else 0.0 
    st.info(f"Spitzenabfluss **Qs = {qs:.2f} l/s**")

else:
    st.subheader("Nenngrößenberechnung Schlachtbetrieb")
    st.caption("Berechnung nach Art des in die Abscheideranlage entwässernden Betriebes")
    
    # Eingaben nach grafik_17.png
    t_betrieb = st.number_input("Durchschnittliche tägliche Betriebszeit [h]", min_value=1, value=8)
    
    c1, c2, c3 = st.columns(3)
    with c1: n_schwein = st.number_input("Anzahl Schweine", min_value=0, step=1)
    with c2: n_rind = st.number_input("Anzahl Rinder", min_value=0, step=1)
    with c3: n_gefluegel = st.number_input("Anzahl Geflügel", min_value=0, step=1)
    
    arbeitstage = st.slider("Arbeitstage pro Woche", 1, 7, 5)

    # GV Berechnung (1 Rind=1.0, 1 Schwein=0.25, 1 Geflügel=0.02)
    gv_tag = (n_schwein * 0.25) + (n_rind * 1.0) + (n_gefluegel * 0.02)
    gv_woche = gv_tag * arbeitstage
    gv_kg = gv_tag * 500

    # Anzeige der GV-Werte
    st.markdown(f"""
    | Einheit | Wert |
    | :--- | :--- |
    | **Tägliche Großvieheinheiten (GV):** | {gv_tag:.2f} GV |
    | **Tägliche GV in kg:** | {gv_kg:.0f} kg |
    | **Wöchentliche GV:** | {gv_woche:.2f} GV/Woche |
    """)

    # Logik für VM und F nach grafik_17.png
    if gv_woche <= 5:
        vm, f_stoß, klasse = 20, 30, "Klein (bis 5 GV/Woche)"
    elif gv_woche <= 10:
        vm, f_stoß, klasse = 15, 35, "Mittel (bis 10 GV/Woche)"
    else:
        vm, f_stoß, klasse = 10, 40, "Groß (bis 40 GV/Woche)"
    
    st.write(f"**Einstufung:** {klasse} → $V_M={vm}$, $F={f_stoß}$")

    # Qs Berechnung: (GV_Tag * VM * F) / (t * 3600)
    if gv_tag > 0:
        v_tag = gv_tag * vm
        qs = (v_tag * f_stoß) / (t_betrieb * 3600)
        st.info(f"Durchschn. tägl. Schmutzwasservolumen V = **{v_tag:.2f} l**")
        st.info(f"Maximaler Schmutzwasserabfluss **Qs = {qs:.2f} l/s**")

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
ns_standards = [1, 2, 4, 7, 10, 15, 20, 25]
ns_final = next((s for s in ns_standards if s >= ns_raw), ns_raw)

st.latex(rf"NS = Q_s \cdot f_t \cdot f_d \cdot f_e = {ns_raw:.2f}")
st.success(f"### Empfohlene Nenngröße: **NS {ns_final}**")

# Schlammfang
sf_faktor = 200 if methode == "Nach Art des Betriebes (Schlachtbetrieb/Küche)" and gv_tag > 0 else 100
st.info(f"Erforderlicher Schlammfang: **{ns_final * sf_faktor} Liter** (Faktor {sf_faktor})")
