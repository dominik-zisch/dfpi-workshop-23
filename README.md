# DfPI Workshop 2023

## Overview
This project is a Python application designed for object tracking with optional video input. It utilizes OpenCV for image processing and Paho MQTT for message handling. The application reads and updates configuration files, records tracking data, and provides a user interface for interaction.

## Installation

### Prerequisites
- Python 3.x
- Required Python packages: `numpy`, `opencv-python`, `scipy`, `paho-mqtt`, `imutils`, `pyyaml`

### Installation Steps
1. Clone the repository or download the source code.
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Features
- Video input handling for object tracking.
- Configuration file reading and updating.
- Real-time exclusion zone setting and editing.
- MQTT integration for remote control.
- Angle calculation and various interpolations.
- Interactive user interface for video control and parameter adjustment.
- CSV file recording for tracking data.

## Usage

### Basic Usage
1. Set up the `config.yaml` and `config_internal.yaml` files with the necessary configurations.
2. Run the script with the optional video input:
   ```bash
   python recorder.py [-v path/to/video/file]
   ```

### Key Bindings
- `q`: Quit the application.
- `Space`: Play/Pause video playback.
- `e`: Toggle Edit mode for setting exclusion zones.
- `Esc`: Exit Edit mode and save changes.
- `Left mouse click`: Add a point to the exclusion zone.
- `Right mouse click`: Move a point in the exclusion zone.
- `del` or `backspace`: Delete a point from the exclusion zone.
- `p`: Set Base Position for angle calculation.
- `r`: Start/Stop recording tracking data.


