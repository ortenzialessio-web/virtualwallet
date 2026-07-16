import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURAZIONE PAGINA (Layout fluido PC / Android)
st.set_page_config(
    page_title="Multi-Portfolio ETF Tracker v3.11",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ottimizzazioni CSS per la reattività mobile
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    .stDataFrame { width: 100%; }
    [data-testid="stMetricValue"] { font-size: 1.6rem; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Virtual ETF Portfolio Tracker (Python 3.11)")
st.caption("Dati Real-Time da Yahoo Finance API • Ottimizzato per PC e Android")

# --- STRUTTURE DATI PREDEFINITE ---
RECESSION_DEFAULT: dict[str, float] = {"XTLT.MI": 4000.0, "XGSD.MI": 3000.0, "SGLN.MI": 3000.0}
GOLDILOCKS_DEFAULT: dict[str, float] = {"SWDA.MI": 4000.0, "EIMI.MI": 2000.0, "QDVE.XETRA": 2000.0, "IQQH.MI": 2000.0}

# --- INTERFACCIA A SCHEDE (TABS) ---
tab1, tab2, tab3 = st.tabs(["👤 Il tuo Portafoglio", "🏛️ Portafogli di Riferimento", "⚖️ Comparazione Strategie"])

# --- SIDEBAR DI CONTROLLO ---
st.sidebar.header("🔧 Configura Asset")
personal_ticker_input = st.sidebar.text_input(
    "I tuoi ETF (separati da virgola):", 
    "SWDA.MI, EIMI.MI, SGLN.MI"
)
personal_tickers: list[str] = [t.strip().upper() for t in personal_ticker_input.split(",") if t.strip()]

if st.sidebar.button("🔄 Forza Aggiornamento Dati"):
    st.cache_data.clear()
    st.rerun()

# --- RECUPERO DATI CON DECORATORE STREAMLIT (OTTIMIZZATO CACHE) ---
@st.cache_data(ttl=1800)
def fetch_financial_data(all_tickers: list[str]) -> pd.DataFrame:
    if not all_tickers:
        return pd.DataFrame()
    
    perf_data = []
    end_date = datetime.today()
    start_date = end_date - timedelta(days=450) # Finestra temporale di sicurezza per 1 anno e YTD
    
    for ticker in all_tickers:
        try:
            asset = yf.Ticker(ticker)
            hist = asset.history(start=start_date, end=end_date)
            if hist.empty:
                continue
                
            last_price = float(hist['Close'].iloc[-1])
            
            # Calcolo dei punti storici finanziari usando .asof() di Pandas
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
            pass # Ignora errori di ticker non trovati per non bloccare l'app su Android
            
    return pd.DataFrame(perf_data)

# Unione e deduplicazione efficiente dei ticker
all_active_tickers = list(set(personal_tickers + list(RECESSION_DEFAULT.keys()) + list(GOLDILOCKS_DEFAULT.keys())))
df_global_perf = fetch_financial_data(all_active_tickers)

# Stile condizionale per i rendimenti (Verde/Rosso vivido)
def style_performance_df(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    def color_vivid(val):
        if isinstance(val, (int, float)):
            return f"color: {'#2ecc71' if val >= 0 else '#e74c3c'}; font-weight: bold;"
        return ''
    cols = ["1 Giorno (%)", "5 Giorni (%)", "1 Mese (%)", "3 Mesi (%)", "6 Mesi (%)", "YTD (%)", "1 Anno (%)"]
    return df.style.map(color_vivid, subset=[c for c in cols if c in df.columns])

# --- COSTRUZIONE DELLE SCHEDE ---
if not df_global_perf.empty:
    
    # -------------------------------------------------------------
    # TAB 1: PORTAFOGLIO UTENTE
    # -------------------------------------------------------------
    with tab1:
        st.subheader("📌 Performance Asset Selezionati")
        df_pers_perf = df_global_perf[df_global_perf["Ticker"].isin(personal_tickers)]
        
        if not df_pers_perf.empty:
            st.dataframe(style_performance_df(df_pers_perf), use_container_width=True, hide_index=True)
            
            st.markdown("### 💵 Allocazione Quote in Euro")
            st.write("Puoi editare la colonna **'Capitale Investito (€)'** direttamente toccando la cella:")
            
            input_df = pd.DataFrame({
                "Ticker": df_pers_perf["Ticker"],
                "Prezzo Attuale (€)": df_pers_perf["Prezzo (€)"],
                "Capitale Investito (€)": [1000.0] * len(df_pers_perf)
            })
            
            # Editor interattivo nativo di Streamlit (perfetto per tastiere Android)
            edited_pers_df = st.data_editor(
                input_df,
                column_config={
                    "Capitale Investito (€)": st.column_config.NumberColumn("Capitale Investito (€)", min_value=0.0, format="%.2f €"),
                    "Ticker": st.column_config.Column(disabled=True),
                    "Prezzo Attuale (€)": st.column_config.NumberColumn(disabled=True, format="%.2f €")
                },
                hide_index=True, use_container_width=True, key="editor_pers_311"
            )
            
            # Calcoli derivati
            edited_pers_df["Quote Calcolate"] = (edited_pers_df["Capitale Investito (€)"] / edited_pers_df["Prezzo Attuale (€)"]).round(4)
            tot_cap_pers = edited_pers_df["Capitale Investito (€)"].sum()
            edited_pers_df["Peso (%)"] = ((edited_pers_df["Capitale Investito (€)"] / (tot_cap_pers if tot_cap_pers > 0 else 1)) * 100).round(2)
            
            st.dataframe(edited_pers_df[["Ticker", "Capitale Investito (€)", "Quote Calcolate", "Peso (%)"]], use_container_width=True, hide_index=True)
        else:
            st.warning("Inserisci ticker validi nella sidebar.")

    # -------------------------------------------------------------
    # TAB 2: PORTAFOGLI BENCHMARK
    # -------------------------------------------------------------
    with tab2:
        col_rec, col_gold = st.columns(2)
        
        with col_rec:
            st.subheader("🛡️ Scenario: Recessione")
            df_rec = df_global_perf[df_global_perf["Ticker"].isin(RECESSION_DEFAULT.keys())].copy()
            df_rec["Capitale (€)"] = df_rec["Ticker"].map(RECESSION_DEFAULT)
            df_rec["Quote"] = (df_rec["Capitale (€)"] / df_rec["Prezzo (€)"]).round(4)
            
            st.dataframe(style_performance_df(df_rec.drop(columns=["Capitale (€)", "Quote"])), use_container_width=True, hide_index=True)
            st.dataframe(df_rec[["Ticker", "Capitale (€)", "Quote"]], use_container_width=True, hide_index=True)

        with col_gold:
            st.subheader("🦄 Scenario: Goldilocks Economy")
            df_gold = df_global_perf[df_global_perf["Ticker"].isin(GOLDILOCKS_DEFAULT.keys())].copy()
            df_gold["Capitale (€)"] = df_gold["Ticker"].map(GOLDILOCKS_DEFAULT)
            df_gold["Quote"] = (df_gold["Capitale (€)"] / df_gold["Prezzo (€)"]).round(4)
            
            st.dataframe(style_performance_df(df_gold.drop(columns=["Capitale (€)", "Quote"])), use_container_width=True, hide_index=True)
            st.dataframe(df_gold[["Ticker", "Capitale (€)", "Quote"]], use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # TAB 3: COMPARAZIONE DELLE STRATEGIE PONDERATE
    # -------------------------------------------------------------
    with tab3:
        st.subheader("⚖️ Analisi Comparativa Ponderata")
        
        def calcola_performance_ponderata(df_perf_asset: pd.DataFrame, dict_capitali: dict[str, float]) -> dict[str, float]:
            df = df_perf_asset.copy()
            df["Capitale"] = df["Ticker"].map(dict_capitali)
            tot_cap = df["Capitale"].sum()
            df["Peso"] = df["Capitale"] / (tot_cap if tot_cap > 0 else 1)
            
            archi_temporali = ["1 Giorno (%)", "5 Giorni (%)", "1 Mese (%)", "3 Mesi (%)", "6 Mesi (%)", "YTD (%)", "1 Anno (%)"]
            return {arco: round((df[arco] * df["Peso"]).sum(), 2) for arco in archi_temporali}

        pers_cap_dict = dict(zip(edited_pers_df["Ticker"], edited_pers_df["Capitale Investito (€)"]))
        
        perf_personale = calcola_performance_ponderata(df_pers_perf, pers_cap_dict)
        perf_recessione = calcola_performance_ponderata(df_global_perf[df_global_perf["Ticker"].isin(RECESSION_DEFAULT.keys())], RECESSION_DEFAULT)
        perf_goldilocks = calcola_performance_ponderata(df_global_perf[df_global_perf["Ticker"].isin(GOLDILOCKS_DEFAULT.keys())], GOLDILOCKS_DEFAULT)
        
        df_confronto = pd.DataFrame([
            {"Portafoglio": "👤 Il tuo Portafoglio", **perf_personale},
            {"Portafoglio": "🛡️ Recessione Benchmark", **perf_recessione},
            {"Portafoglio": "🦄 Goldilocks Economy Benchmark", **perf_goldilocks}
        ])
        
        st.dataframe(style_performance_df(df_confronto), use_container_width=True, hide_index=True)
        
        # GRAFICO PLOTLY RESPONSIVE
