import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
# Dane pobieramy z st.secrets (bezpieczeństwo na GitHub!)
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Supabase", layout="centered")
st.title("Zarządzanie Półproduktami 📦")

menu = ["Dodaj Kategorię", "Dodaj Półprodukt", "Widok Tabel"]
choice = st.sidebar.selectbox("Nawigacja", menu)

# --- FUNKCJE POMOCNICZE ---
def get_categories():
    response = supabase.table("kategorie").select("id, nazwa").execute()
    return response.data

# --- DODAWANIE KATEGORII ---
if choice == "Dodaj Kategorię":
    st.header("Dodaj nową kategorię")
    with st.form("form_kat", clear_on_submit=True):
        nazwa = st.text_input("Nazwa kategorii")
        opis = st.text_area("Opis (opcjonalnie)")
        submit = st.form_submit_button("Zapisz w Supabase")

        if submit and nazwa:
            data = {"nazwa": nazwa, "opis": opis}
            try:
                supabase.table("kategorie").insert(data).execute()
                st.success(f"Dodano kategorię: {nazwa}")
            except Exception as e:
                st.error(f"Błąd: {e}")

# --- DODAWANIE PÓŁPRODUKTU ---
elif choice == "Dodaj Półprodukt":
    st.header("Dodaj nowy półprodukt")
    
    # Pobierz listę kategorii do wyboru
    kategorie_data = get_categories()
    opcje_kat = {k['nazwa']: k['id'] for k in kategorie_data}

    with st.form("form_prod", clear_on_submit=True):
        nazwa_prod = st.text_input("Nazwa półproduktu")
        liczba = st.number_input("Liczba (int8)", min_value=0, step=1)
        cena = st.number_input("Cena (numeric)", min_value=0.0, format="%.2f")
        kat_nazwa = st.selectbox("Wybierz kategorię", options=list(opcje_kat.keys()))
        
        submit = st.form_submit_button("Dodaj do bazy")

        if submit and nazwa_prod:
            payload = {
                "nazwa": nazwa_prod,
                "liczba": liczba,
                "cena": cena,
                "kategoria_id": opcje_kat[kat_nazwa]
            }
            try:
                supabase.table("Półprodukt").insert(payload).execute()
                st.success(f"Produkt {nazwa_prod} został dodany!")
            except Exception as e:
                st.error(f"Błąd: {e}")

# --- WIDOK TABEL ---
elif choice == "Widok Tabel":
    st.header("Aktualna zawartość bazy")
    
    st.subheader("Półprodukty")
    prods = supabase.table("Półprodukt").select("*").execute()
    if prods.data:
        st.dataframe(prods.data)
        
    st.subheader("Kategorie")
    kats = supabase.table("kategorie").select("*").execute()
    if kats.data:
        st.dataframe(kats.data)
