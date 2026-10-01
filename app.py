import os
import sys

# 0. Suppress harmless ONNX Runtime device discovery warnings
os.environ["ORT_LOG_SEVERITY_LEVEL"] = "3"

# 1. ZeroGPU Support for Hugging Face Spaces (MUST be imported before any CUDA / Torch / ONNX / CV2)
try:
    import spaces
    HAS_SPACES = True
except ImportError:
    HAS_SPACES = False
    class spaces:
        @staticmethod
        def GPU(func=None, **kwargs):
            if func is not None:
                return func
            def decorator(f):
                return f
            return decorator

import secrets
import cv2
import numpy as np

# 2. Environment & Path configuration
DEV_SECRET = "dev-secret-change-me"
DEV_JWT_SECRET = "dev-jwt-secret-change-me"

# Auto-generate secure tokens on Hugging Face Spaces if not set
if os.environ.get("SPACE_ID"):
    if not os.environ.get("SECRET_KEY") or os.environ.get("SECRET_KEY") == DEV_SECRET:
        os.environ["SECRET_KEY"] = secrets.token_urlsafe(48)
    if not os.environ.get("JWT_SECRET_KEY") or os.environ.get("JWT_SECRET_KEY") == DEV_JWT_SECRET:
        os.environ["JWT_SECRET_KEY"] = secrets.token_urlsafe(48)
    if not os.environ.get("TRUSTED_PROXY_HOPS"):
        os.environ["TRUSTED_PROXY_HOPS"] = "1"

# Add backend directory to sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import Flask create_app via importlib to avoid root app.py name collision
import importlib.util
spec = importlib.util.spec_from_file_location("backend_app_module", os.path.join(backend_dir, "app.py"))
backend_app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_app_module)
create_app = backend_app_module.create_app

from ppe_detection import load_model, process_frame

# Initialize Flask WSGI app (handles all /api/* requests from Vercel)
flask_app = create_app()

# Load YOLO / ONNX model
model = load_model()

# Satisfy ZeroGPU scanner at startup
@spaces.GPU(duration=1)
def _zerogpu_probe():
    return True

# 3. Define Gradio Interface for interactive ML testing
@spaces.GPU
def detect_ppe(image, conf_threshold):
    if image is None:
        return None, "### ⚠️ No image provided\nPlease upload an image or capture a webcam photo."
    
    # Gradio passes RGB; convert to BGR for OpenCV / ONNX pipeline
    bgr_frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    annotated_frame, detections = process_frame(bgr_frame, model, draw=True, conf=conf_threshold)
    rgb_output = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
    
    violations = [d['type'] for d in detections if d['type'].startswith("NO-")]
    ppe_items = [d['type'] for d in detections if not d['type'].startswith("NO-") and d['type'] not in ("Person", "machinery", "vehicle")]
    persons = sum(1 for d in detections if d['type'] == "Person")
    
    if violations:
        status = "🚨 **VIOLATION DETECTED — ACCESS DENIED**"
    elif ppe_items:
        status = "✅ **COMPLIANT — ACCESS GRANTED**"
    elif persons > 0:
        status = "⚠️ **PERSON DETECTED (NO PPE CONFIRMED)**"
    else:
        status = "ℹ️ **NO PERSON DETECTED**"
        
    lines = [
        f"### {status}\n",
        f"| Metric | Result |",
        f"| :--- | :--- |",
        f"| **Persons Detected** | {persons} |",
        f"| **Detected PPE** | {', '.join(set(ppe_items)) or 'None'} |",
        f"| **Violations** | {', '.join(set(violations)) or 'None'} |",
        f"| **Total Detections** | {len(detections)} |",
        f"\n*Engine: {model[0].upper() if isinstance(model, tuple) else 'YOLO'}*"
    ]
    return rgb_output, "\n".join(lines)

import gradio as gr
from fastapi import FastAPI
try:
    from a2wsgi import WSGIMiddleware
except ImportError:
    from starlette.middleware.wsgi import WSGIMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

with gr.Blocks(title="SafetyFirst PPE Detection & API Server") as demo:
    gr.Markdown("# 🦺 SafetyFirst — Construction PPE Detection")
    gr.Markdown(
        "> **API Server Status:** 🟢 Active & Serving Vercel at `/api`  \n"
        "> This Hugging Face Space hosts both the interactive detector below and the REST API for your Vercel frontend."
    )
    
    with gr.Row():
        with gr.Column():
            input_img = gr.Image(type="numpy", label="Input Photo or Webcam")
            conf_slider = gr.Slider(minimum=0.1, maximum=0.9, value=0.25, step=0.05, label="Confidence Threshold")
            submit_btn = gr.Button("Analyze PPE Compliance", variant="primary")
        with gr.Column():
            output_img = gr.Image(type="numpy", label="Detection Output")
            report_md = gr.Markdown(label="Compliance Report")
            
    submit_btn.click(fn=detect_ppe, inputs=[input_img, conf_slider], outputs=[output_img, report_md])

demo.queue()

# 4. Create Unified ASGI Application
# Routes:
#   - /api/*       -> Flask API (Auth, Attendance, Gate, CCTV, Notices, etc. for Vercel)
#   - /console*    -> Flask Frontend Console fallback
#   - Everything   -> Gradio UI
class UnifiedApp:
    def __init__(self, gradio_app: ASGIApp, flask_wsgi: ASGIApp):
        self.gradio_app = gradio_app
        self.flask_wsgi = flask_wsgi

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] in ("http", "websocket"):
            path = scope.get("path", "")
            if path.startswith("/api"):
                await self.flask_wsgi(scope, receive, send)
                return
            if path.startswith("/console"):
                scope = dict(scope)
                new_path = path.replace("/console", "", 1) or "/"
                scope["path"] = new_path
                await self.flask_wsgi(scope, receive, send)
                return
        await self.gradio_app(scope, receive, send)

fastapi_app = FastAPI()
fastapi_app = gr.mount_gradio_app(fastapi_app, demo, path="/")
flask_wsgi = WSGIMiddleware(flask_app)
app = UnifiedApp(fastapi_app, flask_wsgi)

if __name__ == "__main__":
    import uvicorn
    import socket
    import time

    port = int(os.environ.get("PORT", 7860))

    # Port reuse wait loop for container redeploys
    for attempt in range(10):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("0.0.0.0", port))
                break
            except OSError:
                print(f"Port {port} busy, waiting for release (attempt {attempt + 1}/10)...", flush=True)
                time.sleep(1)

    print(f"Starting SafetyFirst API & Gradio Server on 0.0.0.0:{port}...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
