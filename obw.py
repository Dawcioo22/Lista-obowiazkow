import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import cloudinary
import cloudinary.uploader

# 1. Konfiguracja strony
st.set_page_config(page_title="obowiazki ;)", page_icon="🏠")

# 2. Konfiguracja Cloudinary
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"],
    secure = True
)

st.title("Obowiazki Grynhagelkow :)")

# 3. Połączenie z Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. Funkcja do zdjęć (Cloudinary)
def upload_to_cloudinary(image_file):
    try:
        # Wysyłamy zdjęcie
        upload_result = cloudinary.uploader.upload(image_file)
        # Zwracamy bezpośredni link do pliku
        return upload_result['secure_url']
    except Exception as e:
        return f"Błąd Cloudinary: {str(e)}"

# 5. Formularz
with st.form("form_cloudinary", clear_on_submit=True):
    osoba = st.text_input("Kto?")
    zadanie = st.selectbox("obowiazek", ["Odkurzanie", "Zmywarka", "Kuchnia", "Śmieci", "Łazienka", "Inne"])
    foto = st.camera_input("Zrób zdjęcie")
    submit = st.form_submit_button("Zapisz ✅")

if submit:
    if osoba:
        with st.spinner("Przesyłam zdjęcie i zapisuję dane..."):
            try:
                # A. Zdjęcie
                foto_url = "Brak zdjęcia"
                if foto is not None:
                    foto_url = upload_to_cloudinary(foto)
                
                # B. Pobranie danych z Google
                df = conn.read(worksheet="Arkusz1", ttl=0).dropna(how="all")
                
                # C. Czas i Tydzień
                teraz = datetime.now()
                nr_tygodnia = teraz.strftime("%V")
                etykieta_tygodnia = f"Tydzień {nr_tygodnia} ({teraz.year})"
                
                # D. Formuła IMAGE dla Excela
                # Jeśli link jest poprawny, tworzymy formułę, w przeciwnym razie wpisujemy tekst błędu
                foto_dla_excela = f'=IMAGE("{foto_url}")' if "http" in foto_url else foto_url

                # E. Nowy wpis
                nowy_wpis = pd.DataFrame({
                    "Data": [teraz.strftime("%Y-%m-%d %H:%M")],
                    "Osoba": [osoba.strip().capitalize()],
                    "Zadanie": [zadanie],
                    "Zdjęcie": [foto_dla_excela],
                    "Tydzień": [etykieta_tygodnia]
                })
                
                df_final = pd.concat([df, nowy_wpis], ignore_index=True)
                conn.update(worksheet="Arkusz1", data=df_final)
                
                st.success("Zapisano pomyślnie!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Wystąpił błąd: {e}")
    else:
        st.warning("Podaj imię!")

# 6. Podgląd ostatnich zadań
st.divider()
st.subheader("📋 Ostatnio wykonane")
try:
    data_hist = conn.read(worksheet="Arkusz1", ttl=0).dropna(how="all")
    if not data_hist.empty:
        # W aplikacji pokazujemy linki, bo Streamlit nie obsłuży formuły =IMAGE() z Excela
        st.dataframe(
            data_hist.iloc[::-1].head(10), 
            use_container_width=True,
            hide_index=True
        )
except:
    st.info("Brak danych.")
