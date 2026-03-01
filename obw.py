import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import requests
import base64

# 1. Konfiguracja strony
st.set_page_config(page_title="lobowionski", page_icon="🏠")

st.title("Obowiązki Grynhagelków")

# 2. Połączenie
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Funkcja do zdjęć (ImgBB)
def upload_image(image_file, api_key):
    try:
        url = "https://api.imgbb.com/1/upload"
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        payload = {"key": api_key, "image": encoded_string}
        res = requests.post(url, payload)
        return res.json()['data']['url'] if res.status_code == 200 else "Błąd przesyłania"
    except:
        return "Błąd połączenia z ImgBB"

# 4. Formularz
with st.form("form_simple", clear_on_submit=True):
    osoba = st.text_input("Kto?")
    zadanie = st.selectbox("obowiązki", ["Odkurzanie", "Zmywarka", "Kuchnia", "Śmieci", "Łazienka", "Inne"])
    foto = st.camera_input("Zrób zdjęcie")
    submit = st.form_submit_button("Zapisz ✅")

if submit:
    if osoba:
        with st.spinner("Zapisuję..."):
            try:
                foto_url = "Brak zdjęcia"
                if foto is not None:
                    foto_url = upload_image(foto, st.secrets["imgbb_api_key"])
                
                # Pobranie danych (zawsze świeże)
                df = conn.read(worksheet="Arkusz1", ttl=0).dropna(how="all")
                
                # Czas i Tydzień
                teraz = datetime.now()
                nr_tygodnia = teraz.strftime("%V")
                etykieta_tygodnia = f"Tydzień {nr_tygodnia} ({teraz.year})"
                
                nowy_wpis = pd.DataFrame({
                    "Data": [teraz.strftime("%Y-%m-%d %H:%M")],
                    "Osoba": [osoba.strip().capitalize()],
                    "Zadanie": [zadanie],
                    "Zdjęcie": [foto_url],
                    "Tydzień": [etykieta_tygodnia]
                })
                
                df_final = pd.concat([df, nowy_wpis], ignore_index=True)
                conn.update(worksheet="Arkusz1", data=df_final)
                st.success(f"Zapisano w Excelu!")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd: {e}")
    else:
        st.warning("Podaj imię!")

# 5. Historia (tylko podgląd ostatnich zadań)
st.divider()
st.subheader("📋 Ostatnio wykonane")
try:
    data_hist = conn.read(worksheet="Arkusz1", ttl=0).dropna(how="all")
    if not data_hist.empty:
        # Pokazujemy 10 ostatnich wpisów dla pewności, że wszystko działa
        st.dataframe(
            data_hist.iloc[::-1].head(10), 
            use_container_width=True,
            column_config={"Zdjęcie": st.column_config.LinkColumn("📸 Dowód")},
            hide_index=True
        )
    else:
        st.info("Brak wpisów.")
except:
    st.info("Czekam na dane...")
