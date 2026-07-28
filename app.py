"""
Voltwise - Solar PV Production Dashboard
Real-time solar production forecasting with AI-powered battery management
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Reload environment variables
load_dotenv(override=True)

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from config import (
    IRRADIATION_THRESHOLD_HIGH, IRRADIATION_THRESHOLD_MEDIUM,
    WEATHER_CONDITIONS, OPENROUTER_API_KEY
)
from weather_api import WeatherDataFetcher
from model_utils import ModelManager, DemoPredictionEngine
from energy_recommendation_agent import EnergyRecommendationAgent

# Page configuration
st.set_page_config(
    page_title="Voltwise - Solar Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .stMetric label {
        color: #1a1a1a !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    .stMetric > div > div {
        color: #0d0d0d !important;
        font-weight: 700 !important;
        font-size: 24px !important;
    }
    [data-testid="stMetricValue"] {
        color: #0d0d0d !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #1a1a1a !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def initialize_components():
    """Initialize model and other components"""
    model_manager = ModelManager()
    
    # If model not loaded, use demo engine
    if model_manager.model is None:
        prediction_engine = DemoPredictionEngine
        model_status = "Using Demo Mode (no trained model loaded)"
    else:
        prediction_engine = model_manager
        model_status = "Fine-tuned XGBoost Model Loaded"
    
    return model_manager, prediction_engine, model_status

def main():
    """Main dashboard application"""
    
    # Header
    logo_col, title_col = st.columns([1, 8])
    with logo_col:
        logo_path = Path(__file__).parent / "assets" / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=64)
    with title_col:
        st.title("Voltwise")
    st.markdown("**AI-Powered Solar Energy & Battery Management Dashboard**")
    
    # Initialize components
    model_manager, prediction_engine, model_status = initialize_components()
    
    # Initialize session state for first-time setup
    if 'dashboard_initialized' not in st.session_state:
        st.session_state['dashboard_initialized'] = False
    
    # Sidebar configuration
    st.sidebar.title("⚙️ Settings")
    st.sidebar.divider()
    
    # Location input
    st.sidebar.subheader("📍 Location")
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        city = st.text_input("City Name", value="Sfax", key="city_input").strip()
    with col2:
        country = st.text_input("Country Code", value="TN", max_chars=2, key="country_input").strip().upper()
    
    # Battery Storage Configuration
    st.sidebar.subheader("🔋 Battery Storage")
    has_battery = st.sidebar.checkbox("Enable Battery Storage", value=False, key="has_battery")
    
    if has_battery:
        battery_capacity = st.sidebar.number_input(
            "Battery Capacity (kWh)",
            min_value=1.0,
            max_value=100.0,
            value=10.0,
            step=0.5,
            key="battery_capacity"
        )
        battery_level = st.sidebar.slider(
            "Current Battery Level (%)",
            min_value=0,
            max_value=100,
            value=50,
            step=5,
            key="battery_level"
        )
        daily_consumption = st.sidebar.number_input(
            "Daily Consumption (kWh)",
            min_value=1.0,
            max_value=200.0,
            value=20.0,
            step=1.0,
            key="daily_consumption"
        )
        
        # Calculate actual battery level in kWh
        battery_current_kwh = (battery_level / 100) * battery_capacity
        
        st.sidebar.info(
            f"**Battery Status:**\n"
            f"- Capacity: {battery_capacity} kWh\n"
            f"- Current: {battery_current_kwh:.2f} kWh\n"
            f"- Available: {battery_capacity - battery_current_kwh:.2f} kWh"
        )
    
    st.sidebar.divider()
    
    # Model status
    st.sidebar.subheader("🤖 Model Status")
    st.sidebar.info(f"Status: {model_status}")
    
    # Fetch button
    if st.sidebar.button("🔄 Fetch Weather & Predict", use_container_width=True):
        st.session_state['fetch_data'] = True
    
    # Main content
    st.divider()
    
    # Check if data should be fetched
    if st.session_state.get('fetch_data', False):
        with st.spinner("Fetching weather data..."):
            try:
                fetcher = WeatherDataFetcher()
                current_result = fetcher.get_current_weather(city, country)
                forecast_result = fetcher.get_forecast(city, country, hours=48)
                
                if current_result['status'] == 'error':
                    error_msg = current_result.get('message', 'Unknown error')
                    st.error(f"❌ Weather API Error: {error_msg}")
                    
                    # Provide helpful diagnostics
                    if '404' in error_msg:
                        st.warning(f"⚠️ Location not found: '{city}, {country}'")
                        st.info("**Try these fixes:**\n"
                                "1. Check spelling (e.g., 'Hammamet' not 'hammemet')\n"
                                "2. Use major cities (API free tier has limited coverage)\n"
                                "3. Try just the city name without country code\n"
                                "4. Common Tunisia cities: Sfax, Tunis, Sousse, Hammamet")
                    elif '401' in error_msg:
                        st.error("Invalid WEATHER_API_KEY - check your .env file")
                    else:
                        st.info("Please check your WEATHER_API_KEY in the .env file")
                    return
                
                # Extract data
                current_weather = current_result['data']
                forecast_data = forecast_result['data']
                
                # Format data for model
                current_formatted = fetcher.format_for_model(current_weather)
                
                # Make predictions
                current_prediction = prediction_engine.predict(current_formatted)
                
                # Prepare forecast data
                forecast_formatted = []
                forecast_predictions = []
                
                for fcast in forecast_data:
                    formatted = fetcher.format_for_model(fcast)
                    forecast_formatted.append(formatted)
                    pred = prediction_engine.predict(formatted)
                    forecast_predictions.append(pred)
                
                # Store in session state
                st.session_state['current_weather'] = current_weather
                st.session_state['current_formatted'] = current_formatted
                st.session_state['current_prediction'] = current_prediction
                st.session_state['forecast_data'] = forecast_data
                st.session_state['forecast_formatted'] = forecast_formatted
                st.session_state['forecast_predictions'] = forecast_predictions
                st.session_state['fetch_data'] = False
                st.session_state['dashboard_initialized'] = True
                st.success("✓ Data fetched successfully!")
                st.rerun()
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Make sure you have set WEATHER_API_KEY in your .env file")
                return
    
    # Display results if data is available
    if 'current_prediction' in st.session_state:
        current_weather = st.session_state['current_weather']
        current_prediction = st.session_state['current_prediction']
        forecast_predictions = st.session_state['forecast_predictions']
        forecast_data = st.session_state['forecast_data']
        current_formatted = st.session_state['current_formatted']
        
        # Current Weather Section
        st.subheader("🌤️ Current Conditions & Solar Output")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Temperature",
                f"{current_weather['temperature']:.1f}°C",
                delta=f"Feels like optimal" if 15 <= current_weather['temperature'] <= 35 else "⚠️ Suboptimal"
            )
        
        with col2:
            st.metric(
                "Humidity",
                f"{current_weather['humidity']:.0f}%",
                delta="Good" if 40 <= current_weather['humidity'] <= 70 else "Check"
            )
        
        with col3:
            st.metric(
                "Wind Speed",
                f"{current_weather['wind_speed']:.1f} m/s",
                delta="Moderate" if current_weather['wind_speed'] < 5 else "High"
            )
        
        with col4:
            st.metric(
                "Cloud Coverage",
                f"{current_weather['clouds']:.0f}%",
                delta="Clear" if current_weather['clouds'] < 20 else "Cloudy"
            )
        
        with col5:
            st.metric(
                "Production",
                f"{current_prediction:.2f} kW",
                delta="High" if current_prediction > 1.0 else "Low"
            )
        
        # Weather Description
        st.info(f"🌤️ **Condition:** {current_weather['condition']} - {current_weather['description']}")
        
        st.divider()
        
        # Predictions & Forecast
        st.subheader("📈 24-Hour Solar Production Forecast")
        
        # Prepare forecast dataframe
        forecast_df = pd.DataFrame({
            'Time': [d['timestamp'] for d in forecast_data],
            'Predicted Power (kW)': forecast_predictions[:len(forecast_data)],
            'Temperature (°C)': [d['temperature'] for d in forecast_data],
            'Cloud Coverage (%)': [d['clouds'] for d in forecast_data],
            'Condition': [d['condition'] for d in forecast_data]
        })
        
        # Power prediction chart
        fig_power = go.Figure()
        
        fig_power.add_trace(go.Scatter(
            x=forecast_df['Time'],
            y=forecast_df['Predicted Power (kW)'],
            mode='lines+markers',
            name='Predicted Power',
            line=dict(color='#FDB462', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(253, 180, 98, 0.2)'
        ))
        
        # Add threshold lines
        fig_power.add_hline(
            y=IRRADIATION_THRESHOLD_HIGH/400,
            line_dash="dash",
            line_color="green",
            annotation_text="High Production",
            annotation_position="right"
        )
        
        fig_power.update_layout(
            title="Solar Power Production Forecast",
            xaxis_title="Time",
            yaxis_title="Power (kW)",
            hovermode='x unified',
            height=400,
            template="plotly_white",
            showlegend=True
        )
        
        st.plotly_chart(fig_power, use_container_width=True)
        
        # Forecast table
        st.subheader("📊 Detailed Forecast Table")
        display_df = forecast_df.copy()
        display_df['Time'] = display_df['Time'].dt.strftime('%Y-%m-%d %H:%M')
        display_df['Predicted Power (kW)'] = display_df['Predicted Power (kW)'].round(3)
        display_df['Temperature (°C)'] = display_df['Temperature (°C)'].round(1)
        display_df['Cloud Coverage (%)'] = display_df['Cloud Coverage (%)'].round(0).astype(int)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Power Analysis
        st.subheader("⚡ Power Production Analysis")
        display_simple_analysis(current_prediction, forecast_predictions, current_formatted)
        
        st.divider()
        
        # AI-Powered Battery Recommendation Agent
        if st.session_state.get('has_battery', False) and OPENROUTER_API_KEY:
            st.subheader("🤖 AI Energy Recommendation Agent")
            st.markdown("*Expert analysis using OpenRouter API Agent with persona prompting*")
            
            if st.button("💡 Get AI Recommendation", use_container_width=True, key="get_recommendation"):
                with st.spinner("🔍 Analyzing forecast data and generating recommendation..."):
                    try:
                        # Initialize the recommendation agent
                        agent = EnergyRecommendationAgent(OPENROUTER_API_KEY)
                        
                        # Prepare battery parameters
                        battery_capacity = st.session_state.get('battery_capacity', 10.0)
                        battery_level_percent = st.session_state.get('battery_level', 50)
                        battery_current_kwh = (battery_level_percent / 100) * battery_capacity
                        daily_consumption = st.session_state.get('daily_consumption', 20.0)
                        
                        # Get AI recommendation
                        recommendation_result = agent.analyze_forecast_and_recommend(
                            current_production=float(current_prediction),
                            forecast_data=forecast_data,
                            battery_capacity=battery_capacity,
                            battery_current_level=battery_current_kwh,
                            daily_consumption_kwh=daily_consumption,
                            has_battery_storage=True
                        )
                        
                        # Store in session state for display
                        st.session_state['recommendation_result'] = recommendation_result
                        st.success("✓ Recommendation generated!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error generating recommendation: {str(e)}")
                        st.info("Make sure you have set the GEMINI_API_KEY in your .env file")
            
            # Display recommendation if available
            if 'recommendation_result' in st.session_state:
                rec = st.session_state['recommendation_result']
                
                if rec['status'] == 'success':
                    recommendation = rec.get('recommendation', {})
                    
                    # Display action in prominent style
                    action = recommendation.get('action', 'MAINTAIN')
                    confidence = recommendation.get('confidence', 'Medium')
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Color code based on action
                        if action == "CHARGE":
                            color = "🟢"
                            action_text = "CHARGE BATTERY"
                        elif action == "DISCHARGE":
                            color = "🔴"
                            action_text = "DISCHARGE BATTERY"
                        else:
                            color = "🟡"
                            action_text = "MAINTAIN STATUS"
                        
                        st.markdown(f"### {color} {action_text}")
                    
                    with col2:
                        st.metric("Confidence Level", confidence)
                    
                    with col3:
                        st.metric("Timestamp", rec['timestamp'][:10])
                    
                    st.divider()
                    
                    # Display full analysis
                    st.subheader("📋 Expert Analysis")
                    
                    with st.expander("View Full AI Analysis", expanded=True):
                        analysis_text = recommendation.get('full_analysis', '')
                        # Always show the full analysis - this is what the AI actually said
                        if analysis_text:
                            st.markdown(analysis_text)
                        else:
                            st.warning("No analysis text available")
                    
                    # Display battery info
                    battery_info = rec.get('battery_info', {})
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Battery Level",
                            f"{battery_info.get('charge_percentage', 0):.1f}%",
                            f"{battery_info.get('current_level_kwh', 0):.2f} kWh"
                        )
                    
                    with col2:
                        st.metric(
                            "Battery Capacity",
                            f"{battery_info.get('capacity_kwh', 0):.2f} kWh"
                        )
                    
                    with col3:
                        available = (battery_info.get('capacity_kwh', 0) - 
                                   battery_info.get('current_level_kwh', 0))
                        st.metric(
                            "Available Capacity",
                            f"{available:.2f} kWh"
                        )
                
                elif rec['status'] == 'error':
                    st.error(f"Error: {rec.get('message', 'Unknown error')}")
        
        elif st.session_state.get('has_battery', False) and not OPENROUTER_API_KEY:
            st.warning(
                "🔑 **OpenRouter API Key Required**\n\n"
                "To enable AI-powered recommendations, please add:\n"
                "`OPENROUTER_API_KEY=your_key_here` to your `.env` file\n"
                "and restart the application"
            )
        
        st.divider()
        
        # Weather Forecast Visualization
        st.subheader("🌡️ Weather Forecast")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(
                x=forecast_df['Time'],
                y=forecast_df['Temperature (°C)'],
                mode='lines+markers',
                name='Temperature',
                line=dict(color='#FF6B6B'),
                fill='tozeroy'
            ))
            fig_temp.update_layout(
                title="Temperature Forecast",
                xaxis_title="Time",
                yaxis_title="Temperature (°C)",
                hovermode='x unified',
                height=350,
                template="plotly_white"
            )
            st.plotly_chart(fig_temp, use_container_width=True)
        
        with col2:
            fig_clouds = go.Figure()
            fig_clouds.add_trace(go.Scatter(
                x=forecast_df['Time'],
                y=forecast_df['Cloud Coverage (%)'],
                mode='lines+markers',
                name='Cloud Coverage',
                line=dict(color='#4ECDC4'),
                fill='tozeroy'
            ))
            fig_clouds.update_layout(
                title="Cloud Coverage Forecast",
                xaxis_title="Time",
                yaxis_title="Coverage (%)",
                hovermode='x unified',
                height=350,
                template="plotly_white"
            )
            st.plotly_chart(fig_clouds, use_container_width=True)
        
        # Summary Statistics
        st.subheader("📊 Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Avg Power (24h)",
                f"{np.mean(forecast_predictions):.2f} kW",
                delta=f"±{np.std(forecast_predictions):.2f} σ"
            )
        
        with col2:
            st.metric(
                "Peak Power",
                f"{np.max(forecast_predictions):.2f} kW",
                delta=f"at {forecast_df.loc[forecast_df['Predicted Power (kW)'].idxmax(), 'Time'].strftime('%H:%M')}"
            )
        
        with col3:
            total_energy = sum(forecast_predictions) * 3 / 1000  # 3-hour intervals
            st.metric(
                "Est. Energy (24h)",
                f"{total_energy:.2f} kWh"
            )
        
        with col4:
            st.metric(
                "Avg Temperature",
                f"{np.mean(forecast_df['Temperature (°C)']):.1f}°C",
                delta=f"Max: {np.max(forecast_df['Temperature (°C)']):.1f}°C"
            )
        

    
    else:
        # Initial state - Setup Guide
        st.success("✨ Welcome to Voltwise Dashboard!")
        
        st.markdown("""
        ### 🚀 Quick Start Guide
        
        Your solar energy forecasting dashboard is ready. Follow these steps to get started:
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚙️ Step 1: Configure Settings")
            st.markdown("""
            - **📍 Location**: Enter your city name and country code
            - **🔋 Battery**: Enable battery storage (optional)
            - Check **Model Status** on the sidebar
            """)
        
        with col2:
            st.subheader("🔄 Step 2: Fetch Data")
            st.markdown("""
            - Click the **"Fetch Weather & Predict"** button
            - Dashboard will load real-time weather data
            - AI predictions will be generated automatically
            """)
        
        st.divider()
        
        st.subheader("📊 What You'll See After Fetching:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 🌤️ Current Conditions
            - Temperature & Humidity
            - Wind Speed & Cloud Cover
            - Solar Production (kW)
            """)
        
        with col2:
            st.markdown("""
            ### 📈 24-Hour Forecast
            - Hourly power predictions
            - Weather conditions
            - Production analysis
            """)
        
        with col3:
            st.markdown("""
            ### 🤖 AI Recommendations
            - Smart battery management
            - Charge/discharge advice
            - Energy optimization
            """)
        
        st.divider()
        st.info("""
        **✓ Setup Status:**
        - Weather API: ✅ Configured
        - OpenRouter API: ✅ Configured
        - Model: {} 
        
        You're ready to start! Click the button in the sidebar →
        """.format(model_status))

def display_simple_analysis(current_prediction: float, forecast_predictions: list, current_formatted: dict):
    """Display simple power production analysis"""
    
    # Calculate metrics
    avg_forecast = np.mean(forecast_predictions) if forecast_predictions else 0
    max_forecast = np.max(forecast_predictions) if forecast_predictions else 0
    irradiation = current_formatted.get('Irradiation transitoire pente(W/㎡)', 0)
    cloud_cover = current_formatted.get('Cloud Coverage (%)', 0)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.metric("Current Power", f"{current_prediction:.2f} kW")
    
    with col2:
        st.metric("24h Average", f"{avg_forecast:.2f} kW")
    
    with col3:
        st.metric("Peak Forecast", f"{max_forecast:.2f} kW")
    
    # Analysis details
    st.subheader("📊 Production Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Current Conditions:**
        - Irradiation: {irradiation:.0f} W/m²
        - Cloud Cover: {cloud_cover:.0f}%
        - Temperature: {current_formatted.get('Température ambiante(℃)', 'N/A')}°C
        - Wind Speed: {current_formatted.get('Vitesse vent(m/s)', 'N/A')} m/s
        """)
    
    with col2:
        # Simple recommendation based on irradiance
        if irradiation > IRRADIATION_THRESHOLD_HIGH:
            status = "🟢 High Production"
            advice = "Excellent conditions for power generation"
        elif irradiation > IRRADIATION_THRESHOLD_MEDIUM:
            status = "🟡 Medium Production"
            advice = "Moderate conditions, some cloud cover expected"
        else:
            status = "🔴 Low Production"
            advice = "Low irradiance, overcast conditions"
        
        st.markdown(f"""
        **Production Status:**
        - {status}
        - {advice}
        - Next 24h Average: {avg_forecast:.2f} kW
        """)

if __name__ == "__main__":
    main()
