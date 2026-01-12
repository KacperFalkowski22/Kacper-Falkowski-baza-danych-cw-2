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
    # Pobieramy id, nazwe, liczbe, cene oraz nazwe powiazanej kategorii
    res = supabase.table("Półprodukt").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
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
        # Mapowanie nazwy kategorii z relacji
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
        st.info("Brak produktów w bazie. Dodaj coś w zakładce 'Zarządzanie Produktami'.")

# --- ZAKŁADKA 2: ZARZĄDZANIE PRODUKTAMI ---
with tab_produkty:
    col_prod_add, col_prod_del = st.columns(2)

    # --- DODAWANIE PRODUKTU ---
    with col_prod_add:
        st.subheader("➕ Dodaj nowy półprodukt")
        kategorie_data = get_categories()
        
        if not kategorie_data:
            st.warning("Najpierw dodaj kategorię w sekcji 'Kategorie'!")
        else:
            opcje_kat = {k['nazwa']: k['id'] for k in kategorie_data}
            
            with st.form("form_prod_add", clear_on_submit=True):
                nazwa_prod = st.text_input("Nazwa półproduktu")
                kat_nazwa = st.selectbox("Kategoria", options=list(opcje_kat.keys()))
                c1, c2 = st.columns(2)
                liczba = c1.number_input("Ilość", min_value=0, step=1)
                cena = c2.number_input("Cena (PLN)", min_value=0.0, format="%.2f")
                
                submit_add = st.form_submit_button("Dodaj do bazy")
                
                if submit_add and nazwa_prod:
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

    # --- USUWANIE PRODUKTU ---
    with col_prod_del:
        st.subheader("🗑️ Usuń produkt")
        produkty_data = get_products()
        
        if produkty_data:
            # Tworzymy listę produktów do wyboru (Nazwa - ID)
            opcje_prod = {f"{p['nazwa']} (ID: {p['id']})": p['id'] for p in produkty_data}
            prod_to_del_label = st.selectbox("Wybierz produkt do usunięcia", options=list(opcje_prod.keys()))
            
            if st.button("Usuń produkt", type="primary", use_container_width=True):
                target_id = opcje_prod[prod_to_del_label]
                try:
                    supabase.table("Półprodukt").delete().eq("id", target_id).execute()
                    st.success(f"Pomyślnie usunięto produkt!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd podczas usuwania: {e}")
        else:
            st.info("Brak produktów do usunięcia.")

# --- ZAKŁADKA 3: KATEGORIE ---
with tab_kategorie:
    col_kat_add, col_kat_del = st.columns(2)

    # --- DODAWANIE KATEGORII ---
    with col_kat_add:
        st.subheader("➕ Dodaj nową kategorię")
        with st.form("form_kat_add", clear_on_submit=True):
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

    # --- USUWANIE KATEGORII ---
    with col_kat_del:
        st.subheader("🗑️ Usuń kategorię")
        current_kats = get_categories()
        
        if current_kats:
            delete_options = {k['nazwa']: k['id'] for k in current_kats}
            kat_to_del_name = st.selectbox("Wybierz kategorię do usunięcia", options=list(delete_options.keys()))
            
            if st.button("Usuń kategorię", type="primary", use_container_width=True):
                target_id = delete_options[kat_to_del_name]
                try:
                    supabase.table("kategorie").delete().eq("id", target_id).execute()
                    st.success(f"Usunięto kategorię: {kat_to_del_name}")
                    st.rerun()
                except Exception as e:
                    st.error("Nie można usunąć! Kategoria zawiera produkty.")
        else:
            st.info("Brak kategorii.")

    st.divider()
    st.subheader("📋 Lista wszystkich kategorii")
    if current_kats:
        st.table(current_kats)
