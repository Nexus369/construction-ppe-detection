from flask import Flask, Response, jsonify
from flask_cors import CORS
import cv2
import threading
import json
import time
import os
from ppe_detection import load_model, process_frame
import numpy as np

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Global variables
camera = None
output_frame = None
lock = threading.Lock()
detection_active = False
detection_results = []
violation_count = 0
helmet_count = 0
vest_count = 0

def init_camera():
    """Initialize the camera"""
    global camera
    try:
        # Try different camera indices (0, 1, 2) in sequence
        for camera_idx in [0, 1, 2]:
            print(f"Attempting to open camera at index {camera_idx}")
            camera = cv2.VideoCapture(camera_idx)
            if camera.isOpened():
                # Successfully opened camera
                print(f"Successfully opened camera at index {camera_idx}")
                
                # Set optimal properties
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                camera.set(cv2.CAP_PROP_FPS, 30)
                return True
        
        print("Error: Could not open any camera")
        return False
    except Exception as e:
        print(f"Error initializing camera: {e}")
        return False

def detection_thread():
    """Background thread for PPE detection"""
    global camera, output_frame, lock, detection_active
    global detection_results, violation_count, helmet_count, vest_count
    
    # Load the model
    model = load_model()
    if model is None:
        print("Failed to load model")
        detection_active = False
        return
    
    # Reset counters
    violation_count = 0
    helmet_count = 0
    vest_count = 0
    detection_results = []
    
    frame_failure_count = 0
    max_failures = 10
    
    # Continue until detection is stopped
    while detection_active:
        try:
            if camera is None or not camera.isOpened():
                print("Camera disconnected, attempting to reconnect...")
                if not init_camera():
                    print("Failed to reconnect camera, stopping detection")
                    detection_active = False
                    break
            
            success, frame = camera.read()
            if not success or frame is None or frame.size == 0:
                frame_failure_count += 1
                print(f"Error reading frame (failure {frame_failure_count}/{max_failures})")
                
                if frame_failure_count >= max_failures:
                    print("Too many frame reading failures, attempting to reinitialize camera")
                    if camera is not None:
                        camera.release()
                    if not init_camera():
                        print("Failed to reinitialize camera, stopping detection")
                        detection_active = False
                        break
                    frame_failure_count = 0
                
                time.sleep(0.5)  # Wait a bit before retrying
                continue
            
            # Reset failure counter on successful frame read
            frame_failure_count = 0
            
            # Process frame with the model
            fps_start = cv2.getTickCount()
            processed_frame = process_frame(frame, model, fps_start)
            
            if processed_frame is not None:
                # Extract detection results from the model
                results = extract_detection_results(model, frame)
                
                # Update counters based on detection
                update_counters(results)
                
                # Lock the frame for thread safety
                with lock:
                    output_frame = processed_frame.copy()
                    detection_results.append(results)
                    # Keep only the last 50 results
                    if len(detection_results) > 50:
                        detection_results = detection_results[-50:]
            else:
                print("Failed to process frame, skipping")
            
        except Exception as e:
            print(f"Error in detection thread: {e}")
        
        # Sleep a bit to avoid excessive CPU usage
        time.sleep(0.03)

def extract_detection_results(model, frame):
    """Extract detection results from the model (mock implementation)"""
    # In a real implementation, this would extract actual results from the YOLOv8 model
    # For demo purposes, we're generating mock results
    results = model(frame, conf=0.25, iou=0.45, verbose=False)
    
    detections = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = result.names[cls]
            
            detections.append({
                "type": class_name,
                "detected": True,  # Since it was detected
                "confidence": conf
            })
    
    timestamp = time.strftime("%H:%M:%S")
    return {"timestamp": timestamp, "detections": detections}

def update_counters(results):
    """Update detection counters based on results"""
    global violation_count, helmet_count, vest_count
    
    for detection in results.get("detections", []):
        type_name = detection.get("type", "")
        if type_name.startswith("NO-") and detection.get("detected", False):
            violation_count += 1
        elif (type_name == "Hardhat" or type_name == "helmet") and detection.get("detected", False):
            helmet_count += 1
        elif (type_name == "Safety Vest" or type_name == "vest") and detection.get("detected", False):
            vest_count += 1

def generate_frames():
    """Generate frames for video streaming"""
    global output_frame, lock
    
    # Create a blank frame with text to use when no real frame is available
    blank_height, blank_width = 480, 640
    blank_frame = create_blank_frame(blank_width, blank_height, "Waiting for camera...")
    
    while True:
        try:
            # Get the frame with lock protection
            with lock:
                if output_frame is None:
                    current_frame = blank_frame.copy()
                else:
                    current_frame = output_frame.copy()
            
            # Encode the frame in JPEG format
            (flag, encoded_image) = cv2.imencode(".jpg", current_frame)
            if not flag:
                # If encoding fails, use the blank frame
                (flag, encoded_image) = cv2.imencode(".jpg", blank_frame)
                if not flag:
                    # If that fails too, just sleep and continue
                    time.sleep(0.1)
                    continue
            
            # Yield the frame in the format required for streaming
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                  bytearray(encoded_image) + b'\r\n')
                  
        except Exception as e:
            print(f"Error in generate_frames: {e}")
            time.sleep(0.1)  # Sleep briefly before continuing

def create_blank_frame(width, height, message="No signal"):
    """Create a blank frame with message text"""
    blank_frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Add text in the center
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(message, font, 1, 2)[0]
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2
    
    cv2.putText(blank_frame, message, (text_x, text_y), font, 1, (255, 255, 255), 2)
    
    return blank_frame

@app.route("/")
def index():
    """Home page route"""
    return "PPE Detection API Server"

@app.route("/api/start", methods=["POST"])
def start_detection():
    """Start PPE detection"""
    global detection_active, camera
    
    if detection_active:
        return jsonify({"success": False, "message": "Detection already running"})
    
    # Initialize camera if not already initialized
    if camera is None or not camera.isOpened():
        success = init_camera()
        if not success:
            return jsonify({"success": False, "message": "Failed to initialize camera"})
    
    # Start detection thread
    detection_active = True
    threading.Thread(target=detection_thread, daemon=True).start()
    
    return jsonify({"success": True, "message": "Detection started"})

@app.route("/api/stop", methods=["POST"])
def stop_detection():
    """Stop PPE detection"""
    global detection_active, camera
    
    if not detection_active:
        return jsonify({"success": False, "message": "Detection not running"})
    
    # Stop detection thread
    detection_active = False
    
    # Release camera
    if camera is not None and camera.isOpened():
        camera.release()
        camera = None
    
    return jsonify({"success": True, "message": "Detection stopped"})

@app.route("/api/status")
def get_status():
    """Get detection status and counters"""
    global detection_active, violation_count, helmet_count, vest_count
    
    return jsonify({
        "active": detection_active,
        "violations": violation_count,
        "helmets": helmet_count,
        "vests": vest_count
    })

@app.route("/api/results")
def get_results():
    """Get recent detection results"""
    global detection_results
    
    return jsonify({"results": detection_results})

@app.route("/video_feed")
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    print("Starting PPE Detection API Server...")
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True) 