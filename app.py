import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from pandas.io.formats.style import Styler  # FIX: Import corretto per evitare l'AttributeError

# 1. LIVELLO PREMIUM - CONFIGURAZIONE PAGINA
st.set_page_config(
    page_title="eToro Style Portfolio Tracker",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. DESIGN DI DESIGN IN STILE ETORO (CSS Custom)
st.markdown("""
    <style>
    /* Sfondo generale e font scuri premium */
    .stApp {
        background-color: #0b0e11;
        color: #e3e6e8;
    }
    /* Stile delle intestazioni */
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700 !important;
    }
    /* Card in stile eToro */
    .etoro-card {
        background-color: #182026;
        border: 1px solid #243139;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    /* Tab customizzati */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #141b20;
        padding: 8px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #a0aab2 !important;
        background-color: transparent !important;
        border-radius: 6px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        background-color: #46d35f !important; /* Verde eToro */
    }
    /* Input e Sidebar */
    .stSidebar {
        background-color: #141b20 !important;
        border-right: 1px solid #243139;
    }
    /* Modifiche ai DataFrame di Streamlit per integrarsi nel dark mode */
    .stDataFrame, .stDataEditor {
        background-color: #182026 !important;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER APP ---
st.markdown("""
    <div style='display: flex; align-items: center; gap: 15px; margin-bottom: 25px;'>
        <div style='background-color: #46d35f; width: 14px; height: 35px; border-radius: 4px;'></div>
        <h1 style='margin: 0; padding: 0;'>PRO-INVEST PORTFOLIO</h1>
    </div>
""", unsafe_allow_html=True)

# --- CONFIGURAZIONI MACRO PREDEFINITE ---
RECESSION_DEFAULT: dict[str, float] = {"XTLT.MI": 4000.0, "XGSD.MI": 3000.0, "SGLN.MI": 3000.0}
GOLDILOCKS_DEFAULT: dict[str, float] = {"SWDA.MI": 4000.0, "EIMI.MI": 2000.0, "QDVE.XETRA": 2000.0, "IQQH.MI": 2000.0}

# --- SIDEBAR DI GESTIONE ---
st.sidebar.markdown("<h2 style='font-size: 1.4rem; color: #46d35f !important;'>⚙️ STRUMENTI</h2>", unsafe_allow_html=True)
personal_ticker_input = st.sidebar.text_input(
    "Asset nel tuo Radar (Ticker Yahoo):", 
    "SWDA.MI, EIMI.MI, SGLN.MI"
)
personal_tickers: list[str] = [t.strip().upper() for t in personal_ticker_input.split(",") if t.strip()]

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Sincronizza API Mercati", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# --- FUNZIONE CACHE RECUPERO DATI API ---
@st.cache_data(ttl=1800)
def fetch_financial_data(all_tickers: list[str]) -> pd.DataFrame:
    if not all_tickers:
        return pd.DataFrame()
    
    perf_data = []
    end_date = datetime.today()
    start_date = end_date - timedelta(days=450)
    
    for ticker in all_tickers:
        try:
            asset = yf.Ticker(ticker)
            hist = asset.history(start=start_date, end=end_date)
            if hist.empty:
                continue
                
            last_price = float(hist['Close'].iloc[-1])
            
            price_1g = float(hist['Close'].iloc[-2]) if len(hist) > 1 else last_price
            price_5g = float(hist['Close'].asof(end_date - timedelta(days=5)))
            price_1m = float(hist['Close'].asof(end_date - timedelta(days=30)))
            price_3m = float(hist['Close'].asof(end_date - timedelta(days=90)))
            price_6m = float(hist['Close'].asof(end_date - timedelta(days=180)))
            price_1a = float(hist['Close'].asof(end_date - timedelta(days=365)))
            price_ytd = float(hist['Close'].asof(datetime(end_date.year, 1, 1)))
            
            perf_data.append({
                "Ticker": ticker,
                "Prezzo (€)": round(last_price, 2),
                "1 Giorno (%)": round(((last_price - price_1g) / price_1g) * 100, 2),
                "5 Giorni (%)": round(((last_price - price_5g) / price_5g) * 100, 2),
                "1 Mese (%)": round(((last_price - price_1m) / price_1m) * 100, 2),
                "3 Mesi (%)": round(((last_price - price_3m) / price_3m) * 100, 2),
                "6 Mesi (%)": round(((last_price - price_6m) / price_6m) * 100, 2),
                "YTD (%)": round(((last_price - price_ytd) / price_ytd) * 100, 2),
                "1 Anno (%)": round(((last_price - price_1a) / price_1a) * 100, 2),
            })
        except Exception:
            pass
            
    return pd.DataFrame(perf_data)

# Chiamata globale e deduplicazione
all_active_tickers = list(set(personal_tickers + list(RECESSION_DEFAULT.keys()) + list(GOLDILOCKS_DEFAULT.keys())))
df_global_perf = fetch_financial_data(all_active_tickers)

# Stiler condizionale eToro: Verde Smeraldo / Rosso Corallo
def style_performance_df(df: pd.DataFrame) -> Styler:
    def color_etoro(val):
        if isinstance(val, (int, float)):
            # Colori professionali eToro (testo luminoso su sfondo scuro)
            return f"color: {'#46d35f' if val >= 0 else '#ff4a4a'}; font-weight: 600;"
        return ''
    cols = ["1 Giorno (%)", "5 Giorni (%)", "1 Mese (%)", "3 Mesi (%)", "6 Mesi (%)", "YTD (%)", "1 Anno (%)"]
    return df.style.map(color_etoro, subset=[c for c in cols if c in df.columns])

# --- COSTRUZIONE INTERFACCIA ---
if not df_global_perf.empty:
    
    tab1, tab2, tab3 = st.tabs(["👤 PORTAFOGLIO PERSONALE", "🏛️ MERCATI E SCENARI", "⚖️ BENCHMARK & ANALISI"])

    # -------------------------------------------------------------
    # TAB 1: IL TUO PORTAFOGLIO (STILE ETORO)
    # -------------------------------------------------------------
    with tab1:
        st.markdown("<h3 style='margin-top:10px;'>📊 Monitor di Mercato e Quote</h3>", unsafe_allow_html=True)
        df_pers_perf = df_global_perf[df_global_perf["Ticker"].isin(personal_tickers)]
        
        if not df_pers_perf.empty:
            # Tabella Rendimenti
            st.dataframe(style_performance_df(df_pers_perf), use_container_width=True, hide_index=True)
            
            # Area di allocazione interattiva avvolta in una card stilizzata
            st.markdown("<div class='etoro-card'><h4>💰 Modifica Allocazione Capitale</h4>", unsafe_allow_html=True)
            input_df = pd.DataFrame({
                "Ticker": df_pers_perf["Ticker"],
                "Prezzo Attuale (€)": df_pers_perf["Prezzo (€)"],
                "Capitale Investito (€)": [1000.0] * len(df_pers_perf)
            })
            
            edited_pers_df = st.data_editor(
                input_df,
                column_config={
                    "Capitale Investito (€)": st.column_config.NumberColumn("Capitale (€)", min_value=0.0, format="%.2f €"),
                    "Ticker": st.column_config.Column(disabled=True),
                    "Prezzo Attuale (€)": st.column_config.NumberColumn(disabled=True, format="%.2f €")
                },
                hide_index=True, use_container_width=True, key="editor_etoro"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Calcoli quote e pesi finanziari
            edited_pers_df["Quote Spettanti"] = (edited_pers_df["Capitale Investito (€)"] / edited_pers_df["Prezzo Attuale (€)"]).round(4)
            tot_cap_pers = edited_pers_df["Capitale Investito (€)"].sum()
            edited_pers_df["Peso Allocazione (%)"] = ((edited_pers_df["Capitale Investito (€)"] / (tot_cap_pers if tot_cap_pers > 0 else 1)) * 100).round(2)
            
            # Tabella di Riepilogo Sintetica
            st.markdown("<h4>📑 Portafoglio Consolidato</h4>", unsafe_allow_html=True)
            st.dataframe(edited_pers_df[["Ticker", "Capitale Investito (€)", "Quote Spettanti", "Peso Allocazione (%)"]], use_container_width=True, hide_index=True)
            
            # KPI Totali stile eToro
            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<div class='etoro-card' style='border-left: 4px solid #46d35f;'><h5>VALORE PORTAFOGLIO</h5><h2 style='color:#ffffff;'>{round(tot_cap_pers, 2):,} €</h2></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='etoro-card' style='border-left: 4px solid #3498db;'><h5>ASSET IN DETENZIONE</h5><h2 style='color:#ffffff;'>{len(edited_pers_df)} Strumenti</h2></div>", unsafe_allow_html=True)
        else:
            st.warning("Configura i ticker nella barra laterale per generare il portafoglio.")

    # -------------------------------------------------------------
    # TAB 2: PORTAFOGLI DI RIFERIMENTO METRICA
    # -------------------------------------------------------------
    with tab2:
        st.markdown("<h3 style='margin-top:10px;'>🏛️ Asset Allocations Macroeconomiche</h3>", unsafe_allow_html=True)
        col_rec, col_gold = st.columns(2)
        
        with col_rec:
            st.markdown("<div class='etoro-card' style='border-top: 4px solid #e67e22;'><h4>🛡️ Scenario: Recessione</h4><p style='color:#a0aab2;font-size:0.9rem;'>Strumenti anticiclici: Obbligazioni Lunghe, Oro e Beni Rifugio.</p></div>", unsafe_allow_html=True)
            df_rec = df_global_perf[df_global_perf["Ticker"].isin(RECESSION_DEFAULT.keys())].copy()
            df_rec["Capitale (€)"] = df_rec["Ticker"].map(RECESSION_DEFAULT)
