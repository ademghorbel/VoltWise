"""
Energy Production Forecast Analysis & Battery Management Recommendation Agent
Uses Z AI API with persona prompting for expert recommendations
"""

import re
import requests
from typing import Dict, List
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)


FREE_MODELS = [
    "nvidia/nemotron-3.5-lightning:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "google/gemma-4-26b-a4b-it:free",
    "thinkingmachines/inkling:free",
]
RETRYABLE = {404, 408, 429, 500, 502, 503, 504}

class EnergyRecommendationAgent:
    """
    AI-powered agent that analyzes solar energy production forecasts
    and provides battery storage charging/discharging recommendations.
    Uses persona prompting to position the AI as an expert energy analyst.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the Energy Recommendation Agent with OpenRouter API
        
        Args:
            api_key: OpenRouter API key
        """
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        # Preferred model from .env first, then free models to fall back on when one is
        # busy (429), retired (404) or returns an empty answer.
        preferred = os.getenv("OPENROUTER_MODEL", "").strip()
        self.models = [m for m in [preferred] if m] + [m for m in FREE_MODELS if m != preferred]
        self.model = self.models[0]
        
        # System prompt that establishes the persona and expertise
        self.system_prompt = """You are an expert energy production analyst with deep expertise in:
- Solar PV energy forecasting and production analysis
- Battery storage management and optimization
- Weather-based energy production modeling
- Real-time decision making for charging/discharging strategies
- Maximizing energy independence and grid efficiency

Your role is to analyze weather forecasts and energy production data to provide 
specific, actionable recommendations for battery storage management. Always consider:
1. Upcoming weather conditions and their impact on solar production
2. Cloud cover percentage and its effect on irradiation
3. Temperature trends affecting panel efficiency
4. Wind speed patterns
5. Peak production times vs. peak consumption patterns

Provide clear, concise recommendations with confidence levels and expected benefits."""

    def analyze_forecast_and_recommend(
        self,
        current_production: float,
        forecast_data: List[Dict],
        battery_capacity: float,
        battery_current_level: float,
        daily_consumption_kwh: float,
        has_battery_storage: bool = True
    ) -> Dict:
        """
        Analyze weather forecast and provide battery management recommendations
        
        Args:
            current_production: Current solar production in kW
            forecast_data: List of hourly forecast data
            battery_capacity: Battery storage capacity in kWh
            battery_current_level: Current battery charge level in kWh
            daily_consumption_kwh: Expected daily consumption in kWh
            has_battery_storage: Whether user has battery storage
        
        Returns:
            Dict with recommendation, analysis, and expected production
        """
        
        if not has_battery_storage:
            return {
                "status": "no_battery",
                "message": "No battery storage configured. Enable battery storage to receive recommendations.",
                "recommendation": None
            }
        
        # Prepare forecast summary for the AI
        forecast_summary = self._prepare_forecast_summary(forecast_data)
        
        # Create the analysis prompt
        analysis_prompt = f"""
Analyze this solar battery charging scenario and provide a clear recommendation.

=== CURRENT SITUATION ===
Solar Production Right Now: {current_production:.2f} kW
Battery Status: {battery_current_level:.2f} kWh of {battery_capacity:.2f} kWh total
Battery Percentage: {(battery_current_level/battery_capacity)*100:.0f}%
Available Space in Battery: {battery_capacity - battery_current_level:.2f} kWh
Expected Daily Consumption: {daily_consumption_kwh:.2f} kWh

=== 24-HOUR WEATHER FORECAST ===
{forecast_summary}

=== YOUR DECISION LOGIC ===
You MUST choose ONE action based on these rules:

1. **CHARGE** if ANY of these are true:
   - Battery is below 40% AND forecast shows upcoming clouds/rain/storms
   - Battery is below 50% AND consumption is high (>{daily_consumption_kwh/2:.0f} kWh expected)
   - Next 6 hours have clear skies AND battery is not full
   - Battery nearly empty (<20%) regardless of forecast

2. **DISCHARGE** if ANY of these are true:
   - Battery is above 80% AND excellent forecast (clear, sunny)
   - Battery nearly full (>90%)
   - Next 24 hours show only clear weather AND low immediate production

3. **MAINTAIN** if:
   - Battery between 40-80%
   - Forecast is mixed/uncertain
   - Current conditions are balanced

=== REQUIRED RESPONSE FORMAT ===
Start with exactly these lines:
RECOMMENDATION: [CHARGE or DISCHARGE or MAINTAIN]
CONFIDENCE: [High or Medium or Low]

Then explain your reasoning with specific numbers from above.
Include: weather conditions, battery level, consumption risk."""

        try:
            # Call OpenRouter API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8502",
                "X-Title": "Voltwise"
            }
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": analysis_prompt},
            ]
            
            analysis_text, errors = "", []
            for model in self.models:
                payload = {"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 6000,
                           # thinking models: keep the thinking short and out of the answer
                           "reasoning": {"effort": "low", "exclude": True}}
                try:
                    response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
                except requests.exceptions.RequestException as e:
                    errors.append(f"{model}: {e.__class__.__name__}")
                    continue
                if response.status_code in RETRYABLE:
                    errors.append(f"{model}: HTTP {response.status_code}")
                    continue
                response.raise_for_status()
                message = response.json()['choices'][0]['message']
                # Only the real answer counts; a thinking-only reply moves on to the next model
                analysis_text = message.get('content') or ''
                if analysis_text.strip():
                    self.model = model
                    break
                errors.append(f"{model}: empty answer")
            
            if not analysis_text.strip():
                return {
                    "status": "error",
                    "message": "All AI models are busy right now, try again in a minute. (" + "; ".join(errors) + ")",
                    "recommendation": None
                }
            
            # Parse the response to extract structured recommendation
            recommendation = self._parse_recommendation(analysis_text)
            
            return {
                "status": "success",
                "recommendation": recommendation,
                "full_analysis": analysis_text,
                "timestamp": datetime.now().isoformat(),
                "battery_info": {
                    "current_level_kwh": battery_current_level,
                    "capacity_kwh": battery_capacity,
                    "charge_percentage": (battery_current_level / battery_capacity) * 100
                }
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"API Error: {str(e)}",
                "recommendation": None
            }
        except (KeyError, ValueError) as e:
            return {
                "status": "error",
                "message": f"Response parsing error: {str(e)}",
                "recommendation": None
            }

    def _prepare_forecast_summary(self, forecast_data: List[Dict]) -> str:
        """Format forecast data into a readable summary for the AI"""
        
        summary_lines = []
        summary_lines.append("Hour | Temp(°C) | Cloud% | Wind(m/s) | Condition | Humidity%")
        summary_lines.append("-" * 70)
        
        for item in forecast_data[:24]:  # Next 24 hours
            timestamp = item.get('timestamp', '')
            if isinstance(timestamp, str):
                hour = timestamp.split('T')[1][:5] if 'T' in timestamp else "N/A"
            else:
                hour = timestamp.strftime("%H:%M") if timestamp else "N/A"
            
            temp = f"{item.get('temperature', 0):.1f}"
            clouds = f"{item.get('clouds', 0)}"
            wind = f"{item.get('wind_speed', 0):.1f}"
            condition = item.get('condition', 'Unknown')
            humidity = f"{item.get('humidity', 0)}"
            
            line = f"{hour} | {temp:>6} | {clouds:>5} | {wind:>8} | {condition:<10} | {humidity:>6}"
            summary_lines.append(line)
        
        return "\n".join(summary_lines)

    def _parse_recommendation(self, analysis_text: str) -> Dict:
        """
        Parse the AI analysis to extract key recommendation data
        
        Args:
            analysis_text: Full analysis text from OpenRouter
        
        Returns:
            Structured recommendation dictionary
        """
        
        recommendation = {
            "action": "MAINTAIN",
            "confidence": "Medium",
            "expected_production_kwh": None,
            "reasoning": "",
            "risk_assessment": "",
            "optimal_timing": ""
        }
        
        text = analysis_text
        text_upper = text.upper()
        
        # Parse ACTION from the "RECOMMENDATION:" line. Whole words only, since
        # "DISCHARGE" contains "CHARGE".
        lines = text.split('\n')
        action_re = re.compile(r'\b(DISCHARGE|CHARGE|MAINTAIN)\b')
        found = None
        for line in lines:
            if "RECOMMENDATION" in line.upper():
                m = action_re.search(line.upper())
                if m:
                    found = m.group(1)
                    break
        
        # No "RECOMMENDATION:" line: use the first action word in the text
        if found is None:
            m = action_re.search(text_upper)
            found = m.group(1) if m else "MAINTAIN"
        recommendation["action"] = found
        
        # Parse CONFIDENCE - look for "CONFIDENCE:" format
        for line in lines:
            if "CONFIDENCE:" in line.upper():
                if "HIGH" in line.upper():
                    recommendation["confidence"] = "High"
                elif "LOW" in line.upper():
                    recommendation["confidence"] = "Low"
                else:
                    recommendation["confidence"] = "Medium"
                break
        
        # Extract reasoning from the text (everything after the first two lines)
        if len(lines) > 2:
            reasoning = '\n'.join(lines[2:]).strip()
            if reasoning:
                recommendation["reasoning"] = reasoning[:500]
        
        # ALWAYS store full analysis - this is the raw AI response
        recommendation["full_analysis"] = analysis_text
        
        print(f"DEBUG Stored full_analysis: {analysis_text[:100] if analysis_text else 'EMPTY'}")
        
        return recommendation

    def get_quick_recommendation(self, current_production: float, cloud_cover: int, 
                                battery_level_percent: float) -> str:
        """
        Get a quick recommendation based on current conditions
        
        Args:
            current_production: Current production in kW
            cloud_cover: Cloud cover 0-100%
            battery_level_percent: Battery level 0-100%
        
        Returns:
            Quick recommendation string
        """
        
        if cloud_cover > 70:
            return "DISCHARGE - High cloud cover expected, preserve battery for peak hours"
        elif cloud_cover < 30 and battery_level_percent < 80:
            return "CHARGE - Clear skies and low battery level, optimal charging conditions"
        elif battery_level_percent > 95:
            return "DISCHARGE - Battery nearly full, reduce charging to prevent overflow"
        elif battery_level_percent < 20:
            return "MAINTAIN - Low battery level, preserve for essential consumption"
        else:
            return "MAINTAIN - Balanced conditions, keep current charging state"


# Example usage function
def example_usage():
    """Example of how to use the Energy Recommendation Agent"""
    
    api_key = "YOUR_GEMINI_API_KEY"
    agent = EnergyRecommendationAgent(api_key)
    
    # Sample forecast data
    forecast = [
        {
            'timestamp': '2025-12-20T10:00:00',
            'temperature': 22,
            'clouds': 20,
            'wind_speed': 3.5,
            'condition': 'Clear',
            'description': 'Clear sky',
            'humidity': 45
        },
        {
            'timestamp': '2025-12-20T11:00:00',
            'temperature': 24,
            'clouds': 15,
            'wind_speed': 4.0,
            'condition': 'Clear',
            'description': 'Clear sky',
            'humidity': 40
        },
        # ... more forecast data
    ]
    
    recommendation = agent.analyze_forecast_and_recommend(
        current_production=2.5,
        forecast_data=forecast,
        battery_capacity=10.0,
        battery_current_level=6.5,
        daily_consumption_kwh=15.0,
        has_battery_storage=True
    )
    
    print(json.dumps(recommendation, indent=2, default=str))


if __name__ == "__main__":
    example_usage()
