import os
import sys

# 0. Suppress harmless ONNX Runtime device discovery warnings
os.environ["ORT_LOG_SEVERITY_LEVEL"] = "3"

# 1. ZeroGPU Support — MUST be imported before CUDA / Torch / ONNX / CV2
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
            return lambda f: f

import secrets
import cv2
import numpy as np

# 2. Environment & secrets
DEV_SECRET = "dev-secret-change-me"
DEV_JWT_SECRET = "dev-jwt-secret-change-me"

if os.environ.get("SPACE_ID"):
    if not os.environ.get("SECRET_KEY") or os.environ.get("SECRET_KEY") == DEV_SECRET:
        os.environ["SECRET_KEY"] = secrets.token_urlsafe(48)
    if not os.environ.get("JWT_SECRET_KEY") or os.environ.get("JWT_SECRET_KEY") == DEV_JWT_SECRET:
        os.environ["JWT_SECRET_KEY"] = secrets.token_urlsafe(48)
    if not os.environ.get("TRUSTED_PROXY_HOPS"):
        os.environ["TRUSTED_PROXY_HOPS"] = "1"

# 3. Backend path — importlib avoids root app.py name collision
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import importlib.util
spec = importlib.util.spec_from_file_location(
    "backend_app_module", os.path.join(backend_dir, "app.py")
)
backend_app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_app_module)
create_app = backend_app_module.create_app

from ppe_detection import load_model, process_frame

flask_app = create_app()
model = load_model()

# Satisfy ZeroGPU scanner at container startup
@spaces.GPU(duration=1)
def _zerogpu_probe():
    return True

# 4. Gradio PPE detection function (GPU-accelerated when available)
@spaces.GPU
def detect_ppe(image, conf_threshold):
    if image is None:
        return None, "### ⚠️ No image provided\nPlease upload an image or capture a webcam photo."
    bgr_frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    annotated_frame, detections = process_frame(bgr_frame, model, draw=True, conf=conf_threshold)
    rgb_output = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
    violations = [d["type"] for d in detections if d["type"].startswith("NO-")]
    ppe_items  = [d["type"] for d in detections
                  if not d["type"].startswith("NO-")
                  and d["type"] not in ("Person", "machinery", "vehicle")]
    persons = sum(1 for d in detections if d["type"] == "Person")
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
        "| Metric | Result |",
        "| :--- | :--- |",
        f"| **Persons Detected** | {persons} |",
        f"| **Detected PPE** | {', '.join(set(ppe_items)) or 'None'} |",
        f"| **Violations** | {', '.join(set(violations)) or 'None'} |",
        f"| **Total Detections** | {len(detections)} |",
        f"\n*Engine: {model[0].upper() if isinstance(model, tuple) else 'YOLO'}*",
    ]
    return rgb_output, "\n".join(lines)

# 5. Flask-to-ASGI middleware (pure ASGI, no prefix stripping)
from starlette.middleware import Middleware
from starlette.types import ASGIApp, Receive, Scope, Send

try:
    from a2wsgi import WSGIMiddleware
except ImportError:
    from starlette.middleware.wsgi import WSGIMiddleware


class FlaskAPIMiddleware:
    """Routes /api/* requests to Flask; everything else falls through to Gradio."""

    def __init__(self, app: ASGIApp, flask_app=None):
        self.app = app
        self.flask_asgi = WSGIMiddleware(flask_app)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            print(f"MIDDLEWARE SEES: {scope.get('method')} {scope.get('path')}", flush=True)
            if scope.get("path", "").startswith("/api"):
                await self.flask_asgi(scope, receive, send)
                return
        await self.app(scope, receive, send)


# 6. Build Gradio UI
import gradio as gr

with gr.Blocks(title="SafetyFirst PPE Detection & API Server") as demo:
    gr.Markdown("# 🦺 SafetyFirst — Construction PPE Detection")
    gr.Markdown(
        "> **API Server Status:** 🟢 Active & Serving Vercel at `/api`  \n"
        "> This Hugging Face Space hosts both the interactive detector and the "
        "REST API for your Vercel frontend."
    )
    with gr.Row():
        with gr.Column():
            input_img   = gr.Image(type="numpy", label="Input Photo or Webcam")
            conf_slider = gr.Slider(0.1, 0.9, value=0.25, step=0.05,
                                    label="Confidence Threshold")
            submit_btn  = gr.Button("Analyze PPE Compliance", variant="primary")
        with gr.Column():
            output_img = gr.Image(type="numpy", label="Detection Output")
            report_md  = gr.Markdown(label="Compliance Report")
    submit_btn.click(fn=detect_ppe,
                     inputs=[input_img, conf_slider],
                     outputs=[output_img, report_md])

demo.queue()

# 7. Launch — demo.launch() is what HF Spaces expects.
#    HF patches it to handle port 7860 binding correctly (ZeroGPU-safe).
#    Flask routes are injected through FastAPI's middleware constructor
#    via app_kwargs, so /api/* hits Flask and everything else hits Gradio.
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        app_kwargs={"middleware": [Middleware(FlaskAPIMiddleware, flask_app=flask_app)]},
    )
