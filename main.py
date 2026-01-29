import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
from fredapi import Fred
import finnhub
from datetime import datetime, timedelta
import matplotlib.colors as mcolors

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA & CSS
# ==============================================================================
st.set_page_config(layout="wide", page_title="Edge Terminal", page_icon="📈")

st.markdown("""
<style>
    /* Ajuste de métricas */
    [data-testid="stMetricValue"] { font-size: 20px; }
    
    /* INPUTS: Texto BLANCO */
    .stTextInput>div>div>input { 
        color: #FFFFFF !important; 
        font-weight: bold; 
    }
    
    /* Scrollbars personalizados */
    ::-webkit-scrollbar { width: 10px; }
    ::-webkit-scrollbar-track { background: #1E1E1E; }
    ::-webkit-scrollbar-thumb { background: #555; border-radius: 5px; }
    ::-webkit-scrollbar-thumb:hover { background: #00BBA2; }
    
    /* TÍTULO Y SLOGAN PERSONALIZADO */
    .title-container {
        margin-bottom: 20px;
    }
    .main-title {
        font-size: 50px;
        font-weight: 700;
        margin-bottom: 0px;
        color: #FFFFFF;
        line-height: 1.2;
    }
    .subtitle {
        font-size: 20px;
        color: #AAAAAA;
        font-style: italic;
        font-weight: 300;
        margin-top: -5px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. VARIABLES GLOBALES (Listas y Diccionarios Maestros)
# ==============================================================================
etfs = [
    'XTL', 'PPA', 'MCHI', 'USO', 'XLK', 'EEM', 'XLY', 'XRT', 'XLI', 'QQQ', 
    'XLU', 'TLT', 'DBC', 'XHB', 'XLP', 'USMC', 'XLF', 'XLB', 'SPY', 'JNK', 
    'EMB', 'BNDW', 'COPX', 'DIA', 'JETS', 'XLE', 'UUP', 'GLD', 'SLX', 'EWZ', 
    'XLV', 'SLV', 'PPH', 'GDX', 'ARGT'
]

# Definimos el diccionario AQUÍ para que Tab 1 y Tab 4 lo puedan usar
asset_meta = {
    'XTL':  {'Nombre': 'SPDR S&P Telecom', 'Sector': 'Telecomunicaciones'},
    'PPA':  {'Nombre': 'Invesco Aerospace', 'Sector': 'Aeroespacial'},
    'MCHI': {'Nombre': 'iShares MSCI China', 'Sector': 'China'},
    'USO':  {'Nombre': 'United States Oil', 'Sector': 'Petróleo'},
    'XLK':  {'Nombre': 'Technology Select', 'Sector': 'Tecnología'},
    'EEM':  {'Nombre': 'iShares Emerging', 'Sector': 'Emergentes'},
    'XLY':  {'Nombre': 'Consumer Discretionary', 'Sector': 'Consumo Discrec.'},
    'XRT':  {'Nombre': 'SPDR S&P Retail', 'Sector': 'Retail'},
    'XLI':  {'Nombre': 'Industrial Select', 'Sector': 'Industrial'},
    'QQQ':  {'Nombre': 'Invesco QQQ', 'Sector': 'Nasdaq 100'},
    'XLU':  {'Nombre': 'Utilities Select', 'Sector': 'Utilities'},
    'TLT':  {'Nombre': '20+ Year Treasury', 'Sector': 'Bonos Largos'},
    'DBC':  {'Nombre': 'Invesco DB Commodity', 'Sector': 'Commodities'},
    'XHB':  {'Nombre': 'SPDR Homebuilders', 'Sector': 'Construcción'},
    'XLP':  {'Nombre': 'Consumer Staples', 'Sector': 'Consumo Básico'},
    'USMC': {'Nombre': 'Principal Mega-Cap', 'Sector': 'Mega Cap USA'},
    'XLF':  {'Nombre': 'Financial Select', 'Sector': 'Financiero'},
    'XLB':  {'Nombre': 'Materials Select', 'Sector': 'Materiales'},
    'SPY':  {'Nombre': 'SPDR S&P 500', 'Sector': 'S&P 500'},
    'JNK':  {'Nombre': 'Bloomberg High Yield', 'Sector': 'Bonos Basura'},
    'EMB':  {'Nombre': 'J.P. Morgan EM Bond', 'Sector': 'Bonos Emergentes'},
    'BNDW': {'Nombre': 'Total World Bond', 'Sector': 'Bonos Globales'},
    'COPX': {'Nombre': 'Global X Copper', 'Sector': 'Mineras Cobre'},
    'DIA':  {'Nombre': 'Dow Jones Ind.', 'Sector': 'Dow Jones'},
    'JETS': {'Nombre': 'U.S. Global Jets', 'Sector': 'Aerolíneas'},
    'XLE':  {'Nombre': 'Energy Select', 'Sector': 'Energía'},
    'UUP':  {'Nombre': 'DB US Dollar Index', 'Sector': 'Dólar'},
    'GLD':  {'Nombre': 'SPDR Gold Shares', 'Sector': 'Oro'},
    'SLX':  {'Nombre': 'VanEck Steel', 'Sector': 'Acero'},
    'EWZ':  {'Nombre': 'MSCI Brazil', 'Sector': 'Brasil'},
    'XLV':  {'Nombre': 'Health Care Select', 'Sector': 'Salud'},
    'SLV':  {'Nombre': 'iShares Silver', 'Sector': 'Plata'},
    'PPH':  {'Nombre': 'VanEck Pharma', 'Sector': 'Farmacéuticas'},
    'GDX':  {'Nombre': 'VanEck Gold Miners', 'Sector': 'Mineras Oro'},
    'ARGT': {'Nombre': 'MSCI Argentina', 'Sector': 'Argentina'}
}

# ==============================================================================
# 3. ESTRUCTURA DE PESTAÑAS Y HEADER
# ==============================================================================

# Renderizamos el Título y Slogan con HTML/CSS personalizado
st.markdown("""
<div class="title-container">
    <div class="main-title">Edge Terminal</div>
    <div class="subtitle">Refine Your Edge</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Monitoreo", "Fuerza Relativa", "Deep Dive", "Quant Lab", "Macro Room", "Información"])

# ==============================================================================
# TAB 1: WATCHLIST SECTORIAL
# ==============================================================================
with tab1:
    st.header("Watchlist Sectorial (ETF)")
    st.caption("Mapa de calor dinámico + Tendencia de corto plazo.")

    tickers = etfs 
    
    if tickers:
        try:
            data = yf.download(tickers, period="1y", interval="1d", group_by='ticker', progress=False, auto_adjust=True)
            rows = []
            start_year = f"{datetime.now().year}-01-01"
            date_30d = datetime.now() - timedelta(days=30)

            for ticker in tickers:
                try:
                    if isinstance(data.columns, pd.MultiIndex): df_t = data[ticker]
                    else: df_t = data
                    
                    if not df_t.empty and 'Close' in df_t.columns:
                        history = df_t['Close']
                        current = history.iloc[-1]
                        prev = history.iloc[-2]
                        
                        pct_day = ((current - prev) / prev) * 100
                        
                        m_data = history[history.index >= date_30d]
                        pct_month = ((current - m_data.iloc[0]) / m_data.iloc[0]) * 100 if not m_data.empty else 0.0
                        
                        y_data = history[history.index >= start_year]
                        pct_ytd = ((current - y_data.iloc[0]) / y_data.iloc[0]) * 100 if not y_data.empty else 0.0
                        
                        chart_90d = history.tail(90).tolist()
                        info = asset_meta.get(ticker, {'Nombre': ticker, 'Sector': 'Otro'})

                        rows.append({
                            "Ticker": ticker,
                            "Activo": info['Nombre'],
                            "Sector": info['Sector'],
                            "Precio ($)": current,
                            "Var Día (%)": pct_day,
                            "Var Mes (%)": pct_month,
                            "Var YTD (%)": pct_ytd,
                            "Tendencia": chart_90d 
                        })
                except: continue
            
            df_view = pd.DataFrame(rows)
            col_ord = ["Ticker", "Activo", "Sector", "Precio ($)", "Var Día (%)", "Var Mes (%)", "Var YTD (%)", "Tendencia"]
            df_view = df_view[col_ord]

            if not df_view.empty:
                colors = ["#FF6C6C", "#1E1E1E", "#00BBA2"] 
                cmap = mcolors.LinearSegmentedColormap.from_list("custom_diverging", colors)

                v_day = df_view["Var Día (%)"]; lim_day = max(abs(v_day.min()), abs(v_day.max())) if not v_day.empty else 1
                v_mes = df_view["Var Mes (%)"]; lim_mes = max(abs(v_mes.min()), abs(v_mes.max())) if not v_mes.empty else 1
                v_ytd = df_view["Var YTD (%)"]; lim_ytd = max(abs(v_ytd.min()), abs(v_ytd.max())) if not v_ytd.empty else 1

                styled_df = (df_view.style
                    .format({
                        "Precio ($)": "{:.2f}",
                        "Var Día (%)": "{:+.2f}",
                        "Var Mes (%)": "{:+.2f}",
                        "Var YTD (%)": "{:+.2f}"
                    })
                    .background_gradient(cmap=cmap, subset=["Var Día (%)"], vmin=-lim_day, vmax=lim_day)
                    .background_gradient(cmap=cmap, subset=["Var Mes (%)"], vmin=-lim_mes, vmax=lim_mes)
                    .background_gradient(cmap=cmap, subset=["Var YTD (%)"], vmin=-lim_ytd, vmax=lim_ytd)
                )

                st.dataframe(
                    styled_df,
                    column_config={
                        "Tendencia": st.column_config.AreaChartColumn(
                            "Price performance (90d)", 
                            width="medium",
                            y_min=None, 
                            y_max=None,
                            color="#00BBA2"
                        )
                    },
                    use_container_width=True,
                    height=800,
                    hide_index=True
                )
            else: st.warning("No data.")

        except Exception as e: st.error(f"Error: {e}")

# ==============================================================================
# TAB 2: FUERZA RELATIVA
# ==============================================================================
with tab2:
    st.header("Análisis Comparativo (Ratio vs Rendimiento)")
    
    c_rs1, c_rs2, c_rs3 = st.columns([1, 3, 1])
    
    with c_rs1:
        anchor_input = st.text_input("Ancla (Base)", value="SPY", help="Benchmark", key="anchor_tab2").upper().strip()
    with c_rs2:
        default_compare = "QQQ, GLD, BTC-USD, IWM, XLE"
        compare_str = st.text_input("Activos a Comparar", value=default_compare, key="compare_tab2")
    with c_rs3:
        dias_rs = st.selectbox("Ventana", [60, 90, 120, 252, 500], index=1, format_func=lambda x: f"Últimos {x} días", key="window_tab2")

    if compare_str:
        comparison_tickers = [x.strip().upper() for x in compare_str.split(',') if x.strip()]
        all_download_list = list(set(comparison_tickers + [anchor_input]))
        
        try:
            start_date = datetime.today() - timedelta(days=dias_rs + 15)
            data = yf.download(all_download_list, start=start_date, progress=False, auto_adjust=True)['Close']
            
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            if isinstance(data, pd.Series): data = data.to_frame(name=data.name)
            data = data.ffill().tail(dias_rs).copy()

            if anchor_input in data.columns and not data[anchor_input].isnull().all():
                col_left, col_right = st.columns(2)
                valid_tickers = [t for t in comparison_tickers if t in data.columns]
                
                # Grid Style
                layout_grid = dict(showgrid=True, gridwidth=1, gridcolor='rgba(255, 255, 255, 0.1)')

                with col_left:
                    st.subheader(f"1. Fuerza Relativa (vs {anchor_input})")
                    fig_rs = go.Figure()
                    for ticker in valid_tickers:
                        if ticker == anchor_input: continue 
                        ratio = (data[ticker] / data[anchor_input])
                        if ratio.first_valid_index():
                            base_100 = (ratio / ratio.loc[ratio.first_valid_index()]) * 100
                            fig_rs.add_trace(go.Scatter(x=base_100.index, y=base_100, name=ticker, opacity=0.8, connectgaps=True))
                            
                    fig_rs.add_hline(y=100, line_dash="dash", line_color="gray")
                    fig_rs.update_layout(height=450, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                         yaxis_title="Fuerza Relativa", legend=dict(orientation="h", y=-0.15),
                                         xaxis=layout_grid, yaxis=layout_grid)
                    st.plotly_chart(fig_rs, use_container_width=True)

                with col_right:
                    st.subheader("2. Carrera de Rendimiento (%)")
                    fig_perf = go.Figure()
                    plot_list = list(set(valid_tickers + [anchor_input]))
                    for ticker in plot_list:
                        series = data[ticker]
                        if series.first_valid_index():
                            perf = ((series / series.loc[series.first_valid_index()]) - 1) * 100
                            is_anchor = (ticker == anchor_input)
                            dash = 'dash' if is_anchor else 'solid'
                            color = '#FFFFFF' if is_anchor else None
                            width = 2 if is_anchor else 1.5
                            fig_perf.add_trace(go.Scatter(x=perf.index, y=perf, name=ticker, line=dict(dash=dash, color=color, width=width), connectgaps=True))
                            
                    fig_perf.add_hline(y=0, line_color="gray")
                    fig_perf.update_layout(height=450, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                           yaxis_title="Retorno %", legend=dict(orientation="h", y=-0.15),
                                           xaxis=layout_grid, yaxis=layout_grid)
                    st.plotly_chart(fig_perf, use_container_width=True)
            else:
                st.error("Datos de ancla no disponibles.")
        except Exception as e:
            st.error(f"Error Tab 2: {e}")

# ==============================================================================
# TAB 3: DEEP DIVE
# ==============================================================================
with tab3:
    c_in, c_main, c_ret, c_fund, c_risk = st.columns([1, 2, 1, 1.2, 1.5]) 
    
    with c_in:
        ticker_input_t3 = st.text_input("Ticker", value="CAT", key="input_tab3").upper().strip()

    company_name = ticker_input_t3
    
    try:
        df_header = yf.download(ticker_input_t3, period="1y", interval="1d", progress=False, auto_adjust=True)
        if isinstance(df_header.columns, pd.MultiIndex): df_header.columns = df_header.columns.get_level_values(0)
        
        if not df_header.empty:
            last = df_header['Close'].iloc[-1]
            
            # --- DATOS FUNDAMENTALES ---
            mkt_cap_fmt = "N/A"
            pe_fmt = "N/A"
            div_fmt = "0.00%"
            beta_fmt = "N/A"
            next_earn = "N/A"
            
            try:
                t_obj = yf.Ticker(ticker_input_t3)
                info = t_obj.info
                company_name = info.get('longName', ticker_input_t3)
                
                # Market Cap
                mc = info.get('marketCap', 0)
                if mc > 1e12: mkt_cap_fmt = f"{mc/1e12:.2f}T"
                elif mc > 1e9: mkt_cap_fmt = f"{mc/1e9:.2f}B"
                elif mc > 1e6: mkt_cap_fmt = f"{mc/1e6:.2f}M"
                
                # P/E Ratio
                pe = info.get('trailingPE', None)
                if pe is None: pe = info.get('forwardPE', None)
                pe_fmt = f"{pe:.2f}" if pe else "N/A"
                
                # Dividend Yield (ROBUSTO)
                dy = info.get('dividendYield', None)
                if dy is None and 'dividendRate' in info and last > 0:
                     dr = info.get('dividendRate', 0)
                     if dr: dy = dr / last
                
                if dy is not None:
                    val_pct = dy * 100 if dy < 0.5 else dy
                    div_fmt = f"{val_pct:.2f}%"
                else:
                    div_fmt = "0.00%"
                
                # Beta
                beta = info.get('beta', None)
                if beta: beta_fmt = f"{beta:.2f}"

                # Earnings
                try:
                    cal = t_obj.calendar
                    if isinstance(cal, dict) and 'Earnings Date' in cal:
                        dates = cal['Earnings Date']
                        if len(dates) > 0: next_earn = dates[0].strftime('%d/%m')
                    elif isinstance(cal, pd.DataFrame) and not cal.empty:
                         if 'Earnings Date' in cal.index:
                             val = cal.loc['Earnings Date']
                             if isinstance(val, pd.Series): val = val.iloc[0]
                             next_earn = val.strftime('%d/%m')
                except: next_earn = "N/A"
                
            except: pass

            # Cálculos Técnicos
            diff = last - df_header['Close'].iloc[-2]
            pct = (diff / df_header['Close'].iloc[-2]) * 100
            
            date_30d = datetime.now() - timedelta(days=30)
            start_year = f"{datetime.now().year}-01-01"
            
            m_data = df_header[df_header.index >= date_30d]
            month_change = ((last - m_data['Close'].iloc[0]) / m_data['Close'].iloc[0]) * 100 if not m_data.empty else 0.0
            
            y_data = df_header[df_header.index >= start_year]
            ytd_change = ((last - y_data['Close'].iloc[0]) / y_data['Close'].iloc[0]) * 100 if not y_data.empty else 0.0

            df_header['Log'] = np.log(df_header['Close'] / df_header['Close'].shift(1))
            vol_20 = df_header['Log'].tail(20).std() * np.sqrt(252) * 100
            
            # --- RENDERIZADO ---
            with c_main:
                st.markdown(f"<div style='font-size:20px; color:#E0E0E0; margin-bottom:-5px;'>{company_name}</div>", unsafe_allow_html=True)
                color_p = "#00BBA2" if diff >= 0 else "#FF6C6C"
                st.markdown(f"<div style='display: flex; align-items: baseline; gap: 10px;'><span style='font-size: 38px; font-weight: bold;'>{last:.2f}</span><span style='color:{color_p}; font-size: 20px; font-weight: bold;'>{diff:+.2f} ({pct:+.2f}%)</span></div>", unsafe_allow_html=True)

            with c_ret:
                c_m = "#00BBA2" if month_change >= 0 else "#FF6C6C"
                st.markdown(f"<div style='margin-top:5px; font-size:13px; color:#AAA;'>Mes: <span style='color:{c_m}; font-weight:bold'>{month_change:+.2f}%</span></div>", unsafe_allow_html=True)
                c_y = "#00BBA2" if ytd_change >= 0 else "#FF6C6C"
                st.markdown(f"<div style='font-size:13px; color:#AAA;'>YTD: <span style='color:{c_y}; font-weight:bold'>{ytd_change:+.2f}%</span></div>", unsafe_allow_html=True)

            with c_fund:
                st.markdown(f"<div style='margin-top:5px; font-size:13px; color:#AAA;'>Mkt Cap: <span style='color:white; font-weight:bold'>{mkt_cap_fmt}</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:13px; color:#AAA;'>P/E Ratio: <span style='color:white; font-weight:bold'>{pe_fmt}</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:13px; color:#AAA;'>Div. Yield: <span style='color:#00BBA2; font-weight:bold'>{div_fmt}</span></div>", unsafe_allow_html=True)
                
            with c_risk:
                st.markdown(f"<div style='margin-top:5px; font-size:13px; color:#AAA;'>Volatilidad (20d): <span style='color:white'>{vol_20:.1f}%</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:13px; color:#AAA;'>Beta (5y): <span style='color:white'>{beta_fmt}</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:13px; color:#AAA;'>Próx. Balance: <span style='color:#FFF671; font-weight:bold'>📅 {next_earn}</span></div>", unsafe_allow_html=True)

            st.divider()

            col_chart, col_news = st.columns([2.8, 1]) 

            with col_chart:
                tv_ticker = ticker_input_t3.replace("-", "") 
                if ".BA" in ticker_input_t3: tv_ticker = "BCBA:" + ticker_input_t3.replace(".BA", "")
                
                html_tv = f"""
                <div class="tradingview-widget-container">
                  <div id="tradingview_chart"></div>
                  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                  <script type="text/javascript">
                  new TradingView.widget(
                  {{
                  "width": "100%", "height": 580, "symbol": "{tv_ticker}", "interval": "D", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "es", "toolbar_bg": "#f1f3f6", "enable_publishing": false, "withdateranges": true, "hide_side_toolbar": false, "allow_symbol_change": true, "details": true, "hotlist": true, "calendar": true, "container_id": "tradingview_chart"
                  }}
                  );
                  </script>
                </div>
                """
                components.html(html_tv, height=590) 

            with col_news:
                st.caption("📰 Noticias (Finnhub)")
                # FINNHUB_KEY = "tu_clave_real..."  <-- BORRA ESTO O COMÉNTALO
                try:
                  FINNHUB_KEY = st.secrets["FINNHUB_KEY"] # Busca en la nube
                except:
                  FINNHUB_KEY = "CLAVE_NO_ENCONTRADA" # Por si lo corres local sin configurar 
                
                with st.container(height=600): 
                    if FINNHUB_KEY == "TU_API_KEY_FINNHUB_AQUI":
                        st.warning("Falta API Key.")
                    else:
                        try:
                            fh = finnhub.Client(api_key=FINNHUB_KEY)
                            end = datetime.today().strftime('%Y-%m-%d')
                            start = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
                            news = fh.company_news(ticker_input_t3, _from=start, to=end)
                            
                            if news:
                                for item in news[:15]:
                                    title = item.get('headline', '')
                                    url = item.get('url', '#')
                                    src = item.get('source', 'Finnhub')
                                    date = datetime.fromtimestamp(item['datetime']).strftime('%d/%m')
                                    st.markdown(f"""
                                    <div style="border-bottom: 1px solid #333; padding-bottom: 5px; margin-bottom: 5px;">
                                        <a href="{url}" target="_blank" style="text-decoration:none; color:#FFF; font-weight:bold; font-size:13px;">{title}</a><br>
                                        <span style="font-size:11px; color:#00BBA2;">{src} • {date}</span>
                                    </div>""", unsafe_allow_html=True)
                            else:
                                st.info("Sin noticias recientes.")
                        except:
                            st.error("Error Finnhub.")
        else:
            st.error("Ticker no encontrado en Yahoo.")
    except Exception as e:
        st.error(f"Error Deep Dive: {e}")

# ==============================================================================
# TAB 4: QUANT LAB (CORREGIDO Y ROBUSTO)
# ==============================================================================
with tab4:
    st.header("Laboratorio Cuantitativo")
    opciones = {"1 Año": 1, "2 Años": 2, "3 Años": 3, "5 Años": 5}
    c_t, _ = st.columns([1, 5])
    with c_t:
        sel_t = st.selectbox("Historia", list(opciones.keys()), index=0, key="time_tab4")
    start_corr = datetime.today() - timedelta(days=opciones[sel_t] * 365)

    col_q1, col_q2, col_q3 = st.columns([1, 2.5, 1.5])
    
    # --- COLUMNA 1: REFERENCIA ---
    with col_q1:
        st.subheader("📖 Sectores")
        st.caption("ETF de sectores a modo referencial") 
        data_ref = []
        for t in etfs:
            sec = asset_meta.get(t, {}).get('Sector', 'N/A')
            data_ref.append({'Ticker': t, 'Sector': sec})
        df_ref = pd.DataFrame(data_ref)
        st.dataframe(df_ref, height=600, hide_index=True, use_container_width=True)

    # --- COLUMNA 2: MATRIZ ---
    with col_q2:
        st.subheader("📊 Matriz de Correlación")
        txt_mat = st.text_area("Activos", value="SPY, QQQ, IWM, GLD, BTC-USD, NVDA, XLE, XLF, TSLA", height=70, key="mat_tab4")
        if txt_mat:
            lst_mat = list(set([x.strip().upper() for x in txt_mat.split(',') if x.strip()]))
            if len(lst_mat) > 1:
                try:
                    # Descarga robusta
                    d_mat = yf.download(lst_mat, start=start_corr, progress=False, auto_adjust=True)
                    
                    # Limpieza de MultiIndex (Corrección clave)
                    if isinstance(d_mat.columns, pd.MultiIndex):
                        # Intentamos tomar el nivel 'Close' si existe
                        try:
                            d_mat = d_mat.xs('Close', level=0, axis=1)
                        except:
                            # Si falla, quizás ya son los precios o está en otro nivel
                            if 'Close' in d_mat.columns:
                                d_mat = d_mat['Close']
                    
                    # Si después de limpiar sigue siendo complejo, aplanamos
                    if isinstance(d_mat.columns, pd.MultiIndex):
                        d_mat.columns = d_mat.columns.get_level_values(-1)

                    ret_mat = np.log(d_mat / d_mat.shift(1)).dropna()
                    
                    # Filtramos solo las columnas que tengan datos
                    valid_cols = [c for c in lst_mat if c in ret_mat.columns]
                    ret_mat = ret_mat[valid_cols]

                    if not ret_mat.empty:
                        fig_c = px.imshow(ret_mat.corr(), text_auto=".2f", aspect="auto", 
                                          color_continuous_scale=[(0, "#FF6C6C"), (0.5, "black"), (1, "#00BBA2")], 
                                          range_color=[-1, 1], origin='lower')
                        fig_c.update_layout(height=600, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_c, use_container_width=True)
                except Exception as e: 
                    st.error(f"Error calculando matriz: {e}")

    # --- COLUMNA 3: DISPERSIÓN ---
    with col_q3:
        st.subheader("🔬 Dispersión (Scatter)")
        c1, c2 = st.columns(2)
        tx = c1.text_input("X", value="SPY", key="tx_tab4").upper().strip()
        ty = c2.text_input("Y", value="TSLA", key="ty_tab4").upper().strip()
        
        if tx and ty:
            try:
                # Descarga robusta para solo 2 activos
                ds = yf.download([tx, ty], start=start_corr, progress=False, auto_adjust=True)
                
                # Lógica de limpieza idéntica a la matriz
                if isinstance(ds.columns, pd.MultiIndex):
                    try:
                        ds = ds.xs('Close', level=0, axis=1)
                    except:
                        if 'Close' in ds.columns: ds = ds['Close']
                
                # Aplanado final por seguridad
                if isinstance(ds.columns, pd.MultiIndex):
                     ds.columns = ds.columns.get_level_values(-1)

                rs = np.log(ds / ds.shift(1)).dropna()
                
                # Verificamos que AMBOS tickers estén en las columnas
                if tx in rs.columns and ty in rs.columns:
                    x, y = rs[tx]*100, rs[ty]*100
                    
                    grid_style = dict(showgrid=True, gridwidth=1, gridcolor='rgba(255, 255, 255, 0.1)')

                    def class_r2(r, r2):
                        d = "Directa" if r > 0 else "Inversa"
                        if r2 < 0.5: return f"{d} Débil", "#AAAAAA"
                        elif r2 < 0.7: return f"{d} Moderada", "#FFF671"
                        elif r2 < 0.9: return f"{d} Buena", "#00BBA2"
                        else: return f"{d} Fuerte", "#00FF00"
                    
                    # GRÁFICO 1: GENERAL
                    cv = x.corr(y)
                    r2_gen = cv**2
                    txt, clr = class_r2(cv, r2_gen)
                    f1 = px.scatter(x=x, y=y, trendline="ols", trendline_color_override="#00BBA2", opacity=0.6, title="General")
                    f1.update_traces(marker=dict(size=5, color="#888"))
                    f1.add_annotation(x=0.05, y=0.95, xref="paper", yref="paper", text=f"<b>R = {cv:.2f}</b><br>R² = {r2_gen:.2f}<br><span style='color:{clr}'>{txt}</span>", showarrow=False, bgcolor="rgba(0,0,0,0.7)", align="left")
                    f1.update_layout(height=280, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=30,b=0), xaxis=grid_style, yaxis=grid_style)
                    st.plotly_chart(f1, use_container_width=True)

                    # GRÁFICO 2: SOLO CAÍDAS
                    mask = x < 0
                    xd, yd = x[mask], y[mask]
                    if len(xd) > 10:
                        cd = xd.corr(yd)
                        r2_down = cd**2
                        txtd, clrd = class_r2(cd, r2_down)
                        if r2_down >= 0.7: clrd = "#FF6C6C"
                        f2 = px.scatter(x=xd, y=yd, trendline="ols", trendline_color_override="#FF6C6C", opacity=0.7, title="Solo Caídas (Downside)")
                        f2.update_traces(marker=dict(size=5, color="#FF6C6C"))
                        f2.add_annotation(x=0.05, y=0.95, xref="paper", yref="paper", text=f"<b>R = {cd:.2f}</b><br>R² = {r2_down:.2f}<br><span style='color:{clrd}'>{txtd}</span>", showarrow=False, bgcolor="rgba(0,0,0,0.7)", align="left")
                        f2.update_layout(height=280, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=30,b=0), xaxis=grid_style, yaxis=grid_style)
                        st.plotly_chart(f2, use_container_width=True)
                else:
                    st.warning(f"No hay datos coincidentes para {tx} y {ty}. Verifica los tickers.")
            except Exception as e: 
                st.error(f"Error en Scatter: {e}")

# ==============================================================================
# TAB 5: MACRO ROOM (FRED)
# ==============================================================================
with tab5:
    st.header("Monitor Macroeconómico (USA)")
# FRED_KEY = "tu_clave_real..." <-- BORRA ESTO O COMÉNTALO
try:
    FRED_KEY = st.secrets["FRED_KEY"]
except:
    FRED_KEY = "CLAVE_NO_ENCONTRADA"
    try:
        fred = Fred(api_key=FRED_KEY)
        with st.spinner("Cargando Macro..."):
            cpi = fred.get_series('CPIAUCSL').pct_change(12)*100
            ppi = fred.get_series('PPIFIS').pct_change(12)*100 
            ff = fred.get_series('FEDFUNDS')
            t10 = fred.get_series('DGS10')
            t2 = fred.get_series('DGS2')
            un = fred.get_series('UNRATE')
            sent = fred.get_series('UMCSENT')
            ind = fred.get_series('INDPRO').pct_change(12)*100
            ret = fred.get_series('RSAFS').pct_change(12)*100
            gdp = fred.get_series('GDPC1').pct_change(4)*100
            spread = (t10 - t2).dropna()
            
        start_plot = datetime.today() - timedelta(days=365*10)
        def layout_pro(tit):
            grid_style = dict(showgrid=True, gridwidth=1, gridcolor='rgba(255, 255, 255, 0.1)')
            return dict(title=dict(text=tit, font=dict(size=14, color="white")), height=400, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(range=[start_plot, datetime.today()], **grid_style), yaxis=grid_style, margin=dict(l=20,r=20,t=40,b=20), legend=dict(orientation="h", y=1.05))

        c_m1, c_m2 = st.columns(2)
        with c_m1:
            fi = go.Figure()
            fi.add_trace(go.Scatter(x=cpi.index, y=cpi, name="CPI", line=dict(color='#00BBA2', width=2)))
            fi.add_trace(go.Scatter(x=ppi.index, y=ppi, name="PPI (Final)", line=dict(color='#FFF671', width=1.5)))
            fi.add_hline(y=2, line_dash="dash", line_color="gray")
            fi.update_layout(layout_pro("Inflación (CPI vs PPI)"), yaxis_title="%")
            st.plotly_chart(fi, use_container_width=True)
        with c_m2:
            fr = go.Figure()
            fr.add_trace(go.Scatter(x=ff.index, y=ff, name="Fed Rate", line=dict(color='#00FF00', width=2)))
            fr.add_trace(go.Scatter(x=t10.index, y=t10, name="10Y Bond", line=dict(color='#FFFFFF', width=1.5, dash='dot')))
            fr.update_layout(layout_pro("Tasas"), yaxis_title="%")
            st.plotly_chart(fr, use_container_width=True)

        c_m3, c_m4 = st.columns(2)
        with c_m3:
            fs = go.Figure()
            fs.add_trace(go.Scatter(x=spread.index, y=spread, name="10Y-2Y", line=dict(color='#FFFFFF')))
            fs.add_hline(y=0, line_color="#FF6C6C", line_width=2)
            fs.update_layout(layout_pro("Curva (Spread 10Y-2Y)"))
            st.plotly_chart(fs, use_container_width=True)
        with c_m4:
            fu = go.Figure()
            fu.add_trace(go.Scatter(x=un.index, y=un, name="Desempleo", line=dict(color='#00BFFF', width=2)))
            fu.update_layout(layout_pro("Desempleo"), yaxis_title="%")
            st.plotly_chart(fu, use_container_width=True)

        c_m5, c_m6 = st.columns(2)
        with c_m5:
            fp = go.Figure()
            fp.add_trace(go.Scatter(x=ind.index, y=ind, name="Ind. Prod", line=dict(color='#FF9F40'), fill='tozeroy', fillcolor='rgba(255,159,64,0.1)'))
            fp.add_hline(y=0, line_color="gray")
            fp.update_layout(layout_pro("Producción Ind. (YoY)"), yaxis_title="%")
            st.plotly_chart(fp, use_container_width=True)
        with c_m6:
            fss = go.Figure()
            fss.add_trace(go.Scatter(x=sent.index, y=sent, name="Confianza", line=dict(color='#9966FF')))
            fss.update_layout(layout_pro("Sentimiento Consumidor"), yaxis_title="Idx")
            st.plotly_chart(fss, use_container_width=True)

        c_m7, c_m8 = st.columns(2)
        with c_m7:
            frt = go.Figure()
            frt.add_trace(go.Scatter(x=ret.index, y=ret, name="Retail", line=dict(color='#FF6384')))
            frt.add_hline(y=0, line_color="gray")
            frt.update_layout(layout_pro("Ventas Retail (YoY)"), yaxis_title="%")
            st.plotly_chart(frt, use_container_width=True)
        with c_m8:
            fg = go.Figure()
            fg.add_trace(go.Bar(x=gdp.index, y=gdp, name="GDP", marker_color='#4BC0C0'))
            fg.add_hline(y=0, line_color="gray")
            fg.update_layout(layout_pro("GDP Real (YoY)"), yaxis_title="%")
            st.plotly_chart(fg, use_container_width=True)
    except: st.error("Error FRED.")

# ==============================================================================
# TAB 6: INFORMACIÓN Y METODOLOGÍA
# ==============================================================================
with tab6:
    st.header("📘 Documentación y Guía de Uso")
    
    st.markdown("""
    Esta terminal ha sido diseñada para ofrecer un análisis **360° de los mercados financieros**, integrando análisis técnico, fundamental, cuantitativo y macroeconómico en una sola interfaz.
    
    **Fuentes de Datos:**
    * **Yahoo Finance:** Precios históricos ajustados por dividendos y splits.
    * **FRED (Federal Reserve Economic Data):** Indicadores macroeconómicos oficiales de EE.UU.
    * **Finnhub:** Feed de noticias corporativas y datos de sentimiento.
    """)
    st.divider()

    with st.expander("1. Watchlist Sectorial (Tablero de Control)", expanded=False):
        st.markdown("""
        **¿Para qué sirve?** Permite un "golpe de vista" rápido del estado del mercado global a través de una selección de ETFs representativos de sectores (Tecnología, Energía, Finanzas) y clases de activos (Bonos, Commodities, Monedas).
        * **Sparklines (90d):** Los minigráficos de área muestran la *inercia* de corto plazo.
        """)

    with st.expander("2. Fuerza Relativa (Alpha)", expanded=True):
        st.info("Concepto Clave: Costo de Oportunidad")
        st.markdown("""
        **¿Cómo se calcula?** No graficamos el precio del activo, sino el **Ratio** entre el activo y un Benchmark (ej: `CAT / SPY`).
        * Se parte de una base 100 y se va actualizando en función de la variación del ratio entre dos activos.
        
        **Interpretación:**
        * 📈 **Tendencia Alcista:** El activo se está revalorizando *más rápido* que el activo ancla. Tiene más "fuerza en términos relativos".
        * 📉 **Tendencia Bajista:** El activo puede estar subiendo de precio, pero *menos* que el activo ancla. En términos relativos, estás perdiendo dinero (costo de oportunidad). Es rezagado.
        
        **Ejemplo:** Si el ratio GLD/SPY está para un time frame de 90 días en un valor de **120**, quiere decir que GLD está **+20%** vs el SPY respecto a 90 días atrás.
        """)

    with st.expander("3. Deep Dive (Análisis 360°)", expanded=False):
        st.markdown("""
        **Componentes:**
        * **Análisis Técnico:** Gráfico interactivo (TradingView) para ver soportes, resistencias y tendencias.
        * **Datos Fundamentales Básicos.**
        * **Riesgo:** Volatilidad histórica de 20d y Beta (Sensibilidad al mercado).
        * **News FEED:** Noticias recientes sobre el activo seleccionado.
        """)

    with st.expander("4. Quant Lab (Laboratorio Cuantitativo)", expanded=True):
        st.info("Correlación entre activos")
        st.markdown("""
        * **Coeficiente de regresión ($R$):** Mide la relación lineal entre dos activos (-1 a +1).
            * `+1`: Relación de Retornos positiva.
            * `0`: Sin relación.
            * `-1`: Relación de Retornos negativa.
            
        * **Coeficiente de Determinación ($R^2$):** Indica qué porcentaje del movimiento de un activo es explicado por el otro.  
            *Ejemplo:* Un $R^2$ de 0.80 entre Nvidia y Nasdaq significa que el 80% de la variación de Nvidia se explica por las variaciones en el Nasdaq. 
            Se considera un modelo que explica gran parte de la varianza de los datos a aquel modelo que tenga un valor superior a un $R^2$ > 0.7 (aunque depende del contexto).

        * **Dispersión General vs. Caídas (Downside):**
            * *¿Por qué separar las caídas?*
            * A veces dos activos parecen descorrelacionados en días normales (nube de puntos dispersa), pero cuando el mercado o un Benchmark (Ej: SPY) cae fuerte, la correlación entre activos puede aumentar. 
            * Si uno considera que el mercado puede tener una corrección, es importante tener en cuenta la correlación entre los activos del portfolio y el mercado en momentos de caída.
        """)

    with st.expander("5. Macro Room (Contexto Económico)", expanded=False):
        st.markdown("""
        **¿Para qué sirve?** Monitorea la salud de la economía de EE.UU., como la economía clave que influye en los mercados.
        
        **Indicadores Clave:**
        * **Curva de Tipos (10Y-2Y):** Históricamente, cuando se invierte (cae por debajo de 0), ha predicho recesiones con alta precisión.
        * **Spread Inflacionario (CPI vs PPI):** Muestra si las empresas pueden trasladar sus costos a los consumidores.
        * **Desempleo & Confianza:** Termómetros de la actividad real y el consumo.
        """)

    st.divider()
    
    c_footer1, c_footer2 = st.columns([3, 1])
    
    with c_footer1:
        st.subheader("🚀 Próximamente")
        st.markdown("* Más ratios fundamentales (ROE, ROA, Debt/Equity).")
        st.markdown("* Comparativa de bonos soberanos globales.")
        st.markdown("* ** Edge Journal.**")
        
    with c_footer2:
        st.subheader("📬 Contacto")
        st.markdown("**Desarrollado por Mirko Gulin**")
        st.markdown("📧 mirkogulin2001@gmail.com")

        st.caption("© 2026 Edge Terminal")
