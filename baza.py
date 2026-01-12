import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- KONFIGURACJA POŁĄCZENIA ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

st.set_page_config(page_title="Magazyn Supabase", layout="wide")
st.title("System Zarządzania Magazynem 📦")

# --- FUNKCJE POBIERANIA DANYCH ---
def get_categories():
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return res.data

def get_products():
    res = supabase.table("Półprodukt").select("nazwa, liczba, cena, kategorie(nazwa)").execute()
    return res.data

# --- GŁÓWNA NAWIGACJA (TABS) ---
tab_dashboard, tab_produkty, tab_kategorie = st.tabs([
    "📊 Statystyki i Wykresy", 
    "🔨 Zarządzanie Produktami", 
    "📁 Kategorie"
])

# --- ZAKŁADKA 1: STATYSTYKI I WYKRESY ---
with tab_dashboard:
    st.header("Analityka Magazynowa")
    data = get_products()
    
    if data:
        df = pd.DataFrame(data)
        if 'kategorie' in df.columns:
            df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Ilość produktów")
            st.bar_chart(df.set_index("nazwa")["liczba"])
            
        with col2:
            st.subheader("Wartość zapasów (PLN)")
            df['wartosc'] = df['liczba'] * df['cena']
            st.area_chart(df.set_index("nazwa")["wartosc"])

        st.subheader("Podgląd wszystkich danych")
        st.dataframe(df[["nazwa", "liczba", "cena", "kategoria_nazwa"]], use_container_width=True)
    else:
        st.info("Brak produktów w bazie.")

# --- ZAKŁADKA 2: ZARZĄDZANIE PRODUKTAMI ---
with tab_produkty:
    st.header("Zarządzanie Półproduktami")
    kategorie_data = get_categories()
    
    if not kategorie_data:
        st.warning("Najpierw dodaj kategorię w sekcji 'Kategorie'!")
    else:
        opcje_kat = {k['nazwa']: k['id'] for k in kategorie_data}
        
        with st.form("form_prod", clear_on_submit=True):
            col_n, col_k = st.columns([2, 1])
            nazwa_prod = col_n.text_input("Nazwa półproduktu")
            kat_nazwa = col_k.selectbox("Kategoria", options=list(opcje_kat.keys()))
            
            c1, c2 = st.columns(2)
            liczba = c1.number_input("Ilość", min_value=0, step=1)
            cena = c2.number_input("Cena (PLN)", min_value=0.0, format="%.2f")
            
            submit = st.form_submit_button("➕ Dodaj do magazynu")
            
            if submit and nazwa_prod:
                try:
                    payload = {
                        "nazwa": nazwa_prod,
                        "liczba": liczba,
                        "cena": cena,
                        "kategoria_id": opcje_kat[kat_nazwa]
                    }
                    supabase.table("Półprodukt").insert(payload).execute()
                    st.success(f"Dodano: {nazwa_prod}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd: {e}")

# --- ZAKŁADKA 3: KATEGORIE ---
with tab_kategorie:
    col_left, col_right = st.columns(2)

    # Lewa kolumna: DODAWANIE
    with col_left:
        st.subheader("➕ Dodaj nową kategorię")
        with st.form("form_kat", clear_on_submit=True):
            nowa_kat = st.text_input("Nazwa kategorii")
            opis_kat = st.text_area("Opis")
            kat_submit = st.form_submit_button("Zapisz kategorię")
            
            if kat_submit and nowa_kat:
                try:
                    supabase.table("kategorie").insert({"nazwa": nowa_kat, "opis": opis_kat}).execute()
                    st.success("Kategoria dodana!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd: {e}")

    # Prawa kolumna: USUWANIE
    with col_right:
        st.subheader("🗑️ Usuń kategorię")
        current_kats = get_categories()
        
        if current_kats:
            delete_options = {k['nazwa']: k['id'] for k in current_kats}
            kat_to_del_name = st.selectbox("Wybierz kategorię do usunięcia", options=list(delete_options.keys()))
            
            # Przycisk usuwania z dodatkowym potwierdzeniem
            if st.button("Usuń wybraną kategorię", type="primary", use_container_width=True):
                target_id = delete_options[kat_to_del_name]
                try:
                    # Próba usunięcia z bazy
                    supabase.table("kategorie").delete().eq("id", target_id).execute()
                    st.success(f"Pomyślnie usunięto kategorię: {kat_to_del_name}")
                    st.rerun()
                except Exception as e:
                    st.error("Nie można usunąć! Ta kategoria prawdopodobnie zawiera przypisane produkty. Najpierw usuń produkty, a potem kategorię.")
        else:
            st.info("Brak kategorii do usunięcia.")

    st.divider()
    st.subheader("📋 Lista wszystkich kategorii")
    if current_kats:
        st.table(current_kats)
