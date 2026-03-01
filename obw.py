import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import requests
import base64

# 1. Konfiguracja strony
st.set_page_config(page_title="łobowionski", page_icon="🏠", layout="wide")

st.title("Obowiązki Grynhagelków :)")

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

# 4. Formularz (w kolumnie dla lepszego wyglądu)
col_form, col_empty = st.columns([2, 1])
with col_form:
    with st.form("form_v3", clear_on_submit=True):
        osoba = st.text_input("Kto?")
        zadanie = st.selectbox("obowiązek", ["Odkurzanie", "Zmywarka", "Kuchnia", "Śmieci", "Łazienka", "Inne"])
        foto = st.camera_input("Zrób zdjęcie")
        submit = st.form_submit_button("Zapisz ✅")

if submit:
    if osoba:
        with st.spinner("Zapisuję..."):
            try:
                foto_url = "Brak zdjęcia"
                if foto is not None:
                    foto_url = upload_image(foto, st.secrets["imgbb_api_key"])
                
                try:
                    df = conn.read(worksheet="Arkusz1", ttl=0).dropna(how="all")
                except:
                    df = pd.DataFrame(columns=["Data", "Osoba", "Zadanie", "Zdjęcie", "Tydzień"])
                
                teraz = datetime.now()
                data_tylko_dzien = teraz.strftime("%Y-%m-%d")
                data_pelna = teraz.strftime("%Y-%m-%d %H:%M")
                nr_tygodnia = teraz.strftime("%V")
                rok = teraz.year
                etykieta_tygodnia = f"Tydzień {nr_tygodnia} ({rok})"
                
                nowy_wpis = pd.DataFrame({
                    "Data": [data_pelna],
                    "Osoba": [osoba.capitalize()], # Automatycznie wielka litera
                    "Zadanie": [zadanie],
                    "Zdjęcie": [foto_url],
                    "Tydzień": [etykieta_tygodnia]
                })
                
                df_final = pd.concat([df, nowy_wpis], ignore_index=True)
                conn.update(worksheet="Arkusz1", data=df_final)
                st.success(f"Zapisano!")
                st.rerun() # Odśwież stronę, żeby od razu pokazać statystyki
            except Exception as e:
                st.error(f"Błąd: {e}")
    else:
        st.warning("Podaj imię!")

# 5. Sekcja Statystyk i Historii
st.divider()
try:
    data_hist = conn.read(worksheet="Arkusz1", ttl=0).dropna(how="all")
    
    if not data_hist.empty:
        # Wybór tygodnia
        tygodnie = sorted(data_hist["Tydzień"].unique(), reverse=True)
        wybrany_tydzien = st.selectbox("📅 Wybierz tydzień do podglądu:", tygodnie)
        
        # Filtrowanie danych pod tydzień
        df_filtered = data_hist[data_hist["Tydzień"] == wybrany_tydzien].copy()
        
        # Tworzymy dwie kolumny: lewa na statystyki, prawa na historię
        col_stats, col_table = st.columns([1, 2])
        
        with col_stats:
            st.subheader("Ranking Dzienny ")
            # Wyciągamy samą datę z kolumny Data (pierwsze 10 znaków: RRRR-MM-DD)
            df_filtered['Dzień'] = df_filtered['Data'].str[:10]
            
            # Tworzymy tabelę podsumowującą: Kto | Dzień | Ile razy
            ranking = df_filtered.groupby(['Dzień', 'Osoba']).size().reset_index(name='Ilość')
            ranking = ranking.sort_values(by=['Dzień', 'Ilość'], ascending=[False, False])
            
            st.dataframe(ranking, use_container_width=True, hide_index=True)
            
            # Małe podsumowanie ogólne tygodnia
            total_tasks = len(df_filtered)
            st.metric("Suma zadań w tygodniu", total_tasks)

        with col_table:
            st.subheader("📋 Szczegółowa Lista")
            st.dataframe(
                df_filtered.iloc[::-1], 
                use_container_width=True,
                column_config={
                    "Zdjęcie": st.column_config.LinkColumn("📸 Dowód"),
                    "Tydzień": None,
                    "Dzień": None # Ukrywamy pomocniczą kolumnę
                },
                hide_index=True
            )
    else:
        st.info("Brak danych w historii.")
except Exception as e:
    st.info("Dodaj pierwsze zadanie, aby zobaczyć statystyki!")
