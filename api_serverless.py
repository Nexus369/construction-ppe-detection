from flask import Flask, Response, jsonify, request
from http.server import BaseHTTPRequestHandler
import json
import os
import base64
import numpy as np
import time
from datetime import datetime

# Mock data for demonstration purposes
mock_detection_results = [
    {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "detections": [
            {"type": "helmet", "detected": True, "confidence": 0.92},
            {"type": "vest", "detected": True, "confidence": 0.88}
        ]
    }
]

# Serverless handler for Vercel
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/status'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "status": "online",
                "detection_active": True,
                "helmet_count": 5,
                "vest_count": 4,
                "violation_count": 1
            }
            
            self.wfile.write(json.dumps(response).encode())
            return
        
        elif self.path.startswith('/api/results'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Generate some mock detection results
            current_time = datetime.now().strftime("%H:%M:%S")
            new_result = {
                "timestamp": current_time,
                "detections": [
                    {"type": "helmet", "detected": True, "confidence": 0.92},
                    {"type": "vest", "detected": True, "confidence": 0.88}
                ]
            }
            
            mock_detection_results.append(new_result)
            if len(mock_detection_results) > 50:
                mock_detection_results.pop(0)
            
            self.wfile.write(json.dumps(mock_detection_results).encode())
            return
        
        # Default response for other paths
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        if self.path.startswith('/api/upload'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Here you would process the uploaded image
            # For demo purposes, we'll just return a mock response
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "success": True,
                "message": "Image processed successfully",
                "detections": [
                    {"type": "helmet", "detected": True, "confidence": 0.95},
                    {"type": "vest", "detected": True, "confidence": 0.89}
                ]
            }
            
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Default response for other paths
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()