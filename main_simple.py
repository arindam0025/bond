"""
Commodity Price Predictor - Simplified Version
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

# Page configuration
st.set_page_config(
    page_title="Commodity Price Predictor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Commodity symbols
COMMODITIES = {
    'CL=F': {'name': 'WTI Crude Oil', 'category': 'Energy'},
    'BZ=F': {'name': 'Brent Crude Oil', 'category': 'Energy'},
    'NG=F': {'name': 'Natural Gas', 'category': 'Energy'},
    'GC=F': {'name': 'Gold', 'category': 'Metals'},
    'SI=F': {'name': 'Silver', 'category': 'Metals'},
    'HG=F': {'name': 'Copper', 'category': 'Metals'},
    'ZC=F': {'name': 'Corn', 'category': 'Agriculture'},
    'ZS=F': {'name': 'Soybeans', 'category': 'Agriculture'},
}

def load_data(symbol, days=365):
    """Load commodity data from yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=f"{days}d")
        return data
    except Exception as e:
        st.error(f"Error loading {symbol}: {str(e)}")
        return pd.DataFrame()

def main():
    """Main application function."""
    
    st.title("📈 Commodity Price Predictor")
    st.markdown("Welcome to the Commodity Price Predictor - your comprehensive tool for commodity market analysis.")
    
    # Sidebar
    st.sidebar.title("📊 Data Controls")
    
    # Symbol selection
    selected_symbols = st.sidebar.multiselect(
        "Select Commodities",
        list(COMMODITIES.keys()),
        default=list(COMMODITIES.keys())[:3]
    )
    
    # Date range
    days_back = st.sidebar.slider("Days Back", 30, 365, 90)
    
    # Load data button
    if st.sidebar.button("🔄 Load Data"):
        with st.spinner("Loading data..."):
            data_dict = {}
            for symbol in selected_symbols:
                data = load_data(symbol, days_back)
                if not data.empty:
                    data_dict[symbol] = data
            st.session_state.data = data_dict
            st.success(f"Loaded data for {len(data_dict)} commodities")
    
    # Check if data is loaded
    if 'data' not in st.session_state or not st.session_state.data:
        st.warning("Please load data first using the sidebar controls.")
        return
    
    data = st.session_state.data
    
    # Key Metrics
    st.subheader("📊 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Commodities", len(data))
    
    with col2:
        total_data_points = sum(len(df) for df in data.values())
        st.metric("Total Data Points", f"{total_data_points:,}")
    
    with col3:
        avg_vol = np.mean([df['Close'].pct_change().std() * np.sqrt(252) 
                          for df in data.values() if 'Close' in df.columns])
        st.metric("Avg Volatility", f"{avg_vol:.1%}")
    
    with col4:
        st.metric("Last Update", datetime.now().strftime("%Y-%m-%d"))
    
    # Market Overview
    st.subheader("🌍 Market Overview")
    
    # Create summary table
    summary_data = []
    for symbol, df in data.items():
        if df.empty or 'Close' not in df.columns:
            continue
        
        # Calculate metrics
        last_close = df['Close'].iloc[-1]
        returns_20d = df['Close'].pct_change(20).iloc[-1]
        vol_20d = df['Close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252)
        
        summary_data.append({
            'Symbol': symbol,
            'Name': COMMODITIES[symbol]['name'],
            'Category': COMMODITIES[symbol]['category'],
            'Last Close': f"${last_close:.2f}",
            '20d Return': f"{returns_20d:.1%}",
            '20d Vol': f"{vol_20d:.1%}"
        })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)
    
    # Price Charts
    st.subheader("📈 Price Charts")
    
    # Select commodities to display
    chart_symbols = st.multiselect(
        "Select commodities to display",
        list(data.keys()),
        default=list(data.keys())[:3]
    )
    
    if chart_symbols:
        # Create tabs for each commodity
        tabs = st.tabs(chart_symbols)
        
        for i, symbol in enumerate(chart_symbols):
            with tabs[i]:
                if symbol in data and not data[symbol].empty:
                    df = data[symbol]
                    
                    # Create price chart
                    import plotly.graph_objects as go
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df['Close'],
                        mode='lines',
                        name='Price',
                        line=dict(color='#1f77b4', width=2)
                    ))
                    
                    fig.update_layout(
                        title=f"{symbol} Price Chart",
                        xaxis_title='Date',
                        yaxis_title='Price',
                        template='plotly_white',
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Price statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Current Price", f"${df['Close'].iloc[-1]:.2f}")
                    with col2:
                        returns_1d = df['Close'].pct_change().iloc[-1]
                        st.metric("1d Return", f"{returns_1d:.2%}")
                    with col3:
                        returns_20d = df['Close'].pct_change(20).iloc[-1]
                        st.metric("20d Return", f"{returns_20d:.2%}")
                    with col4:
                        vol_20d = df['Close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252)
                        st.metric("20d Volatility", f"{vol_20d:.1%}")
    
    # Data Export
    st.subheader("💾 Data Export")
    
    if st.button("📥 Download All Data as CSV"):
        # Combine all data
        all_data = []
        for symbol, df in data.items():
            df_copy = df.copy()
            df_copy['Symbol'] = symbol
            df_copy = df_copy.reset_index()
            all_data.append(df_copy)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            csv = combined_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"commodity_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    # Footer
    st.markdown("---")
    st.markdown("**Commodity Price Predictor** - Built with Streamlit")

if __name__ == "__main__":
    main()
