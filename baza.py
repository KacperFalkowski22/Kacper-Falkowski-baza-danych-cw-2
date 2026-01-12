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
    res = supabase.table("Półprodukt").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
    return res.data

# --- GŁÓWNA NAWIGACJA ---
tab_dashboard, tab_produkty, tab_kategorie = st.tabs([
    "📊 Statystyki i Wykresy", 
    "🔨 Zarządzanie Produktami", 
    "📁 Kategorie"
])

# --- ZAKŁADKA 1: STATYSTYKI (Bez zmian) ---
with tab_dashboard:
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
        st.dataframe(df[["nazwa", "liczba", "cena", "kategoria_nazwa"]], use_container_width=True)
    else:
        st.info("Baza jest pusta.")

# --- ZAKŁADKA 2: ZARZĄDZANIE PRODUKTAMI (ZMIENIONA) ---
with tab_produkty:
    col_prod_add, col_prod_edit = st.columns(2)

    # --- DODAWANIE PRODUKTU ---
    with col_prod_add:
        st.subheader("➕ Dodaj / Zwiększ stan")
        kategorie_data = get_categories()
        if kategorie_data:
            opcje_kat = {k['nazwa']: k['id'] for k in kategorie_data}
            with st.form("form_prod_add", clear_on_submit=True):
                nazwa_prod = st.text_input("Nazwa półproduktu")
                kat_nazwa = st.selectbox("Kategoria", options=list(opcje_kat.keys()))
                c1, c2 = st.columns(2)
                liczba_add = c1.number_input("Ilość do dodania", min_value=1, step=1)
                cena_add = c2.number_input("Cena (PLN)", min_value=0.0, format="%.2f")
                submit_add = st.form_submit_button("Dodaj do magazynu")
                
                if submit_add and nazwa_prod:
                    try:
                        payload = {"nazwa": nazwa_prod, "liczba": liczba_add, "cena": cena_add, "kategoria_id": opcje_kat[kat_nazwa]}
                        supabase.table("Półprodukt").insert(payload).execute()
                        st.success(f"Dodano {liczba_add} szt. produktu {nazwa_prod}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd: {e}")

    # --- WYDAWANIE / ZDEJMOWANIE ZE STANU ---
    with col_prod_edit:
        st.subheader("➖ Wydaj z magazynu (Zdejmij stan)")
        produkty_data = get_products()
        
        if produkty_data:
            # Tworzymy mapowanie: Etykieta -> Pełne dane o produkcie
            opcje_prod = {f"{p['nazwa']} (Dostępne: {p['liczba']})": p for p in produkty_data}
            wybrany_label = st.selectbox("Wybierz produkt", options=list(opcje_prod.keys()))
            
            produkt = opcje_prod[wybrany_label]
            id_prod = produkt['id']
            obecny_stan = produkt['liczba']

            with st.form("form_prod_reduce"):
                ile_odjac = st.number_input(f"Ile sztuk wydać? (Max: {obecny_stan})", min_value=1, max_value=obecny_stan, step=1)
                tryb_usun = st.checkbox("Usuń całkowicie z bazy, jeśli stan wyniesie 0", value=True)
                submit_reduce = st.form_submit_button("Potwierdź wydanie", type="primary")

                if submit_reduce:
                    nowy_stan = obecny_stan - ile_odjac
                    
                    try:
                        if nowy_stan > 0:
                            # AKTUALIZACJA (UPDATE)
                            supabase.table("Półprodukt").update({"liczba": nowy_stan}).eq("id", id_prod).execute()
                            st.success(f"Wydano {ile_odjac} szt. Zostało: {nowy_stan}")
                        else:
                            # USUWANIE (DELETE) lub ustawienie 0
                            if tryb_usun:
                                supabase.table("Półprodukt").delete().eq("id", id_prod).execute()
                                st.success(f"Wydano wszystko. Produkt usunięty z bazy.")
                            else:
                                supabase.table("Półprodukt").update({"liczba": 0}).eq("id", id_prod).execute()
                                st.success(f"Stan wynosi teraz 0.")
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd: {e}")
        else:
            st.info("Brak produktów do wydania.")

# --- ZAKŁADKA 3: KATEGORIE (Bez zmian) ---
with tab_kategorie:
    col_kat_add, col_kat_del = st.columns(2)
    with col_kat_add:
        st.subheader("➕ Dodaj kategorię")
        with st.form("form_kat_add", clear_on_submit=True):
            n = st.text_input("Nazwa")
            if st.form_submit_button("Zapisz"):
                supabase.table("kategorie").insert({"nazwa": n}).execute()
                st.rerun()
    with col_kat_del:
        st.subheader("🗑️ Usuń kategorię")
        kats = get_categories()
        if kats:
            o = {k['nazwa']: k['id'] for k in kats}
            wybor = st.selectbox("Kategoria", list(o.keys()))
            if st.button("Usuń całkowicie", type="secondary"):
                try:
                    supabase.table("kategorie").delete().eq("id", o[wybor]).execute()
                    st.rerun()
                except:
                    st.error("Kategoria ma przypisane produkty!")
