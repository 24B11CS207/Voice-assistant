"""Core logic for the personal voice assistant.

The assistant follows a simple rule-based workflow:
listen -> process -> speak.
"""

from __future__ import annotations

import datetime as dt
import json
import threading
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - handled at runtime
    sr = None

try:
    import pyttsx3
except ImportError:  # pragma: no cover - handled at runtime
    pyttsx3 = None

try:
    import wikipedia
except ImportError:  # pragma: no cover - handled at runtime
    wikipedia = None


@dataclass(frozen=True)
class AssistantResponse:
    """Structured response returned by the assistant."""

    text: str
    should_exit: bool = False


class VoiceAssistant:
    """Simple voice assistant for microphone-driven interaction."""

    def __init__(self, threshold: int = 300) -> None:
        self.threshold = threshold
        self.engine = pyttsx3.init() if pyttsx3 else None
        self.recognizer = sr.Recognizer() if sr else None
        self._speech_lock = threading.Lock()

        if self.recognizer is not None:
            self.recognizer.energy_threshold = threshold
            self.recognizer.dynamic_energy_threshold = True

    def speak(self, message: str) -> None:
        """Speak the response and mirror it in the terminal."""

        print(f"Assistant: {message}")
        if self.engine is None or not message:
            return

        with self._speech_lock:
            self.engine.stop()
            self.engine.say(message)
            self.engine.runAndWait()

    def calibrate_microphone(self, duration: float = 0.3) -> None:
        """Calibrate the microphone once before continuous listening starts."""

        if self.recognizer is None:
            raise RuntimeError("SpeechRecognition is not installed.")

        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
        except (OSError, AttributeError) as exc:
            raise RuntimeError(
                "Microphone input is unavailable. Install PyAudio or use the text box instead."
            ) from exc

    def listen(self) -> str:
        """Listen to the microphone and return recognized speech."""

        if self.recognizer is None:
            raise RuntimeError("SpeechRecognition is not installed.")

        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = self.recognizer.listen(source)
        except (OSError, AttributeError) as exc:
            raise RuntimeError(
                "Microphone input is unavailable. Install PyAudio or use the text box instead."
            ) from exc

        try:
            return self.recognizer.recognize_google(audio).strip().lower()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""

    def get_weather(self, location: str) -> str:
        """Fetch current weather for a location using Open-Meteo."""

        if not location:
            return "Please tell me a city name for the weather check."

        geocode_url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode(
            {
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json",
            }
        )

        try:
            with urllib.request.urlopen(geocode_url, timeout=10) as response:
                geocode_data = json.loads(response.read().decode("utf-8"))
        except Exception:
            return "I could not reach the weather service right now."

        results = geocode_data.get("results") or []
        if not results:
            return f"I could not find weather information for {location}."

        place = results[0]
        latitude = place.get("latitude")
        longitude = place.get("longitude")
        place_name = place.get("name", location)
        country = place.get("country")
        admin1 = place.get("admin1")

        forecast_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current_weather": "true",
                "timezone": "auto",
            }
        )

        try:
            with urllib.request.urlopen(forecast_url, timeout=10) as response:
                weather_data = json.loads(response.read().decode("utf-8"))
        except Exception:
            return "I could not reach the weather service right now."

        current_weather = weather_data.get("current_weather") or {}
        temperature = current_weather.get("temperature")
        windspeed = current_weather.get("windspeed")
        weathercode = current_weather.get("weathercode")
        description = self._weather_description(weathercode)

        location_parts = [part for part in [place_name, admin1, country] if part]
        formatted_location = ", ".join(location_parts)

        return (
            f"Current weather for {formatted_location}: {description}, "
            f"{temperature} degrees Celsius, wind speed {windspeed} kilometers per hour."
        )

    def _weather_description(self, code: object) -> str:
        """Convert an Open-Meteo weather code into a human readable description."""

        weather_codes = {
            0: "clear sky",
            1: "mainly clear",
            2: "partly cloudy",
            3: "overcast",
            45: "foggy",
            48: "rime fog",
            51: "light drizzle",
            53: "moderate drizzle",
            55: "dense drizzle",
            56: "light freezing drizzle",
            57: "dense freezing drizzle",
            61: "slight rain",
            63: "moderate rain",
            65: "heavy rain",
            66: "light freezing rain",
            67: "heavy freezing rain",
            71: "slight snow fall",
            73: "moderate snow fall",
            75: "heavy snow fall",
            77: "snow grains",
            80: "slight rain showers",
            81: "moderate rain showers",
            82: "violent rain showers",
            85: "slight snow showers",
            86: "heavy snow showers",
            95: "thunderstorm",
            96: "thunderstorm with slight hail",
            99: "thunderstorm with heavy hail",
        }

        try:
            return weather_codes.get(int(code), "current conditions")
        except (TypeError, ValueError):
            return "current conditions"

    def _open_website(self, target: str) -> AssistantResponse:
        """Open a known website or a direct URL."""

        websites = {
            "google": ("https://www.google.com", "Opening Google."),
            "youtube": ("https://www.youtube.com", "Opening YouTube."),
            "github": ("https://github.com", "Opening GitHub."),
            "leetcode": ("https://leetcode.com", "Opening LeetCode."),
            "linkedin": ("https://www.linkedin.com", "Opening LinkedIn."),
            "hackerrank": ("https://www.hackerrank.com", "Opening HackerRank."),
            "codeforces": ("https://codeforces.com", "Opening Codeforces."),
            "codechef": ("https://www.codechef.com", "Opening CodeChef."),
        }

        normalized_target = target.strip().lower()
        if normalized_target in websites:
            url, message = websites[normalized_target]
            webbrowser.open(url)
            return AssistantResponse(message)

        if normalized_target.startswith("http://") or normalized_target.startswith("https://"):
            webbrowser.open(normalized_target)
            return AssistantResponse(f"Opening {normalized_target}.")

        return AssistantResponse(
            "I can open Google, YouTube, GitHub, LeetCode, LinkedIn, HackerRank, Codeforces, CodeChef, or a full website link."
        )

    def _greeting_response(self, command: str) -> AssistantResponse:
        """Return a friendly greeting based on the current time and command."""

        hour = dt.datetime.now().hour
        if hour < 12:
            time_of_day = "morning"
        elif hour < 18:
            time_of_day = "afternoon"
        else:
            time_of_day = "evening"

        greetings = {
            "hello": f"Hello. Good {time_of_day}.",
            "hi": f"Hi there. Good {time_of_day}.",
            "hey": f"Hey. Good {time_of_day}.",
            "good morning": "Good morning. How can I help you?",
            "good afternoon": "Good afternoon. How can I help you?",
            "good evening": "Good evening. How can I help you?",
            "good night": "Good night. Sleep well, sweet dreams.",
            "how are you": "I am doing well. How can I help you?",
            "what's up": "I am ready to help you.",
            "whats up": "I am ready to help you.",
            "thank you": "You are welcome.",
            "thanks": "You are welcome.",
        }

        normalized = command.strip().lower()
        for phrase, response in greetings.items():
            if phrase in normalized:
                return AssistantResponse(response)

        return AssistantResponse("Hello. How can I help you?")

    def _extract_weather_location(self, command: str) -> str:
        """Extract a location from a weather-style query."""

        normalized = command.strip().lower().replace("wheather", "weather")
        patterns = [
            "weather in",
            "weather for",
            "weather at",
            "weather of",
            "weather details in",
            "weather details for",
            "weather details at",
            "tell me weather details in",
            "tell me weather details for",
            "tell me weather details at",
            "show me weather details in",
            "show me weather details for",
            "show me weather details at",
            "show weather in",
            "show weather for",
            "show weather at",
            "tell me weather in",
            "tell me weather for",
            "tell me weather at",
            "what is the weather in",
            "what is the weather for",
            "what is the weather at",
            "what's the weather in",
            "what's the weather for",
            "what's the weather at",
            "weather",
        ]

        for pattern in patterns:
            if normalized.startswith(pattern):
                location = normalized.removeprefix(pattern).strip()
                return location

        return ""

    def process_command(self, command: str) -> AssistantResponse:
        """Process a command using simple if/elif rules."""

        normalized = command.strip().lower().replace("wheather", "weather")

        if not normalized:
            return AssistantResponse("I did not catch that. Please try again.")

        if any(word in normalized for word in ["exit", "quit", "stop"]):
            return AssistantResponse("Goodbye.", should_exit=True)

        if "time" in normalized:
            current_time = dt.datetime.now().strftime("%I:%M %p")
            return AssistantResponse(f"The current time is {current_time}.")

        if "date" in normalized or "day" in normalized:
            current_date = dt.datetime.now().strftime("%A, %d %B %Y")
            return AssistantResponse(f"Today is {current_date}.")

        if normalized.startswith("open "):
            target = normalized.removeprefix("open ").strip()

            if target.startswith("website "):
                target = target.removeprefix("website ").strip()

            return self._open_website(target)

        if "weather" in normalized:
            location = self._extract_weather_location(normalized)

            if not location:
                return AssistantResponse(
                    "Please tell me a city or place name, like weather in London or weather for Mumbai."
                )

            return AssistantResponse(self.get_weather(location))

        if any(
            phrase in normalized
            for phrase in [
                "hello",
                "hi",
                "hey",
                "good morning",
                "good afternoon",
                "good evening",
                "how are you",
                "what's up",
                "whats up",
                "thanks",
                "thank you",
            ]
        ):
            return self._greeting_response(normalized)

        if normalized.startswith("search wikipedia") or normalized.startswith("wikipedia"):
            if wikipedia is None:
                return AssistantResponse("Wikipedia is not installed.")

            query = normalized.replace("search wikipedia", "").replace("wikipedia", "").strip()
            if not query:
                return AssistantResponse("Please tell me what to search on Wikipedia.")

            try:
                summary = wikipedia.summary(query, sentences=2, auto_suggest=True)
                return AssistantResponse(summary)
            except Exception:
                return AssistantResponse(f"I could not find information about {query}.")

        if "who are you" in normalized or "your name" in normalized:
            return AssistantResponse("I am a simple personal voice assistant built with Python.")

        return AssistantResponse("I can help with time, date, weather, greetings, websites, and Wikipedia search.")

    def run(self) -> None:
        """Start the assistant loop."""

        self.speak("Voice assistant started.")

        while True:
            command = self.listen()
            response = self.process_command(command)
            self.speak(response.text)

            if response.should_exit:
                break