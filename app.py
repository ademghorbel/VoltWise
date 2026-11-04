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
import theme
from theme import ACCENT, ACCENT_SOFT, AMBER, STEEL

# Page configuration
st.set_page_config(
    page_title="Voltwise - Solar Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Red noir theme (CSS + Plotly template), see theme.py
theme.apply_theme()
CHART_TEMPLATE = "voltwise_noir"

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
    
    # Initialize components
    model_manager, prediction_engine, model_status = initialize_components()
    
    # Initialize session state for first-time setup
    if 'dashboard_initialized' not in st.session_state:
        st.session_state['dashboard_initialized'] = False
    
    # Header
    if 'current_prediction' in st.session_state:
        place = f"{st.session_state.get('city_input', 'Sfax')}, {st.session_state.get('country_input', 'TN')}"
        theme.hero(True, f"Live forecast · {place}", compact=True)
    else:
        theme.hero(model_manager.model is not None, model_status)
    
    # Location search bar under the hero. A form, so pressing Enter fetches too.
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        with st.form("location_form", clear_on_submit=False):
            col_city, col_code, col_go = st.columns([4.6, 1.2, 2.6])
            with col_city:
                city = st.text_input("City", value="Sfax", key="city_input",
                                     placeholder="City, e.g. Sfax", label_visibility="collapsed").strip()
            with col_code:
                country = st.text_input("Country code", value="TN", max_chars=2, key="country_input",
                                        placeholder="TN", label_visibility="collapsed").strip().upper()
            with col_go:
                if st.form_submit_button("Fetch forecast  →", use_container_width=True):
                    st.session_state['fetch_data'] = True
        
        # Battery settings, tucked away under the bar
        with st.expander("Battery storage (optional)"):
            has_battery = st.checkbox("I have battery storage", value=False, key="has_battery")
            if has_battery:
                b1, b2, b3 = st.columns(3)
                with b1:
                    battery_capacity = st.number_input("Capacity (kWh)", min_value=1.0, max_value=100.0,
                                                       value=10.0, step=0.5, key="battery_capacity")
                with b2:
                    battery_level = st.slider("Current level (%)", min_value=0, max_value=100,
                                              value=50, step=5, key="battery_level")
                with b3:
                    daily_consumption = st.number_input("Daily use (kWh)", min_value=1.0, max_value=200.0,
                                                        value=20.0, step=1.0, key="daily_consumption")
                battery_current_kwh = (battery_level / 100) * battery_capacity
                st.caption(f"{battery_current_kwh:.2f} kWh stored · "
                           f"{battery_capacity - battery_current_kwh:.2f} kWh free of {battery_capacity} kWh")
    
    # Check if data should be fetched
    if st.session_state.get('fetch_data', False):
        with st.spinner("Fetching weather data..."):
            try:
                fetcher = WeatherDataFetcher()
                current_result = fetcher.get_current_weather(city, country)
                forecast_result = fetcher.get_forecast(city, country, hours=48)
                
                if current_result['status'] == 'error':
                    error_msg = current_result.get('message', 'Unknown error')
                    st.error(f"Weather data error: {error_msg}")
                    
                    # Provide helpful diagnostics
                    if '404' in error_msg:
                        st.warning(f"⚠️ Location not found: '{city}, {country}'")
                        st.info("**Try these fixes:**\n"
                                "1. Check spelling (e.g., 'Hammamet' not 'hammemet')\n"
                                "2. Use major cities (API free tier has limited coverage)\n"
                                "3. Try just the city name without country code\n"
                                "4. Common Tunisia cities: Sfax, Tunis, Sousse, Hammamet")
                    elif '401' in error_msg:
                        st.error("The weather service refused the request, try again in a moment")
                    else:
                        st.info("Check your internet connection and try again")
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
                st.info("Check your internet connection and try again")
                return
    
    # Display results if data is available
    if 'current_prediction' in st.session_state:
        current_weather = st.session_state['current_weather']
        current_prediction = st.session_state['current_prediction']
        forecast_predictions = st.session_state['forecast_predictions']
        forecast_data = st.session_state['forecast_data']
        current_formatted = st.session_state['current_formatted']
        
        # Current Weather Section
        theme.section("Right now", "Current conditions & <span>solar output</span>",
                      f"{current_weather['condition']} · {current_weather['description']}")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Temperature",
                f"{current_weather['temperature']:.1f}°C",
                delta="Optimal" if 15 <= current_weather['temperature'] <= 35 else "⚠️ Suboptimal"
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
        
        st.divider()

        # Predictions & Forecast
        theme.section("Forecast", "Solar production, <span>next 48 hours</span>")
        
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
            line=dict(color=ACCENT, width=2.5, shape='spline'),
            marker=dict(size=6, color='#000', line=dict(color=ACCENT, width=2)),
            fill='tozeroy',
            fillcolor=ACCENT_SOFT
        ))

        # Add threshold lines
        fig_power.add_hline(
            y=IRRADIATION_THRESHOLD_HIGH/400,
            line_dash="dot",
            line_color="rgba(255,255,255,0.35)",
            annotation_text="High production",
            annotation_position="top right",
            annotation_font_color="#a1a1aa"
        )

        fig_power.update_layout(
            title="Predicted PV power",
            xaxis_title="Time",
            yaxis_title="Power (kW)",
            hovermode='x unified',
            height=420,
            template=CHART_TEMPLATE,
            showlegend=False
        )
        
        st.plotly_chart(fig_power, use_container_width=True)
        
        # Forecast table
        theme.section("Data", "Detailed forecast")
        display_df = forecast_df.copy()
        display_df['Time'] = display_df['Time'].dt.strftime('%Y-%m-%d %H:%M')
        display_df['Predicted Power (kW)'] = display_df['Predicted Power (kW)'].round(3)
        display_df['Temperature (°C)'] = display_df['Temperature (°C)'].round(1)
        display_df['Cloud Coverage (%)'] = display_df['Cloud Coverage (%)'].round(0).astype(int)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Power Analysis
        theme.section("Analysis", "Power <span>production</span>")
        display_simple_analysis(current_prediction, forecast_predictions, current_formatted)
        
        st.divider()
        
        # AI-Powered Battery Recommendation Agent
        if st.session_state.get('has_battery', False) and OPENROUTER_API_KEY:
            theme.section("AI agent", "Battery <span>recommendation</span>",
                          "Expert analysis by an OpenRouter agent with persona prompting")

            if st.button("Get AI Recommendation  →", use_container_width=True, key="get_recommendation"):
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
                        st.info("Make sure you have set the OPENROUTER_API_KEY in your .env file")
            
            # Display recommendation if available
            if 'recommendation_result' in st.session_state:
                rec = st.session_state['recommendation_result']
                
                if rec['status'] == 'success':
                    recommendation = rec.get('recommendation', {})
                    
                    # Display action in prominent style
                    action = recommendation.get('action', 'MAINTAIN')
                    confidence = recommendation.get('confidence', 'Medium')
                    
                    action_text = {
                        "CHARGE": "Charge battery",
                        "DISCHARGE": "Discharge battery",
                    }.get(action, "Maintain status")
                    # Solid red banner for an action to take, quiet banner for "maintain"
                    banner_cls = "vw-banner calm" if action not in ("CHARGE", "DISCHARGE") else "vw-banner"

                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.markdown(f'<div class="{banner_cls}"><div class="k">Recommended action</div>'
                                    f'<div class="v">{action_text}</div></div>', unsafe_allow_html=True)

                    with col2:
                        st.metric("Confidence Level", confidence)

                    with col3:
                        st.metric("Timestamp", rec['timestamp'][:10])

                    with st.expander("Full AI analysis", expanded=True):
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
                "**OpenRouter API Key Required**\n\n"
                "To enable AI-powered recommendations, please add:\n"
                "`OPENROUTER_API_KEY=your_key_here` to your `.env` file\n"
                "and restart the application"
            )
        
        st.divider()
        
        # Weather Forecast Visualization
        theme.section("Weather", "What the sky is <span>doing</span>")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(
                x=forecast_df['Time'],
                y=forecast_df['Temperature (°C)'],
                mode='lines+markers',
                name='Temperature',
                line=dict(color=AMBER, width=2, shape='spline'),
                marker=dict(size=5),
                fill='tozeroy',
                fillcolor='rgba(245, 177, 76, 0.10)'
            ))
            fig_temp.update_layout(
                title="Temperature",
                xaxis_title="Time",
                yaxis_title="Temperature (°C)",
                hovermode='x unified',
                height=350,
                template=CHART_TEMPLATE
            )
            st.plotly_chart(fig_temp, use_container_width=True)
        
        with col2:
            fig_clouds = go.Figure()
            fig_clouds.add_trace(go.Scatter(
                x=forecast_df['Time'],
                y=forecast_df['Cloud Coverage (%)'],
                mode='lines+markers',
                name='Cloud Coverage',
                line=dict(color=STEEL, width=2, shape='spline'),
                marker=dict(size=5),
                fill='tozeroy',
                fillcolor='rgba(122, 162, 200, 0.10)'
            ))
            fig_clouds.update_layout(
                title="Cloud coverage",
                xaxis_title="Time",
                yaxis_title="Coverage (%)",
                hovermode='x unified',
                height=350,
                template=CHART_TEMPLATE
            )
            st.plotly_chart(fig_clouds, use_container_width=True)
        
        # Summary Statistics
        theme.section("Summary", "Statistics")
        
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
            # Predictions are in kW at 3-hour steps: first 8 steps = 24h, kW x 3h = kWh
            total_energy = sum(forecast_predictions[:8]) * 3
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
        # Initial state: what the dashboard does, plus a real check of the setup
        theme.section("Get started", "One dashboard for your <span>solar system</span>",
                      "Type your city in the search bar above, then hit Fetch forecast.")
        
        model_ok = model_manager.model is not None
        status = (theme.chip("Weather: Open-Meteo, no key needed", True)
                  + theme.chip("OpenRouter API key" if OPENROUTER_API_KEY else "OpenRouter API key missing", bool(OPENROUTER_API_KEY))
                  + theme.chip("XGBoost model loaded" if model_ok else "Demo mode, no model", model_ok))
        steps = ('<div class="vw-steps">'
                 '<div class="vw-step"><b>01</b>Type your city and country code above</div>'
                 '<div class="vw-step"><b>02</b>Optionally enable battery storage</div>'
                 '<div class="vw-step"><b>03</b>Fetch weather and generate the forecast</div>'
                 f'</div><div class="vw-status">{status}</div>')
        
        st.markdown('<div class="vw-bento">'
            + theme.card("sun", "Solar production forecasting",
                         "Live Open-Meteo conditions go through a fine-tuned XGBoost model trained on "
                         "real PV plant data from Sfax, giving you power output now and over the next two days.",
                         size="big", extra=steps)
            + theme.card("chart", "48-hour outlook",
                         "Predicted power, temperature and cloud cover in one view, with a detailed table.",
                         size="wide", glow=STEEL)
            + theme.card("battery", "Battery aware",
                         "Track capacity, charge level and daily consumption.", glow=AMBER)
            + theme.card("bot", "AI recommendations",
                         "An OpenRouter agent tells you when to charge or discharge.")
            + '</div>', unsafe_allow_html=True)
    
    theme.footer()

def display_simple_analysis(current_prediction: float, forecast_predictions: list, current_formatted: dict):
    """Display simple power production analysis"""
    
    # Calculate metrics
    avg_forecast = np.mean(forecast_predictions) if forecast_predictions else 0
    max_forecast = np.max(forecast_predictions) if forecast_predictions else 0
    irradiation = current_formatted.get('Irradiation transitoire pente(W/㎡)', 0)
    cloud_cover = current_formatted.get('cloud_coverage', 0)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.metric("Current Power", f"{current_prediction:.2f} kW")
    
    with col2:
        st.metric("24h Average", f"{avg_forecast:.2f} kW")
    
    with col3:
        st.metric("Peak Forecast", f"{max_forecast:.2f} kW")
    
    st.write("")
    col1, col2 = st.columns(2)
    
    def rows(items):
        return "".join(f'<div class="vw-row"><span>{k}</span><span>{v}</span></div>' for k, v in items)
    
    with col1:
        st.markdown('<div class="vw-list"><div class="k">Current conditions</div>' + rows([
            ("Irradiation", f"{irradiation:.0f} W/m²"),
            ("Cloud cover", f"{cloud_cover:.0f}%"),
            ("Temperature", f"{current_formatted.get('Température ambiante(℃)', 0):.1f}°C"),
            ("Wind speed", f"{current_formatted.get('Vitesse vent(m/s)', 0):.1f} m/s"),
        ]) + '</div>', unsafe_allow_html=True)
    
    with col2:
        # Simple recommendation based on irradiance
        if irradiation <= 0:
            status = "No production"
            advice = "Night time, no sunlight"
        elif irradiation > IRRADIATION_THRESHOLD_HIGH:
            status = "High production"
            advice = "Excellent conditions for power generation"
        elif irradiation > IRRADIATION_THRESHOLD_MEDIUM:
            status = "Medium production"
            advice = "Moderate conditions, some cloud cover expected"
        else:
            status = "Low production"
            advice = "Low irradiance, overcast conditions"
        
        st.markdown('<div class="vw-list"><div class="k">Production status</div>' + rows([
            ("Status", status),
            ("Outlook", advice),
            ("Next 24h average", f"{avg_forecast:.2f} kW"),
        ]) + '</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
