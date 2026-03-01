import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Konfiguracja strony
st.set_page_config(page_title="Lista Obowiązków", page_icon="🧹")

st.title("obowiązki grynhagelków")
st.write("Wypełnij formularz, aby zapisać wykonanie zadania")

# Połączenie z Arkuszem Google (wykorzystuje link z Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

# Formularz wprowadzania danych
with st.form("formularz_obowiazkow", clear_on_submit=True):
    osoba = st.text_input("Kto wykonał obowiązek?")
    zadanie = st.selectbox("Wybierz obowiązek", [
        "Odkurzanie", 
        "Wyjmowanie zmywarki", 
        "Sprzątanie kuchni i salonu", 
        "Wyrzucanie śmieci", 
        "Inne"
    ])
    
    submit = st.form_submit_button("Zapisz w tabeli ✅")

if submit:
    if osoba:
        try:
            # 1. Odczytujemy aktualne dane z zakładki "Arkusz1"
            # usecols=[0,1,2] oznacza kolumny A, B i C
            existing_data = conn.read(worksheet="Arkusz1", usecols=[0, 1, 2])
            existing_data = existing_data.dropna(how="all")
            
            # 2. Przygotowujemy nowy wiersz
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_row = pd.DataFrame({
                "Data": [now],
                "Osoba": [osoba],
                "Zadanie": [zadanie]
            })
            
            # 3. Łączymy stare dane z nowymi
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            
            # 4. Wysyłamy zaktualizowaną tabelę z powrotem do Google Sheets
            conn.update(worksheet="Arkusz1", data=updated_df)
            
            st.success(f"Dobra robota {osoba}! Zadanie zapisane.")
        except Exception as e:
            st.error(f"Wystąpił błąd podczas zapisu: {e}")
            st.info("Sprawdź, czy nazwa zakładki to na pewno 'Arkusz1' i czy masz uprawnienia Edytora.")
    else:
        st.warning("Proszę wpisać imię przed zapisaniem!")

# Wyświetlanie historii zadań pod formularzem
st.divider()
st.subheader("Historia wykonanych zadań")

try:
    # Odświeżamy widok tabeli
    df_view = conn.read(worksheet="Arkusz1")
    if not df_view.empty:
        # Pokazujemy od najnowszych (odwrócona kolejność)
        st.dataframe(df_view.iloc[::-1], use_container_width=True)
    else:
        st.info("Tabela jest pusta. Czekam na pierwszy wpis!")
except:
    st.info("Nie udało się jeszcze wczytać danych. Zrób pierwszy wpis!")
