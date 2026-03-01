import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Konfiguracja strony
st.set_page_config(page_title="Lista Obowiązków", page_icon="✅")

# Tworzenie folderu na zdjęcia, jeśli nie istnieje
if not os.path.exists("images"):
    os.makedirs("images")

# Plik bazy danych
DB_FILE = "obowiazki_log.csv"

# Interfejs użytkownika
st.title("🏠 Monitor Obowiązków")
st.subheader("Zamelduj wykonanie zadania")

# Formularz dodawania
with st.form("formularz_zadania", clear_on_submit=True):
    osoba = st.text_input("Kto wykonał?")
    zadanie = st.selectbox("Wybierz obowiązek", [
        "Odkurzanie", 
        "Wyjmowanie zmywarki", 
        "Sprzątanie kuchni i salonu", 
        "Wyrzucanie śmieci", 
        "Inne"
    ])
    
    # Obsługa aparatu / pliku
    zdjecie = st.camera_input("Zrób zdjęcie potwierdzające")
    
    submit = st.form_submit_button("Wyślij raport")

if submit:
    if osoba and zdjecie:
        # Zapisywanie zdjęcia
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_path = f"images/{timestamp}_{osoba}.jpg"
        with open(img_path, "wb") as f:
            f.write(zdjecie.getbuffer())
        
        # Zapisywanie danych do CSV
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nowy_wpis = pd.DataFrame([[now, osoba, zadanie, img_path]], 
                                columns=["Data", "Osoba", "Zadanie", "Sciezka_Foto"])
        
        if not os.path.isfile(DB_FILE):
            nowy_wpis.to_csv(DB_FILE, index=False)
        else:
            nowy_wpis.to_csv(DB_FILE, mode='a', header=False, index=False)
            
        st.success(f"Brawo {osoba}! Zadanie '{zadanie}' zostało zapisane.")
    else:
        st.error("Proszę podać imię i zrobić zdjęcie!")

# Wyświetlanie historii
st.divider()
st.subheader("📜 Historia wykonanych zadań")
if os.path.exists(DB_FILE):
    df = pd.read_csv(DB_FILE)
    for index, row in df.iloc[::-1].iterrows(): # Wyświetlaj od najnowszych
        with st.expander(f"{row['Data']} - {row['Osoba']}: {row['Zadanie']}"):
            st.image(row['Sciezka_Foto'], use_container_width=True)
else:
    st.info("Brak wpisów w historii.")
