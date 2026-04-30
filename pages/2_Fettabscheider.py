import streamlit as st
import math

st.set_page_config(page_title="Fettabscheidertool", layout="centered")

st.title("🍳 Fettabscheidertool (DIN 4040-100)")

methode = st.radio("Berechnungsweg:", ["Einrichtungsgegenstände", "Art des Betriebes (Schlachtbetrieb)"])

if methode == "Einrichtungsgegenstände":
    st.subheader("Küchenausstattung")
    s50 = st.number_input("Spülbecken DN 50 (0,8 l/s)", min_value=0)
    gsm = st.number_input("Gastro-Spülmaschine (1,5 l/s)", min_value=0)
    qs = (s50 * 0.8 + gsm * 1.5) * 0.5
else:
    st.subheader("Schlachtbetrieb: Großvieheinheiten (GV)")
    t_betr = st.number_input("Betriebszeit [h]", min_value=1, value=8)
    n_r = st.number_input("Anzahl Rinder (1,0 GV)", min_value=0)
    n_s = st.number_input("Anzahl Schweine (0,25 GV)", min_value=0)
    n_g = st.number_input("Anzahl Geflügel (0,02 GV)", min_value=0)
    
    gv_tag = (n_r * 1.0) + (n_s * 0.25) + (n_g * 0.02)
    gv_woche = gv_tag * 5 # Annahme 5 Tage
    
    if gv_woche <= 5: vm, f_st = 20, 30
    elif gv_woche <= 10: vm, f_st = 15, 35
    else: vm, f_st = 10, 40
    
    qs = (gv_tag * vm * f_st) / (t_betr * 3600)
    st.write(f"Einstufung: {gv_woche:.1f} GV/Woche (VM={vm}, F={f_st})")

st.divider()

# Faktoren
ft = st.selectbox("Temperaturfaktor ft", [1.0, 1.3])
fd = st.selectbox("Dichtefaktor fd", [1.0, 1.5])
fe = st.selectbox("Erschwerungsfaktor fe", [1.0, 1.3])

ns_raw = qs * ft * fd * fe
ns_final = next((s for s in [1, 2, 4, 7, 10, 15, 20] if s >= ns_raw), ns_raw)

st.latex(rf"NS = Q_s \cdot f_t \cdot f_d \cdot f_e = {ns_raw:.2f}")
st.success(f"### Erforderlich: NS {ns_final}")
