# ... (Vorheriger Code-Teil bleibt gleich)

# --- 2. SCHMUTZWASSER ---
st.header("2. Schmutzwasser (Qs)")

# NEU: Erklärungsblock für die richtige Messung
with st.expander("⚠️ Wichtig: Wie messe ich die Ventildimension richtig?"):
    st.markdown("""
    Bitte messen Sie **nicht** die Schlauchverschraubung am Auslauf. Diese ist baubedingt immer **eine Dimension größer** als das eigentliche Ventil. 
    
    Orientieren Sie sich am **Anschlussgewinde zur Wand** oder der eingestanzten Zahl am Gehäuse:
    """)
    
    # Tabelle zur Klarheit
    st.table({
        "Ventil-Nenngröße (Eingang)": ["DN 15 (1/2\")", "DN 20 (3/4\")", "DN 25 (1\")"],
        "Schlauchanschluss (Ausgang)": ["3/4\"", "1\"", "1 1/4\""],
        "Typische Verwendung": ["Standard Zapfhahn", "Großer Wandhydrant", "Industrieanschluss"]
    })

col_s1, col_s2 = st.columns(2)
with col_s1:
    # Beschriftungen inkl. Zoll-Maßen
    v15_c = st.number_input("Anzahl Ventile DN 15 (1/2\")", min_value=0, step=1)
    v20_c = st.number_input("Anzahl Ventile DN 20 (3/4\")", min_value=0, step=1)
    v25_c = st.number_input("Anzahl Ventile DN 25 (1\")", min_value=0, step=1)

# ... (Rest des Codes zur Berechnung von Qs1_total, Waschanlage etc. bleibt gleich)
