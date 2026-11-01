# 🤖 AI Energy Recommendation Agent - Integration Guide

## Overview

Voltwise Solar Dashboard now includes an **AI-powered Energy Recommendation Agent** that uses OpenRouter.ai with persona prompting to provide expert battery management recommendations.

## What's New

### 1. **Energy Recommendation Agent Module** (`energy_recommendation_agent.py`)

A sophisticated AI agent that:
- **Analyzes weather forecasts** to predict solar production patterns
- **Provides expert recommendations** on battery charging/discharging strategies
- **Uses persona prompting** to position AI as an expert energy analyst
- **Considers multiple factors**: cloud cover, temperature, wind speed, humidity
- **Gives confidence levels** and detailed reasoning for each recommendation

#### Key Features:
- **Weather-based Analysis**: Examines 24-48 hour forecasts
- **Smart Decision Logic**: Evaluates battery capacity, current level, and consumption patterns
- **Production Estimation**: Predicts expected kWh generation
- **Risk Assessment**: Identifies potential issues (unexpected weather changes, consumption surges)
- **Optimal Timing**: Suggests when to charge/discharge

### 2. **Battery Storage Configuration**

Under the search bar, open "Battery storage (optional)" to:
- ✅ **Enable Battery Storage** - Toggle battery management features
- 📊 **Set Battery Capacity** - Define total kWh storage (1-100 kWh)
- 🔋 **Current Battery Level** - Adjust current charge percentage
- ⚡ **Daily Consumption** - Input expected kWh usage

Example Configuration:
```
- Battery Capacity: 10 kWh
- Current Level: 50% (5 kWh)
- Daily Consumption: 20 kWh
- Available Capacity: 5 kWh
```

### 3. **AI Recommendation Button**

After fetching weather data, click **"Get AI Recommendation"** to:
1. Send weather forecast + battery data to a free OpenRouter model (with automatic fallback)
2. Get detailed expert analysis
3. Receive actionable recommendation: **CHARGE**, **DISCHARGE**, or **MAINTAIN**

### 4. **Recommendation Output**

The AI provides:
- **Action**: Primary recommendation (CHARGE/DISCHARGE/MAINTAIN)
- **Confidence Level**: High/Medium/Low based on forecast certainty
- **Expected Production**: Estimated kWh generation next 24 hours
- **Reasoning**: Detailed explanation of weather factors
- **Risk Assessment**: Potential problems to watch for
- **Optimal Timing**: Specific hours for best results

## How to Use

### Step 1: Add OpenRouter API Key
Add your OpenRouter API key to your `.env` file:
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
```
Get your free API key from: [OpenRouter.ai](https://openrouter.ai/keys)

### Step 2: Configure Battery Storage
1. Open **"Battery storage (optional)"** under the search bar and tick **"I have battery storage"**
2. Set your battery specifications:
   - Total capacity in kWh
   - Current charge level (%)
   - Expected daily consumption
3. Review the battery status display

### Step 3: Fetch Weather Data
1. Enter your location (city, country code)
2. Click **"🔄 Fetch Weather & Predict"**
3. Wait for weather and production forecast

### Step 4: Get AI Recommendation
1. Click **"💡 Get AI Recommendation"** button
2. AI analyzes:
   - Current weather conditions
   - 24-48 hour forecast
   - Your battery configuration
   - Expected consumption patterns
3. Review detailed analysis and recommendation

### Step 5: Act on Recommendation
- 🟢 **CHARGE**: Start charging battery (abundant production expected)
- 🔴 **DISCHARGE**: Use battery power (low production expected)
- 🟡 **MAINTAIN**: Keep current state (balanced conditions)

## Persona Prompting Details

The agent uses this expert persona:

> "You are an expert energy production analyst with deep expertise in:
> - Solar PV energy forecasting and production analysis
> - Battery storage management and optimization
> - Weather-based energy production modeling
> - Real-time decision making for charging/discharging strategies
> - Maximizing energy independence and grid efficiency"

This makes the AI provide responses like a professional energy consultant would.

## Example Scenarios

### Scenario 1: Sunny Day - Charge
```
Current: 3.5 kW production, Clear skies, Low cloud cover
Forecast: Expected 45+ kWh generation next 24 hours
Battery: Currently at 40%

✓ Recommendation: CHARGE
Confidence: High
Reasoning: Clear skies with high irradiation will provide optimal charging window
Timing: Start immediately, peak charging 10:00-14:00
```

### Scenario 2: Stormy Day - Discharge
```
Current: 0.2 kW production, Heavy clouds, 90% cloud cover
Forecast: Expected 8 kWh generation next 24 hours
Battery: Currently at 75%

✓ Recommendation: DISCHARGE
Confidence: High
Reasoning: Storm system moving in, production will drop significantly
Timing: Begin discharge to preserve power for evening/night
Risk: If storm clears early, may need to switch to charging
```

### Scenario 3: Transitional Weather - Maintain
```
Current: 1.8 kW production, Partly cloudy, 45% cloud cover
Forecast: Expected 20 kWh generation next 24 hours
Battery: Currently at 50%

✓ Recommendation: MAINTAIN
Confidence: Medium
Reasoning: Variable cloud patterns, maintain flexibility
Timing: Monitor conditions hourly, be ready to switch strategies
```

## API Configuration

### Environment Variables (.env)
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
```

### API Providers
- **Weather Data**: [Open-Meteo](https://open-meteo.com) (free, no key)
- **AI Recommendations**: [OpenRouter.ai](https://openrouter.ai) (free models ending in `:free`)

## Features in Detail

### 1. Weather Analysis
- Temperature trends
- Cloud cover percentage
- Wind speed patterns
- Humidity levels
- Visibility conditions
- Rain/precipitation data

### 2. Production Forecasting
- Estimates hourly solar generation
- Accounts for weather factors
- Provides confidence intervals
- Identifies peak production windows

### 3. Battery Optimization
- Maximizes stored energy usage
- Prevents battery overflow
- Ensures reserve capacity
- Extends battery lifespan

### 4. Risk Management
- Detects sudden weather changes
- Alerts on consumption spikes
- Identifies reserve inadequacy
- Suggests contingency plans

## Advanced Features

### Quick Recommendation (Future)
The agent also includes a `get_quick_recommendation()` method for rapid decisions:
```python
quick_rec = agent.get_quick_recommendation(
    current_production=2.5,      # kW
    cloud_cover=20,              # 0-100%
    battery_level_percent=65     # 0-100%
)
```

### Forecast Summary Format
The agent formats forecast data for optimal AI analysis:
```
Hour | Temp(°C) | Cloud% | Wind(m/s) | Condition | Humidity%
-----|----------|--------|-----------|-----------|----------
10:00|   22.1   |  20    |   3.5     |  Clear    |   45
11:00|   24.0   |  15    |   4.0     |  Clear    |   40
```

## Troubleshooting

### Issue: "OpenRouter API Key Required"
**Solution**: 
1. Make sure `OPENROUTER_API_KEY` is in `.env`
2. Restart the Streamlit app
3. Get free API key from [OpenRouter.ai](https://openrouter.ai/keys)
4. Verify the key starts with `sk-or-v1-`

### Issue: "Error generating recommendation"
**Solution**:
1. Verify internet connection
2. Check API key is valid at [OpenRouter.ai Dashboard](https://openrouter.ai)
3. Ensure weather data was fetched successfully
4. Check .env file is properly formatted (no extra spaces)

### Issue: Recommendation takes too long
**Solution**:
1. This is normal (2-10 seconds) for first request using thinking models
2. Subsequent requests should be faster (5-8 seconds)
3. Check your internet connection speed
4. Verify OpenRouter API service status at [openrouter.ai](https://openrouter.ai)

## Next Steps

1. **Configure your battery**: Set realistic capacity and consumption values
2. **Enable recommendations**: Use the AI feature with real weather data
3. **Monitor results**: Track recommendation accuracy over time
4. **Refine settings**: Adjust battery parameters based on actual usage
5. **Integrate more services**: Add notifications or automation based on recommendations

## Performance Tips

- ✅ Recommendations work best with accurate weather data
- ✅ Update battery level daily for accurate projections
- ✅ Review recommendations during peak production hours
- ✅ Consider historical weather patterns for your location
- ✅ Monitor Gemini API usage for quota management

## Support Resources

- [OpenRouter.ai Documentation](https://openrouter.ai/docs)
- [OpenRouter API Guide](https://openrouter.ai/docs/guides)
- [Open-Meteo API](https://open-meteo.com/en/docs)
- [Streamlit Documentation](https://docs.streamlit.io/)

---

**Version**: 1.0  
**Last Updated**: December 20, 2025  
**Status**: ✅ Production Ready
