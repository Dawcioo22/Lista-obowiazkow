import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import cloudinary
import cloudinary.uploader

# 1. Konfiguracja strony
st.set_page_config(page_title="obowiazki :o", page_icon="🏠")

# 2. Konfiguracja Cloudinary (pobierane z Secrets)
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"],
    secure = True
)

st.title("Obowiazki Grynhagelkow")

# 3. Połączenie z Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. Funkcja do przesyłania zdjęć na Cloudinary
def upload_to_cloudinary(image_file):
    try:
        # Wysyłka pliku
        upload_result = cloudinary.uploader.upload(image_file)
        # Zwrócenie bezpośredniego adresu URL (czysty link)
        return upload_result['secure_url']
    except Exception as e:
        return f"Błąd Cloudinary: {str(e)}"

# 5. Formularz wprowadzania danych
with st.form("form_final", clear_on_submit=True):
    osoba = st.text_input("Kto?")
    zadanie = st.selectbox("obowiazek", ["Odkurzanie", "Zmywarka", "Kuchnia", "Śmieci", "Łazienka", "Inne"])
    foto = st.camera_input("Zrób zdjęcie (dowód)")
    submit = st.form_submit_button("Zapisz ✅")

if submit:
    if osoba:
        with st.spinner("Przesyłam dane..."):
            try:
                # A. Obsługa zdjęcia
                foto_url = "Brak zdjęcia"
                if foto is not None:
                    foto_url = upload_to_cloudinary(foto)
                
                # B. Pobranie aktualnych danych z Google Sheets (ttl=0 zapobiega nadpisywaniu)
                df = conn.read(worksheet="Arkusz1", ttl=0).dropna(how="all")
                
                # C. Obliczanie czasu i tygodnia
                teraz = datetime.now()
                data_str = teraz.strftime("%Y-%m-%d %H:%M")
                nr_tygodnia = teraz.strftime("%V")
                etykieta_tygodnia = f"Tydzień {nr_tygodnia} ({teraz.year})"
                
                # D. Przygotowanie surowego linku dla Excela (bez kłopotliwych formuł)
                # Google Sheets automatycznie zamieni czysty link HTTPS na klikalny odnośnik.
                foto_dla_excela = foto_url

                # E. Nowy wiersz
                nowy_wpis = pd.DataFrame({
                    "Data": [data_str],
                    "Osoba": [osoba.strip().capitalize()],
                    "Zadanie": [zadanie],
                    "Zdjęcie": [foto_dla_excela],
                    "Tydzień": [etykieta_tygodnia]
                })
                
                # F. Połączenie i wysyłka do Google Sheets
                df_final = pd.concat([df, nowy_wpis], ignore_index=True)
                conn.update(worksheet="Arkusz1", data=df_final)
                
                st.success("Zapisano pomyślnie! Czysty link jest już w Excelu.")
                st.balloons()
                st.rerun() 
                
            except Exception as e:
                st.error(f"Wystąpił błąd podczas zapisu: {e}")
    else:
        st.warning("Musisz wpisać imię!")

# 6. Podgląd ostatnich 10 wpisów (w aplikacji)
st.divider()
st.subheader("📋 Ostatnio dodane")
try:
    data_hist = conn.read(worksheet="Arkusz1", ttl=0).dropna(how="all")
    if not data_hist.empty:
        # Pokazujemy 10 ostatnich rekordów
        st.dataframe(
            data_hist.iloc[::-1].head(10), 
            use_container_width=True,
            hide_index=True
        )
except:
    st.info("Lista jest obecnie pusta.")
