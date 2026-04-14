# Personal Voice Assistant

A Python voice assistant with a Tkinter GUI that supports typed commands and continuous microphone input, then speaks responses aloud.

![Personal Voice Assistant screenshot](image.png)

## Overview

- Speech recognition for spoken commands
- Text-to-speech response output
- Rule-based command handling
- Ambient noise calibration for microphone input
- Desktop interface built with Tkinter

## Features

- Speech-to-Text with `SpeechRecognition`
- Text-to-Speech with `pyttsx3`
- Opens websites with `webbrowser`
- Answers basic questions like time, date, and Wikipedia summaries
- Gives current weather for a city or location
- Tkinter interface with text input and continuous voice listening

## Tech Stack

- Python
- SpeechRecognition
- pyttsx3
- PyAudio
- wikipedia
- webbrowser

## Workflow

1. Listen: capture microphone input continuously or accept typed commands.
2. Process: use simple `if` and `elif` rules to detect commands.
3. Speak: return the answer with text-to-speech.

## How to Run

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Open the GUI version:

   ```bash
   python gui_app.py
   ```

## Version Control Notes

- Keep `.venv` and `__pycache__` out of the repository. They are already ignored by `.gitignore`.
- Commit only the source files, `README.md`, `requirements.txt`, and `.gitignore`.

## Useful Commands

- `time` - tells the current time
- `date` - tells the current date
- `open youtube` - opens YouTube
- `open google` - opens Google
- `open github` - opens GitHub
- `open leetcode` - opens LeetCode
- `open linkedin` - opens LinkedIn
- `open hackerrank` - opens HackerRank
- `open codeforces` - opens Codeforces
- `open codechef` - opens CodeChef
- `search wikipedia python` - gives a short Wikipedia summary
- `weather in london` - gives current weather for London
- `show weather for delhi` - also gives current weather for Delhi
- `exit` or `quit` - closes the assistant

## Project Structure

- `assistant_core.py` - shared assistant logic
- `gui_app.py` - Tkinter desktop interface
- `requirements.txt` - Python dependencies
- `README.md` - project guide

## Notes

- This is a rule-based assistant, not a machine learning model.
- Audio input requires `PyAudio`.
- Weather uses the free Open-Meteo API, so internet access is required.
