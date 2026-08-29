import os
import cv2
import numpy as np

VIOLATION_PREFIX = "NO-"
HELMET_CLASSES = {"Hardhat", "helmet"}
VEST_CLASSES = {"Safety Vest", "vest"}
GLOVE_CLASSES = {"Gloves", "hand gloves"}

BOX_COLORS = {
    "helmet": (0, 255, 0),
    "vest": (0, 165, 255),
    "gloves": (255, 0, 255),
    "violation": (0, 0, 255),
    "other": (255, 255, 0),
}

NAMES = {
    0: 'Hardhat', 1: 'Mask', 2: 'NO-Hardhat', 3: 'NO-Mask', 4: 'NO-Safety Vest',
    5: 'Person', 6: 'Safety Cone', 7: 'Safety Vest', 8: 'machinery', 9: 'vehicle'
}


def _resolve_model_path():
    if "MODEL_PATH" in os.environ:
        return os.environ["MODEL_PATH"]
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    onnx_candidate = os.path.join(base_dir, "best.onnx")
    if os.path.isfile(onnx_candidate):
        return onnx_candidate
    return os.path.join(base_dir, "best.pt")


def load_model():
    """Load the YOLOv8 PPE detection model.
    Prioritizes pure ONNX Runtime for ultra-low memory (~15MB) and high CPU performance.
    """
    model_path = _resolve_model_path()
    if model_path.endswith(".onnx"):
        try:
            import onnxruntime as ort
            session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
            return ("onnx", session)
        except Exception as e:
            print("ONNX load failed, falling back to PyTorch:", e)

    try:
        import torch
        from ultralytics import YOLO
        original_torch_load = torch.load
        def patched_torch_load(*args, **kwargs):
            kwargs["weights_only"] = False
            return original_torch_load(*args, **kwargs)
        torch.load = patched_torch_load
        try:
            model = YOLO(model_path, task="detect")
            return ("yolo", model)
        finally:
            torch.load = original_torch_load
    except Exception as e:
        print("Ultralytics load failed:", e)
        return None


def _color_for_class(class_name):
    if class_name in HELMET_CLASSES:
        return BOX_COLORS["helmet"]
    if class_name in VEST_CLASSES:
        return BOX_COLORS["vest"]
    if class_name in GLOVE_CLASSES:
        return BOX_COLORS["gloves"]
    if class_name.startswith(VIOLATION_PREFIX):
        return BOX_COLORS["violation"]
    return BOX_COLORS["other"]


def _process_onnx(frame, session, draw=True, conf=0.25):
    h0, w0 = frame.shape[:2]
    img = cv2.resize(frame, (480, 480))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.transpose(2, 0, 1)
    img = np.expand_dims(img, axis=0).astype(np.float32) / 255.0

    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: img})[0]
    preds = outputs[0].T

    boxes = []
    confidences = []
    class_ids = []

    x_factor = w0 / 480.0
    y_factor = h0 / 480.0

    for row in preds:
        scores = row[4:]
        max_idx = int(np.argmax(scores))
        max_conf = float(scores[max_idx])
        if max_conf >= conf:
            cx, cy, w, h = float(row[0]), float(row[1]), float(row[2]), float(row[3])
            x1 = int((cx - w / 2) * x_factor)
            y1 = int((cy - h / 2) * y_factor)
            box_w = int(w * x_factor)
            box_h = int(h * y_factor)

            boxes.append([x1, y1, box_w, box_h])
            confidences.append(max_conf)
            class_ids.append(max_idx)

    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf, 0.45)
    detections = []
    if len(indices) > 0:
        for i in indices.flatten():
            bx, by, bw, bh = boxes[i]
            x1 = max(0, bx)
            y1 = max(0, by)
            x2 = min(w0, bx + bw)
            y2 = min(h0, by + bh)
            cls_name = NAMES.get(class_ids[i], 'unknown')
            conf_val = float(confidences[i])
            detections.append({
                "type": cls_name,
                "detected": True,
                "confidence": conf_val,
                "box": [x1, y1, x2, y2],
            })
            if draw:
                color = _color_for_class(cls_name)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"{cls_name} {conf_val:.2f}"
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    return frame, detections


def process_frame(frame, model_tuple, draw=True, conf=0.25):
    """Run detection on a single BGR frame using ONNX Runtime or PyTorch."""
    if frame is None or model_tuple is None:
        return None, []

    if isinstance(model_tuple, tuple):
        kind, model = model_tuple
    else:
        kind, model = "yolo", model_tuple

    if kind == "onnx":
        return _process_onnx(frame, model, draw=draw, conf=conf)

    import torch
    with torch.inference_mode():
        results = model(frame, conf=conf, iou=0.45, verbose=False, imgsz=480)

    detections = []
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            conf_score = float(box.conf[0])
            class_name = result.names[cls]

            detections.append({
                "type": class_name,
                "detected": True,
                "confidence": conf_score,
                "box": [x1, y1, x2, y2],
            })

            if draw:
                color = _color_for_class(class_name)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"{class_name} {conf_score:.2f}"
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    return frame, detections
