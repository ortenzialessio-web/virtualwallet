import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from pandas.io.formats.style import Styler

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(
    page_title="eToro Style Portfolio Tracker",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. DESIGN STILE ETORO (CSS Custom)
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #e3e6e8; }
    h1, h2, h3, h4 { color: #ffffff !important; font-family: 'Inter', sans-serif; font-weight: 700 !important; }
    .etoro-card {
        background-color: #182026;
        border: 1px solid #243139;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #141b20; padding: 8px; border-radius: 8px; }
    .stTabs [data-baseweb="tab"] { color: #a0aab2 !important; background-color: transparent !important; border-radius: 6px !important; padding: 10px 20px !important; font-weight: 600 !important; }
    .stTabs [aria-selected="true"] { color: #ffffff !important; background-color: #46d35f !important; }
    .stSidebar { background-color: #141b20 !important; border-right: 1px solid #243139; }
    .stDataFrame, .stDataEditor { background-color: #182026 !important; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div style='display: flex; align-items: center; gap: 15px; margin-bottom: 25px;'>
        <div style='background-color: #46d35f; width: 14px; height: 35px; border-radius: 4px;'></div>
        <h1 style='margin: 0; padding: 0;'>PRO-INVEST PORTFOLIO</h1>
    </div>
""", unsafe_allow_html=True)

# --- TICKER PREDEFINITI ULTRA-STABILI ---
RECESSION_DEFAULT: dict[str, float] = {"TLT": 4000.0, "GLD": 3000.0, "XLU": 3000.0}
GOLDILOCKS_DEFAULT: dict[str, float] = {"URTH": 4000.0, "IEMG": 2000.0, "XLK": 4000.0}

# --- SIDEBAR ---
st.sidebar.markdown("<h2 style='font-size: 1.4rem; color: #46d35f !important;'>⚙️ STRUMENTI</h2>", unsafe_allow_html=True)
personal_ticker_input = st.sidebar.text_input(
    "I tuoi ETF (separati da virgola):", 
    "URTH, XLK, GLD"
)
personal_tickers: list[str] = [t.strip().upper() for t in personal_ticker_input.split(",") if t.strip()]

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Sincronizza API Mercati", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# --- FUNZIONE CACHE RECUPERO DATI API ---
@st.cache_data(ttl=600)
def fetch_financial_data(all_tickers: list[str]) -> pd.DataFrame:
    if not all_tickers:
        return pd.DataFrame()
    
    perf_data = []
    end_date = datetime.today()
    start_date = end_date - timedelta(days=450)
    
    for ticker in all_tickers:
        try:
            asset = yf.Ticker(ticker)
            hist = asset.history(period="2y") 
            
            if hist.empty or len(hist) < 10:
                continue
                
            last_price = float(hist['Close'].iloc[-1])
            
            price_1g = float(hist['Close'].iloc[-2]) if len(hist) > 1 else last_price
            price_5g = float(hist['Close'].asof(end_date - timedelta(days=5)))
            price_1m = float(hist['Close'].asof(end_date - timedelta(days=30)))
            price_3m = float(hist['Close'].asof(end_date - timedelta(days=90)))
            price_6m = float(hist['Close'].asof(end_date - timedelta(days=180)))
            price_1a = float(hist['Close'].asof(end_date - timedelta(days=365)))
            price_ytd = float(hist['Close'].asof(datetime(end_date.year, 1, 1)))
            
            price_5g = price_5g if pd.notna(price_5g) else last_price
            price_1m = price_1m if pd.notna(price_1m) else last_price
            price_3m = price_3m if pd.notna(price_3m) else last_price
            price_6m = price_6m if pd.notna(price_6m) else last_price
            price_1a = price_1a if pd.notna(price_1a) else last_price
            price_ytd = price_ytd if pd.notna(price_ytd) else last_price

            perf_data.append({
                "Ticker": ticker,
                "Prezzo ($/€)": round(last_price, 2),
                "1 Giorno (%)": round(((last_price - price_1g) / price_1g) * 100, 2) if price_1g else 0.0,
                "5 Giorni (%)": round(((last_price - price_5g) / price_5g) * 100, 2) if price_5g else 0.0,
                "1 Mese (%)": round(((last_price - price_1m) / price_1m) * 100, 2) if price_1m else 0.0,
                "3 Mesi (%)": round(((last_price - price_3m) / price_3m) * 100, 2) if price_3m else 0.0,
                "6 Mesi (%)": round(((last_price - price_6m) / price_6m) * 100, 2) if price_6m else 0.0,
                "YTD (%)": round(((last_price - price_ytd) / price_ytd) * 100, 2) if price_ytd else 0.0,
                "1 Anno (%)": round(((last_price - price_1a) / price_1a) * 100, 2) if price_1a else 0.0,
            })
        except Exception:
            pass
            
    return pd.DataFrame(perf_data)

all_active_tickers = list(set(personal_tickers + list(RECESSION_DEFAULT.keys()) + list(GOLDILOCKS_DEFAULT.keys())))
df_global_perf = fetch_financial_data(all_active_tickers)

def style_performance_df(df: pd.DataFrame) -> Styler:
    def color_etoro(val):
        if isinstance(val, (int, float)):
            return f"color: {'#46d35f' if val >= 0 else '#ff4a4a'}; font-weight: 600;"
        return ''
    cols = ["1 Giorno (%)", "5 Giorni (%)", "1 Mese (%)", "3 Mesi (%)", "6 Mesi (%)", "YTD (%)", "1 Anno (%)"]
    return df.style.map(color_etoro, subset=[c for c in cols if c in df.columns])

# --- RENDERING APPLICAZIONE ---
if not df_global_perf.empty:
    
    tab1, tab2, tab3 = st.tabs(["👤 PORTAFOGLIO PERSONALE", "🏛️ MERCATI E SCENARI", "⚖️ BENCHMARK & ANALISI"])

    # -------------------------------------------------------------
    # TAB 1: PORTAFOGLIO PERSONALE
    # -------------------------------------------------------------
    with tab1:
        st.markdown("<h3 style='margin-top:10px;'>📊 Il tuo Radar Asset</h3>", unsafe_allow_html=True)
        df_pers_perf = df_global_perf[df_global_perf["Ticker"].isin(personal_tickers)]
        
        if not df_pers_perf.empty:
            st.dataframe(style_performance_df(df_pers_perf), use_container_width=True, hide_index=True)
            
            st.markdown("<div class='etoro-card'><h4>💰 Quantità Quote Acquistate (Capitale in Euro)</h4>", unsafe_allow_html=True)
            input_df = pd.DataFrame({
                "Ticker": df_pers_perf["Ticker"],
                "Prezzo Attuale ($/€)": df_pers_perf["Prezzo ($/€)"],
                "Capitale Investito (€)": [1000.0] * len(df_pers_perf)
            })
            
            edited_pers_df = st.data_editor(
                input_df,
                column_config={
                    "Capitale Investito (€)": st.column_config.NumberColumn("Capitale (€)", min_value=0.0, format="%.2f €"),
                    "Ticker": st.column_config.Column(disabled=True),
                    "Prezzo Attuale ($/€)": st.column_config.NumberColumn(disabled=True)
                },
                hide_index=True, use_container_width=True, key="editor_etoro_v6"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
            edited_pers_df["Quote Spettanti"] = (edited_pers_df["Capitale Investito (€)"] / edited_pers_df["Prezzo Attuale ($/€)"]).round(4)
            tot_cap_pers = edited_pers_df["Capitale Investito (€)"].sum()
            edited_pers_df["Peso Allocazione (%)"] = ((edited_pers_df["Capitale Investito (€)"] / (tot_cap_pers if tot_cap_pers > 0 else 1)) * 100).round(2)
            
            st.markdown("<h4>📑 Portafoglio Consolidato</h4>", unsafe_allow_html=True)
            st.dataframe(edited_pers_df[["Ticker", "Capitale Investito (€)", "Quote Spettanti", "Peso Allocazione (%)"]], use_container_width=True, hide_index=True)
            
            c1, c2 = st.columns(2)
            c1.markdown(f"<div class='etoro-card' style='border-left: 4px solid #46d35f;'><h5>VALORE PORTAFOGLIO</h5><h2>{round(tot_cap_pers, 2):,} €</h2></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='etoro-card' style='border-left: 4px solid #3498db;'><h5>STRUMENTI IN DETENZIONE</h5><h2>{len(edited_pers_df)} ETF</h2></div>", unsafe_allow_html=True)
        else:
            st.warning("Nessun dato disponibile per i tuoi asset personali. Verifica i ticker.")

    # -------------------------------------------------------------
    # TAB 2: PORTAFOGLI DI RIFERIMENTO (SINTASSI E SPAZI CORRETTI)
    # -------------------------------------------------------------
    with tab2:
        st.markdown("<h3 style='margin-top:10px;'>🏛️ Asset Allocations Macroeconomiche</h3>", unsafe_allow_html=True)
        col_rec, col_gold = st.columns(2)
        
        with col_rec:
            st.markdown("<div class='etoro-card' style='border-top: 4px solid #e67e22;'><h4>🛡️ Scenario: Recessione</h4><p style='color:#a0aab2;font-size:0.9rem;'>Asset: TLT (Bond), GLD (Oro), XLU (Utility).</p></div>", unsafe_allow_html=True)
            df_rec = df_global_perf[df_global_perf["Ticker"].isin(RECESSION_DEFAULT.keys())].copy()
            if not df_rec.empty:
                df_rec["Capitale (€)"] = df_rec["Ticker"].map(RECESSION_DEFAULT)
                df_rec["Quote"] = (df_rec["Capitale (€)"] / df_rec["Prezzo ($/€)"]).round(4)
                st.dataframe(style_performance_df(df_rec.drop(columns=["Capitale (€)", "Quote"])), use_container_width=True, hide_index=True)
                st.dataframe(df_rec[["Ticker", "Capitale (€)", "Quote"]], use_container_width=True, hide_index=True)
            else:
                st.info("Nessun dato recuperato per il portafoglio Recessione.")

        with col_gold:
