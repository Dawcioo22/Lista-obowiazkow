import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Lista Obowiązków", page_icon="🧹")

st.title("obowiazki grynhagelkow")

# Połączenie
conn = st.connection("gsheets", type=GSheetsConnection)

# Formularz
with st.form("formularz", clear_on_submit=True):
    osoba = st.text_input("Kto wykonał?")
    zadanie = st.selectbox("Obowiązek", ["Odkurzanie", "Zmywarka", "Kuchnia", "Śmieci", "Inne"])
    submit = st.form_submit_button("Zapisz ✅")

if submit:
    if osoba:
        try:
            # Pobieramy dane (jeśli arkusz jest pusty, tworzymy pusty DataFrame)
            try:
                existing_data = conn.read(worksheet="Arkusz1")
            except:
                existing_data = pd.DataFrame(columns=["Data", "Osoba", "Zadanie"])
            
            # Nowy wpis
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_row = pd.DataFrame({"Data": [now], "Osoba": [osoba], "Zadanie": [zadanie]})
            
            # Łączymy i czyścimy puste wiersze
            updated_df = pd.concat([existing_data, new_row], ignore_index=True).dropna(how="all")
            
            # ZAPIS - to tutaj zwykle jest błąd 400
            conn.update(worksheet="Arkusz1", data=updated_df)
            
            st.success("Zapisano pomyślnie!")
            st.balloons() # Efekt świętowania!
        except Exception as e:
            st.error(f"Błąd zapisu: {e}")
    else:
        st.warning("Wpisz imię!")

# Wyświetlanie tabeli
st.divider()
st.subheader("📊 Historia")
try:
    data = conn.read(worksheet="Arkusz1")
    st.dataframe(data.iloc[::-1], use_container_width=True)
except:
    st.info("Brak danych do wyświetlenia.")

