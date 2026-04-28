import streamlit as st
import pandas as pd

# Design-Einstellungen
st.set_page_config(page_title="Abscheider-Rechner DIN", page_icon="💧")

st.title("💧 Abscheider-Bemessung")
st.markdown("Berechnung nach **DIN 1999-100** & **DIN 4040-100**")

# Auswahl des Typs
typ = st.sidebar.selectbox("Abscheidertyp wählen", ["Leichtflüssigkeit (DIN 1999)", "Fett (DIN 4040)"])

results = {}

if typ == "Leichtflüssigkeit (DIN 1999)":
    st.header("Leichtflüssigkeitsabscheider")
    
    col1, col2 = st.columns(2)
    with col1:
        qr = st.number_input("Regenwasserabfluss Qr [l/s]", min_value=0.0, value=0.0, step=0.1)
        qs = st.number_input("Schmutzwasserabfluss Qs [l/s]", min_value=0.0, value=0.0, step=0.1)
        fx = st.number_input("Erschwerungsfaktor fx", min_value=1.0, value=1.0, step=0.1)
    with col2:
        fd = st.number_input("Dichtefaktor fd", min_value=1.0, value=1.0, step=0.05)
        ff = st.number_input("FAME-Faktor ff", min_value=1.0, value=1.0, step=0.05)
    
    # Formel: NS = (Qr + fx * Qs) * fd * ff
    ns = (qr + fx * qs) * fd * ff
    results["NS"] = round(ns, 2)
    
    st.subheader("Überhöhung prüfen")
    h_max = st.number_input("Max. Speicherschichtdicke h_max [m]", min_value=0.0, value=0.2, step=0.01)
    rho_l = st.number_input("Dichte der Flüssigkeit [g/cm³]", min_value=0.0, value=0.85, step=0.01)
    
    delta_h = h_max * (1 - rho_l / 1.0)
    results["Mindestüberhöhung [cm]"] = round(delta_h * 100, 2)

else:
    st.header("Fettabscheider")
    
    col1, col2 = st.columns(2)
    with col1:
        qs = st.number_input("Schmutzwasser Qs [l/s]", min_value=0.0, value=0.0, step=0.1)
        ft = st.selectbox("Temperaturfaktor ft", [1.0, 1.3], help="1.3 bei Abwasser > 60°C")
    with col2:
        fd = st.number_input("Dichtefaktor fd", value=1.0, disabled=True)
        fr = st.selectbox("Reinigungsmittel fr", [1.0, 1.3, 1.5], help="1.3 bei Spülmitteleinsatz")
    
    # Formel: NS = Qs * ft * fd * fr
    ns = qs * ft * fd * fr
    results["NS"] = round(ns, 2)

# Schlammfang (für beide)
st.divider()
st.header("Schlammfangvolumen")
last = st.radio("Schlammanfall", ["Gering (100*NS)", "Mittel (200*NS)", "Groß (300*NS)"], index=1)

factor = 100 if "Gering" in last else 300 if "Groß" in last else 200
v_sf = factor * results["NS"]

# Mindestvolumen Regel
if "Mittel" in last and results["NS"] <= 3:
    v_sf = max(v_sf, 600)

results["Schlammfang [Liter]"] = round(v_sf, 2)

# Anzeige der Ergebnisse
st.success(f"### Berechnete Nenngröße: NS {results['NS']}")
st.metric("Schlammfangvolumen", f"{results['Schlammfang [Liter]']} Liter")
if "Mindestüberhöhung [cm]" in results:
    st.metric("Erforderliche Überhöhung", f"{results['Mindestüberhöhung [cm]']} cm")

# Export-Button
if st.button("Als CSV speichern"):
    df_export = pd.DataFrame([results])
    st.download_button("Datei herunterladen", df_export.to_csv(index=False), "bemessung.csv", "text/csv")