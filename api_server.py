from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import cv2
import json
import time
import os
import base64
import numpy as np
from datetime import datetime
from ppe_detection import load_model, process_frame

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from Vercel frontend

# Global variables
model = None
detection_active = False
detection_results = []
violation_count = 0
helmet_count = 0
vest_count = 0
glove_count = 0

def init_model():
    """Load the YOLOv8 model globally"""
    global model
    if model is None:
        print("Loading YOLOv8 model...")
        model = load_model()
        if model is None:
            print("Failed to load model!")

def update_counters(detections):
    """Update global counters based on detection results"""
    global violation_count, helmet_count, vest_count, glove_count
    
    current_violation_count = 0
    current_helmet_count = 0
    current_vest_count = 0
    current_glove_count = 0
    
    for detection in detections:
        type_name = detection.get("type", "")
        if type_name.startswith("NO-") and detection.get("detected", False):
            current_violation_count += 1
        elif (type_name == "Hardhat" or type_name == "helmet") and detection.get("detected", False):
            current_helmet_count += 1
        elif (type_name == "Safety Vest" or type_name == "vest") and detection.get("detected", False):
            current_vest_count += 1
        elif (type_name == "Gloves" or type_name == "hand gloves") and detection.get("detected", False):
            current_glove_count += 1
            
    # Update global counters
    violation_count = current_violation_count
    helmet_count = current_helmet_count
    vest_count = current_vest_count
    glove_count = current_glove_count

@app.route("/")
def index():
    """Home page route"""
    return "PPE Detection Cloud API Server is running!"

@app.route("/api/start", methods=["POST"])
def start_detection():
    """Start PPE detection"""
    global detection_active
    
    # Initialize the model on first start
    init_model()
    
    detection_active = True
    return jsonify({"success": True, "message": "Detection started"})

@app.route("/api/stop", methods=["POST"])
def stop_detection():
    """Stop PPE detection"""
    global detection_active
    detection_active = False
    return jsonify({"success": True, "message": "Detection stopped"})

@app.route("/api/status")
def get_status():
    """Get detection status and counters"""
    global detection_active, violation_count, helmet_count, vest_count, glove_count
    return jsonify({
        "active": detection_active,
        "violations": violation_count,
        "helmets": helmet_count,
        "vests": vest_count,
        "gloves": glove_count
    })

@app.route("/api/results")
def get_results():
    """Get recent detection results"""
    global detection_results
    return jsonify({"results": detection_results})

@app.route("/api/socket", methods=["POST", "OPTIONS"])
def process_socket_frame():
    """Process incoming base64 video frames from the frontend"""
    if request.method == "OPTIONS":
        return jsonify({"success": True})
        
    global model, detection_active, detection_results
    
    if not detection_active:
        return jsonify({"success": False, "message": "Detection is not active"})
        
    if model is None:
        init_model()
        if model is None:
            return jsonify({"success": False, "message": "Model failed to load"})

    try:
        data = request.json
        frame_data = data.get("frame", "")
        
        # Remove base64 prefix if present
        if "," in frame_data:
            frame_data = frame_data.split(",")[1]
            
        # Decode base64 to OpenCV image
        img_bytes = base64.b64decode(frame_data)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({"success": False, "message": "Failed to decode frame"})
            
        # Run YOLO inference
        _, detections = process_frame(frame, model, 0)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Update counters
        update_counters(detections)
        
        # Update results log
        result_entry = {
            "timestamp": timestamp,
            "detections": detections
        }
        detection_results.append(result_entry)
        
        # Keep only the last 50 results
        if len(detection_results) > 50:
            detection_results = detection_results[-50:]
            
        return jsonify({
            "success": True,
            "processed": True,
            "timestamp": timestamp,
            "message": "Frame processed successfully",
            "detections": detections
        })
        
    except Exception as e:
        print(f"Error processing frame: {e}")
        return jsonify({"success": False, "message": str(e)})

if __name__ == "__main__":
    print("Starting Cloud PPE Detection API Server...")
    # Render binds to the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True) 