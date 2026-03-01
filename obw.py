import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import requests
import base64

# 1. Konfiguracja strony
st.set_page_config(page_title="Lista Obowiązków", page_icon="📸", layout="centered")

st.title("Lista obowiązków Grynhagelków")
st.write("Zrób zdjęcie i zapisz wykonane zadanie.")

# 2. Połączenie z Google Sheets (korzysta z Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Funkcja pomocnicza do wysyłania zdjęcia na ImgBB
def upload_image(image_file, api_key):
    try:
        url = "https://api.imgbb.com/1/upload"
        # Konwersja zdjęcia na format base64
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        payload = {
            "key": api_key,
            "image": encoded_string,
        }
        res = requests.post(url, payload)
        if res.status_code == 200:
            return res.json()['data']['url']
        else:
            return f"Błąd ImgBB: {res.status_code}"
    except Exception as e:
        return f"Błąd przesyłania: {str(e)}"

# 4. Formularz wprowadzania danych
with st.form("formularz_glowny", clear_on_submit=True):
    osoba = st.text_input("Kto wykonał zadanie?")
    zadanie = st.selectbox("Co zostało zrobione?", [
        "Odkurzanie", 
        "Wyjmowanie zmywarki", 
        "Sprzątanie kuchni/salonu", 
        "Wyrzucenie śmieci", 
        "Mycie łazienki",
        "Inne"
    ])
    
    # Pole na zdjęcie z kamery
    foto = st.camera_input("Zrób zdjęcie (dowód wykonania)")
    
    submit = st.form_submit_button("Zapisz w dzienniku ✅")

# 5. Logika po kliknięciu przycisku
if submit:
    if osoba:
        with st.spinner("Trwa zapisywanie... Proszę czekać."):
            try:
                # A. Przesyłanie zdjęcia (jeśli zostało zrobione)
                foto_url = "Brak zdjęcia"
                if foto is not None:
                    if "imgbb_api_key" in st.secrets:
                        api_key = st.secrets["imgbb_api_key"]
                        foto_url = upload_image(foto, api_key)
                    else:
                        st.error("Brak klucza 'imgbb_api_key' w Secrets!")

                # B. POBIERANIE NAJŚWIEŻSZYCH DANYCH (ttl=0 zapobiega nadpisywaniu)
                try:
                    # Pobieramy to, co jest w arkuszu dokładnie w tej chwili
                    existing_data = conn.read(worksheet="Arkusz1", ttl=0)
                    existing_data = existing_data.dropna(how="all")
                except:
                    # Jeśli arkusz jest pusty, tworzymy strukturę
                    existing_data = pd.DataFrame(columns=["Data", "Osoba", "Zadanie", "Zdjęcie"])
                
                # C. Przygotowanie nowego wiersza
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_row = pd.DataFrame({
                    "Data": [now], 
                    "Osoba": [osoba], 
                    "Zadanie": [zadanie],
                    "Zdjęcie": [foto_url]
                })
                
                # D. Łączenie starej listy z nowym wpisem
                updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                
                # E. Wysłanie CAŁEJ listy z powrotem do Google Sheets
                conn.update(worksheet="Arkusz1", data=updated_df)
                
                st.success(f"Dobra robota {osoba}! Zadanie zostało zapisane.")
                st.balloons()
            except Exception as e:
                st.error(f"Wystąpił błąd: {e}")
    else:
        st.warning("Musisz podać imię, aby zapisać zadanie!")

# 6. Wyświetlanie historii (zawsze świeże dane dzięki ttl=0)
st.divider()
st.subheader("📊 Historia wykonanych zadań")

try:
    # Odczytujemy historię z wymuszonym odświeżaniem
    df_view = conn.read(worksheet="Arkusz1", ttl=0)
    
    if not df_view.empty:
        # Odwracamy kolejność, aby najnowsze były na górze
        st.dataframe(
            df_view.iloc[::-1], 
            use_container_width=True,
            column_config={
                "Zdjęcie": st.column_config.LinkColumn("📸 Zobacz dowód")
            }
        )
    else:
        st.info("Lista jest pusta. Dodaj pierwszy obowiązek!")
except Exception as e:
    st.info("Czekam na pierwsze dane...")

