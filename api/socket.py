from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
import base64
import numpy as np
import os

# This file handles WebSocket connections for live camera feed
# Note: This is a simplified implementation for Vercel

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        # Process the frame data
        if 'frame' in data:
            try:
                # Decode base64 image
                image_data = data['frame']
                # Remove the data URL prefix if present
                if 'base64,' in image_data:
                    image_data = image_data.split('base64,')[1]
                
                # In a real implementation, we would process the image with the model
                # For demo purposes, we'll return mock detection results
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # Generate mock detection results
                current_time = datetime.now().strftime("%H:%M:%S")
                detection_result = {
                    "timestamp": current_time,
                    "detections": [
                        {"type": "helmet", "detected": True, "confidence": 0.92},
                        {"type": "vest", "detected": True, "confidence": 0.88}
                    ],
                    "processed": True
                }
                
                self.wfile.write(json.dumps(detection_result).encode())
                return
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return
        
        # Default response
        self.send_response(400)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Invalid request"}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()