import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import requests
import base64

# 1. Konfiguracja strony
st.set_page_config(page_title="Obowiazki Grynhagelkow", page_icon="🏠", layout="centered")

st.title("Obowiazki Grynhagelkow :)")

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
with st.form("form_v2", clear_on_submit=True):
    osoba = st.text_input("Kto wykonał?")
    zadanie = st.selectbox("Zadanie", ["Odkurzanie", "Zmywarka", "Kuchnia", "Śmieci", "Łazienka", "Inne"])
    foto = st.camera_input("Zrób zdjęcie")
    submit = st.form_submit_button("Zapisz ✅")

if submit:
    if osoba:
        with st.spinner("Zapisuję..."):
            try:
                # Zdjęcie
                foto_url = "Brak zdjęcia"
                if foto is not None:
                    foto_url = upload_image(foto, st.secrets["imgbb_api_key"])
                
                # Dane z Google (zawsze świeże)
                try:
                    df = conn.read(worksheet="Arkusz1", ttl=0).dropna(how="all")
                except:
                    df = pd.DataFrame(columns=["Data", "Osoba", "Zadanie", "Zdjęcie", "Tydzień"])
                
                # Czas i Tydzień
                teraz = datetime.now()
                data_str = teraz.strftime("%Y-%m-%d %H:%M")
                nr_tygodnia = teraz.strftime("%V") # ISO week number
                rok = teraz.year
                etykieta_tygodnia = f"Tydzień {nr_tygodnia} ({rok})"
                
                # Nowy wpis
                nowy_wpis = pd.DataFrame({
                    "Data": [data_str],
                    "Osoba": [osoba],
                    "Zadanie": [zadanie],
                    "Zdjęcie": [foto_url],
                    "Tydzień": [etykieta_tygodnia]
                })
                
                df_final = pd.concat([df, nowy_wpis], ignore_index=True)
                conn.update(worksheet="Arkusz1", data=df_final)
                
                st.success(f"Zapisano w: {etykieta_tygodnia}")
                st.balloons()
            except Exception as e:
                st.error(f"Błąd: {e}")
    else:
        st.warning("Podaj imię!")

# 5. Historia z filtrowaniem
st.divider()
st.subheader("📊 Historia i Statystyki")

try:
    data_hist = conn.read(worksheet="Arkusz1", ttl=0).dropna(how="all")
    
    if not data_hist.empty:
        # Wybór tygodnia do wyświetlenia
        tygodnie = sorted(data_hist["Tydzień"].unique(), reverse=True)
        wybrany_tydzien = st.selectbox("Filtruj historię wg tygodnia:", tygodnie)
        
        # Filtrowanie danych
        df_filtered = data_hist[data_hist["Tydzień"] == wybrany_tydzien]
        
        # Proste podsumowanie
        st.info(f"W tym tygodniu wykonano już **{len(df_filtered)}** zadań.")
        
        # Tabela
        st.dataframe(
            df_filtered.iloc[::-1], 
            use_container_width=True,
            column_config={
                "Zdjęcie": st.column_config.LinkColumn("📸 Dowód"),
                "Tydzień": None # Ukrywamy tę kolumnę w tabeli, bo i tak filtrujemy
            }
        )
    else:
        st.info("Brak danych w historii.")
except:
    st.info("Czekam na dane z arkusza...")
