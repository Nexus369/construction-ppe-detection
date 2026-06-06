from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

# Mock data for demonstration purposes
mock_detection_results = []

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
                "glove_count": 0,
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
            
            response_data = {"results": mock_detection_results}
            self.wfile.write(json.dumps(response_data).encode())
            return
            
        elif self.path.startswith('/video_feed') or self.path.startswith('/api/video_feed'):
            self.send_response(302)
            self.send_header('Location', 'https://images.unsplash.com/photo-1541888946425-d81bb19240f5?auto=format&fit=crop&w=600&q=80')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            return
        
        # Default response for other paths
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        if self.path.startswith('/api/upload') or self.path.startswith('/api/socket'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Here you would process the uploaded image
            # For demo purposes, we'll just return a mock response
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "success": True,
                "processed": True,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "message": "Image processed successfully",
                "detections": [
                    {"type": "helmet", "detected": True, "confidence": 0.95},
                    {"type": "vest", "detected": True, "confidence": 0.89}
                ]
            }
            
            self.wfile.write(json.dumps(response).encode())
            return
            
        elif self.path.startswith('/api/start'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": "Detection started"}).encode())
            return
            
        elif self.path.startswith('/api/stop'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": "Detection stopped"}).encode())
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