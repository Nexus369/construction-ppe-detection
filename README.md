# Construction Site PPE Detection System

A real-time safety monitoring system for construction sites that detects PPE (Personal Protective Equipment) such as hard hats and safety vests, and alerts when violations are detected.

## Features

- Beautiful, responsive web interface with a royal aesthetic designed for construction companies
- Real-time PPE detection using computer vision (YOLOv8)
- Audio alerts when safety violations are detected
- Dashboard showing current safety compliance status
- Works with webcams or other camera sources

## Project Structure

```
├── index.html                # Main landing page
├── visit-site.html           # Live monitoring page
├── js/
│   └── main.js               # Common JavaScript functions
├── ppe_detection.py          # Core PPE detection logic using OpenCV and YOLO
├── api_server.py             # Flask API server to connect web frontend with backend
└── best.pt                   # YOLOv8 model trained for PPE detection (not included in repo)
```

## Prerequisites

1. Python 3.8+ installed
2. A webcam or camera connected to your computer
3. The YOLOv8 model file (`best.pt`) placed in the project root directory

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/construction-ppe-detection.git
   cd construction-ppe-detection
   ```

2. Install the required Python packages:
   ```
   pip install ultralytics opencv-python flask flask-cors
   ```

3. Make sure you have the YOLOv8 model file (`best.pt`) placed in the project root directory.

## Running the Application

1. Start the API server:
   ```
   python api_server.py
   ```
   This will start the Flask server on http://localhost:5000

2. Open the website:
   - Simply open `index.html` in your web browser
   - Or serve it using a simple HTTP server:
     ```
     # If you have Python installed:
     python -m http.server
     ```
     Then navigate to http://localhost:8000

3. Click on "Visit Site" or "Launch Detection System" button to access the monitoring page.

4. In the monitoring page, click "Start Detection" to begin real-time PPE detection.

## Demo Mode

If the API server is not running or cannot be connected to, the web interface will automatically fall back to a demo mode that simulates PPE detection with sample images.

## Customization

- The detection thresholds can be adjusted in `ppe_detection.py`
- Web UI colors and styling can be modified in the HTML files using Tailwind CSS classes

## Troubleshooting

- If the camera doesn't work, make sure your browser has permission to access the camera
- If the model fails to load, check that the `best.pt` file is in the correct location
- For webcam issues, try changing the camera index in `api_server.py` (current options are 0 and 1)

## License

MIT License

## Credits

- YOLOv8 by Ultralytics
- TailwindCSS for styling
- Demo images from Freepik

#Developed By Jasbir Singh Monga 