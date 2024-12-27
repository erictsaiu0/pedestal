# Pedestal art project
# Pedestal Art Project

An interactive art installation that uses computer vision and AI to analyze and respond to objects placed on a pedestal.

## Overview

This project combines motion detection, computer vision, and GPT-4 Vision to create an interactive art experience. When an object is placed on the pedestal, the system:

1. Detects the object using motion detection
2. Captures and processes the image
3. Analyzes the object using GPT-4 Vision to:
   - Determine if it's an art piece
   - Generate artistic interpretation
   - Provide non-artistic description
4. Converts the analysis to speech using OpenAI TTS
5. Plays the audio response

## Requirements

- Python 3.8+
- OpenCV
- OpenAI API key
- Webcam/camera
- Speaker system

## Key Components

- `run.py`: Main program with motion detection and control flow
- `gpt_utils.py`: GPT-4 Vision API integration
- `TTS_utils.py`: Text-to-speech conversion
- `pi.py`: Network communication between devices
- `device_ip.py`: Device IP configuration

## Setup

1. Create venv and install dependencies:
    ```bash
    pip -m venv .pedestal
    source .pedestal/bin/activate 
    pip install -r requirements.txt
    ```

2. Configure environment:
   - Copy `KEYS_example.py` to `KEYS.py`
   - Add your OpenAI API key to `KEYS.py`
   - Update device IPs in `device_ip.py` if using multiple devices

3. Hardware setup:
   - Position webcam/camera above pedestal
   - Connect speaker system
   - Ensure proper lighting conditions

## Usage

1. Start the main program:
   ```bash
   python run.py [--zoom ZOOM] [--text_num TEXT_NUM]
   ```
   - `--zoom`: Zoom level for camera (default: 0)
   - `--text_num`: Maximum text length for responses (default: 50)

2. Place objects on the pedestal and wait for audio response

## Configuration

- Adjust motion detection sensitivity in `run.py`
- Modify GPT prompts in `gpt_utils.py`
- Change TTS voices in `TTS_utils.py`
- Update network settings in `device_ip.py`
