# ⚡ Voltwise - Solar PV Production Dashboard

A real-time solar power production forecasting application with interactive weather analysis and machine learning predictions.

## 📋 Project Overview

This project provides:
- **Real-time weather data** integration from OpenWeatherMap API
- **ML-powered solar production forecasts** using fine-tuned XGBoost model with exogenous features
- **Interactive Streamlit dashboard** with live charts and analytics
- **24-hour production forecasts** with weather correlation analysis

**Status**: ✅ Fully operational with trained XGBoost model + AI-powered battery recommendations

---

## ✨ NEW: AI Energy Recommendation Agent

The dashboard now includes an **intelligent AI-powered battery management system** powered by OpenRouter API:

### 🤖 Key Features
- **Expert AI Analysis**: Uses advanced LLM (OLMo-3.1-32B) with persona prompting as energy analyst
- **Weather-Based Recommendations**: Analyzes 24-hour forecasts to suggest CHARGE/DISCHARGE/MAINTAIN
- **Battery Optimization**: Considers capacity, current level, consumption patterns, and weather conditions
- **Confidence Levels**: Provides High/Medium/Low confidence based on forecast certainty
- **Detailed Reasoning**: Full explanation of decision logic with specific numbers and considerations

### 📚 Usage
1. Enable **"🔋 Battery Storage"** in sidebar
2. Configure battery capacity, level, and daily consumption
3. Fetch weather data for your location
4. Click **"💡 Get AI Recommendation"** button
5. Review AI's expert analysis and recommendation

See **AI_RECOMMENDATION_GUIDE.md** for complete documentation.

---

## 📦 Project Structure

```
.
├── app.py                          # Main Streamlit dashboard application
├── config.py                       # Configuration and constants
├── weather_api.py                  # OpenWeatherMap API integration
├── model_utils.py                  # XGBoost model loading and prediction
├── energy_recommendation_agent.py  # AI-powered battery recommendation agent
├── best_model_exogenous.pkl        # Fine-tuned XGBoost model (trained)
├── BDDsfax.xlsx                    # Training dataset (Sfax, Tunisia)
├── notebooks/
│   └── model_training.ipynb        # ML model development notebook
├── assets/
│   └── logo.png                    # Dashboard logo
├── AI_RECOMMENDATION_GUIDE.md       # AI agent integration documentation
├── .env                            # Environment variables (API keys, gitignored)
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

---

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Python 3.8+
- Virtual environment: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/Mac)
- Two API keys (both FREE tier available)

### ⚙️ Step 1: Get Your OpenWeatherMap API Key

1. **Visit** [OpenWeatherMap API](https://openweathermap.org/api)
2. **Click** "Sign Up" → Create free account
3. **Verify** email address
4. **Go to** [API Keys tab](https://home.openweathermap.org/api_keys)
5. **Copy** your default API key (starts with alphanumeric)
6. **Save it** - you'll need it for `.env`

**Free Tier Includes**:
- 1,000 calls/day
- 24-hour forecasts
- Current weather data
- Historical data

### ⚙️ Step 2: Get Your OpenRouter API Key (For AI Recommendations)

1. **Visit** [OpenRouter.ai](https://openrouter.ai)
2. **Click** "Sign Up" → Create free account (via GitHub/Google recommended)
3. **Go to** [API Keys](https://openrouter.ai/keys)
4. **Create** new API key (click button)
5. **Copy** the full key (starts with `sk-or-v1-`)
6. **Save it** - you'll need it for `.env`

**Free Tier Includes**:
- Access to free models like OLMo-3.1-32B
- First $5 monthly credits
- Perfect for testing and demos

**Alternative Models** (if primary doesn't work):
- `nvidia/nemotron-3-nano-30b-a3b:free` - Fast, lightweight
- `meta-llama/llama-2-70b-chat:free` - Reliable alternative

### 📝 Step 3: Configure Environment Variables

Create `.env` file in project root with your actual keys:

```env
# OpenWeatherMap API Key (Get from: https://openweathermap.org/api)
WEATHER_API_KEY=your_actual_openweathermap_key_here

# OpenRouter API Key (Get from: https://openrouter.ai/keys)
OPENROUTER_API_KEY=your_actual_openrouter_key_here

# AI Model (use free tier models from OpenRouter)
OPENROUTER_MODEL=allenai/olmo-3.1-32b-think:free
```

**⚠️ Security**: Never commit `.env` to git - it contains sensitive credentials!

### 📦 Step 4: Create Virtual Environment & Install

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 🚀 Step 5: Launch Dashboard

```bash
streamlit run app.py
```

Dashboard opens at: `http://localhost:8501`

**Troubleshooting**:
- If port 8501 is busy: `streamlit run app.py --server.port 8502`
- If API errors: Check `.env` file has correct keys with no extra spaces
- See **Troubleshooting** section below for more help

---

## 💡 How to Use

### Basic Workflow
1. **Enter Location**: City name + country code (e.g., "Sfax", "TN")
2. **(Optional) Enable Battery Storage**: Configure battery settings in sidebar
3. **Click "Fetch Weather & Predict"**
4. **View Results**:
   - Current conditions (temp, humidity, wind, clouds)
   - 24-hour production forecast chart
   - Detailed forecast table with predictions
   - Statistical analysis (avg, peak, total energy)
   - **(NEW) AI Recommendation**: Get intelligent battery management advice

### Dashboard Sections

#### 🔋 Battery Storage Configuration (NEW)
- Enable/disable battery management features
- Set battery capacity (kWh)
- Adjust current charge level (%)
- Input daily consumption estimate
- View available storage capacity

#### 🤖 AI Energy Recommendation Agent (NEW)
- Click **"💡 Get AI Recommendation"** to analyze weather and battery status
- Receives recommendation: **🟢 CHARGE**, **🔴 DISCHARGE**, or **🟡 MAINTAIN**
- Reviews detailed expert analysis explaining the decision
- Confidence level (High/Medium/Low) based on forecast certainty
- Considers battery capacity, consumption patterns, and weather trends

#### 🌤️ Current Conditions
- Temperature, humidity, wind speed, cloud coverage
- Current solar irradiance
- Current power production estimate

#### 📈 24-Hour Production Forecast
- Predicted solar power output (kW) with trend visualization
- High/medium/low production threshold indicators
- Hourly granularity for detailed planning

#### 🌡️ Weather Forecast
- Temperature trends (24 hours)
- Cloud coverage patterns
- Wind and humidity forecasts

#### 📊 Statistics & Analysis
- Average power (24h)
- Peak power prediction + time
- Total estimated energy (kWh)
- Average temperature with min/max
- Total estimated energy (kWh)
- Average temperature with min/max

---

## 🤖 Machine Learning Model

### Model Details
- **Type**: XGBoost Regressor (fine-tuned)
- **Training Data**: Historical solar production data from Sfax, Tunisia
- **Dataset**: BDDsfax.xlsx (hourly measurements)
- **Model File**: `best_model_exogenous.pkl`

### Features Used (Exogenous)
- `hour` - Hour of day (0-23)
- `Température ambiante(℃)` - Ambient temperature
- `Humidité ambiante(%RH)` - Relative humidity
- `Vitesse vent(m/s)` - Wind speed
- `Irradiation transitoire pente(W/㎡)` - Solar irradiance
- `day_Monday` to `day_Sunday` - Day of week (one-hot encoded)

### Performance
- Uses real trained model from `best_model_exogenous.pkl`
- Exogenous features incorporate weather variables
- Non-negative predictions (physical constraint enforced)

---

## 📚 Development & Training

### Jupyter Notebook
The ML model development is documented in `notebooks/model_training.ipynb`:
- Data exploration and preprocessing
- Feature engineering
- Model training and evaluation
- Hyperparameter tuning

### Training Data
- **Source**: `BDDsfax.xlsx`
- **Location**: Sfax, Tunisia
- **Variables**: Temperature, humidity, wind, irradiance, power output

To retrain the model:
1. Open `notebooks/model_training.ipynb` in Jupyter
2. Update training parameters if needed
3. Run all cells to train XGBoost
4. Export model as `best_model_exogenous.pkl`

---

## 🔧 Configuration

### .env Variables
```env
WEATHER_API_KEY=your_openweathermap_key    # Required: OpenWeatherMap API key
OPENROUTER_API_KEY=your_openrouter_key     # Required: OpenRouter API key (for AI recommendations)
OPENROUTER_MODEL=allenai/olmo-3.1-32b-think:free  # LLM model for AI agent
```

### Model Configuration (config.py)
- `WEATHER_API_BASE_URL` - OpenWeatherMap current weather endpoint
- `WEATHER_FORECAST_URL` - OpenWeatherMap forecast endpoint
- `MODEL_PATH` - Path to trained model file
- `FEATURE_COLUMNS_EXOGENOUS` - Features expected by model
- `OPENROUTER_API_KEY` - API key for AI recommendations
- `OPENROUTER_MODEL` - LLM model identifier

### Thresholds
- `IRRADIATION_THRESHOLD_HIGH` = 500 W/m²
- `IRRADIATION_THRESHOLD_MEDIUM` = 200 W/m²
- `TEMPERATURE_RANGE` = (5, 45)°C

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | Streamlit 1.28.1 |
| **ML Model** | XGBoost 2.0.3 |
| **AI Engine** | OpenRouter.ai + OLMo-3.1-32B LLM |
| **Data Processing** | Pandas, NumPy, Scikit-learn |
| **Visualization** | Plotly 5.18.0 |
| **Weather API** | OpenWeatherMap REST API |
| **Python Version** | 3.8+ |

---

## 📋 Dependencies

See `requirements.txt` for full list:
- streamlit - Dashboard framework
- xgboost - ML model
- pandas - Data manipulation
- numpy - Numerical computing
- plotly - Interactive charts
- requests - HTTP requests (for API calls)
- python-dotenv - Environment management

Install all: `pip install -r requirements.txt`

---

## 🚨 Troubleshooting

### "Weather API Error: 404"
**Solution**: Check city spelling (e.g., use "Hammamet" not "hammemet")
- Try major cities first (Sfax, Tunis, Sousse)
- Use 2-letter country code (TN for Tunisia, FR for France)

### "Model not loaded"
**Solution**: Ensure `best_model_exogenous.pkl` exists in project root
- Check file exists: `ls *.pkl`
- Retrain if missing using `notebooks/model_training.ipynb`

### "WEATHER_API_KEY not set"
**Solution**: 
1. Get free key from [OpenWeatherMap](https://openweathermap.org/api)
2. Create `.env` file with: `WEATHER_API_KEY=your_key_here`
3. Restart app: `streamlit run app.py`

### "AI Recommendation not working"
**Solution**:
1. Get free OpenRouter API key from [OpenRouter.ai](https://openrouter.ai)
2. Add to `.env`: `OPENROUTER_API_KEY=your_key_here`
3. Ensure battery storage is enabled in sidebar
4. Restart app: `streamlit run app.py`
5. See **AI_RECOMMENDATION_GUIDE.md** for detailed setup

---

## 📝 License

Project for solar forecasting and energy management.

## 👥 Authors & History

Originally built as a personal project during a summer 2025 internship. The
codebase has since been reworked (repo hygiene, file organization, dead
config cleanup, UI fixes) and republished here under my own account, since
the original commit history wasn't attributed to it.

Built by Mohamed Adam Ghorbel.

---

**Last Updated**: December 2025  
**Model Status**: ✅ Fine-tuned XGBoost with exogenous features loaded  
**Dashboard Status**: ✅ Fully operational with AI recommendations  
**AI Features**: ✅ OpenRouter.ai powered energy recommendations (Dec 20, 2025)


---



## 📊 Model Performance & Example Predictions

### XGBoost Model Performance (Latest Results)

#### Training Phase Results (4622 samples)
| Metric | Baseline | Exogenous | Improvement |
|--------|----------|-----------|-------------|
| MAE (kW) | 0.2534 | 0.0205 | ↓ 91.9% |
| RMSE (kW) | 0.4997 | 0.0369 | ↓ 92.6% |
| R² Score | 0.8774 | 0.9993 | ↑ 12.2 pts |

#### Test Phase Results (Real-world generalization, 1150 samples: Dec 24 2024 - Jan 15 2025)
| Metric | Baseline | Exogenous | Fine-tuned |
|--------|----------|-----------|-----------|
| MAE (kW) | 0.3944 | 0.2734 | **0.2567** |
| RMSE (kW) | 0.6927 | 0.5581 | **0.5332** |
| R² Score | 0.6087 | 0.7460 | **0.7742** |

**Key Insight**: The exogenous model reduces prediction error by **30.7%** in production vs baseline. Fine-tuning adds an additional **6.1%** improvement.

#### Model Configuration
- **Framework**: XGBoost Regressor
- **Optimized Hyperparameters**:
  - `learning_rate=0.05`
  - `max_depth=5`
  - `n_estimators=100`
- **Cross-validation MAE**: 0.2262 kW
- **Input Features**: Hour, day of week, temperature, humidity, wind speed, solar irradiance

### Example Prediction

Given weather input:
```
Temperature: 28°C
Humidity: 45%
Wind Speed: 3.2 m/s
Cloud Coverage: 20% (Irradiance: ~800 W/m²)
Hour: 14:00
```

Expected output:
```
Predicted Power: 4.8 kW
Model Confidence: High (sunny conditions)
Expected Accuracy: ±0.26 kW (based on test MAE)
```

---

## 🔐 Security Notes

1. **Never commit `.env` file** to git (it's ignored)
2. **Keep API keys private** - regenerate if exposed
3. **Use environment variables** in production
4. **Monitor API usage** to avoid unexpected charges

---

## 📚 Documentation Files

- **README.md** (this file) - Complete usage guide
- **notebooks/model_training.ipynb** - ML model training and validation
- **config.py** - All configuration constants
- **Code comments** - Inline documentation

---

## 🚦 Status Indicators

| Component | Status | Notes |
|-----------|--------|-------|
| Core Application | ✅ Working | Tested and validated |
| Weather API | ✅ Working | Requires valid API key |
| ML Model | ✅ Working | Pre-trained XGBoost |
| AI Recommendations | ✅ NEW | OpenRouter.ai powered |
| Battery Management | ✅ NEW | AI-optimized charging strategy |

---

**Python Version**: 3.8+  
**Framework**: Streamlit 1.28.1  
**Latest Update**: December 20, 2025 - Added AI Energy Recommendation Agent
