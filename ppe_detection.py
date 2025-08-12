import cv2
import numpy as np
from ultralytics import YOLO
import time
import torch
import os
import sys

def load_model():
    """Load the YOLOv8 model"""
    try:
        print("Attempting to load model...")
        
        # Monkey patch torch.load for this specific call
        original_torch_load = torch.load
        
        def patched_torch_load(*args, **kwargs):
            kwargs['weights_only'] = False
            return original_torch_load(*args, **kwargs)
        
        # Replace torch.load temporarily
        torch.load = patched_torch_load
        
        # Load the model with the patched function
        try:
            model = YOLO('best.pt')
            print("Model loaded successfully!")
        finally:
            # Restore original torch.load even if model loading fails
            torch.load = original_torch_load
        
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        print("If you still face issues, consider:")
        print("1. Using an older version of PyTorch (pre-2.6)")
        print("2. Retraining the model with your current environment")
        return None

def process_frame(frame, model, fps_start):
    """Process a single frame and draw detections with optimized performance"""
    if frame is None or model is None:
        return None
    
    # Perform detection with optimized settings
    results = model(frame, conf=0.25, iou=0.45, verbose=False)
    
    # Process results
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Get box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Get class and confidence
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            
            # Get class name
            class_name = result.names[cls]
            
            # Color coding based on class and confidence
            if class_name == 'Hardhat' or class_name == 'helmet':
                color = (0, 255, 0)  # Green for helmet
            elif class_name == 'Safety Vest' or class_name == 'vest':
                color = (0, 165, 255)  # Orange for vest
            elif class_name.startswith('NO-'):
                color = (0, 0, 255)  # Red for violations
            else:
                color = (255, 255, 0)  # Yellow for other items
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Add label with confidence
            label = f'{class_name} {conf:.2f}'
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Add FPS counter
    fps = cv2.getTickFrequency() / (cv2.getTickCount() - fps_start)
    cv2.putText(frame, f'FPS: {fps:.1f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    return frame

def process_image(image_path, model):
    """Process a single image"""
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not read image at {image_path}")
        return
    
    # Process the image
    processed_image = process_frame(image, model, 0)
    if processed_image is None:
        return
    
    # Save the processed image
    output_path = f"output/processed_{image_path.split('/')[-1]}"
    cv2.imwrite(output_path, processed_image)
    print(f"Processed image saved to {output_path}")

def process_video(video_path, model):
    """Process a video file or camera stream"""
    # Open video capture
    if video_path == 0:  # Use webcam
        cap = cv2.VideoCapture(1)
    else:  # Use video file
        cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("Error: Could not open video source")
        return
    
    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    # Create video writer if processing a video file
    if video_path != 0:
        output_path = f"output/processed_{video_path.split('/')[-1]}"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process frame
        processed_frame = process_frame(frame, model, 0)
        if processed_frame is None:
            break
        
        # Display the frame
        cv2.imshow('PPE Detection', processed_frame)
        
        # Save frame if processing a video file
        if video_path != 0:
            out.write(processed_frame)
        
        # Break if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Clean up
    cap.release()
    if video_path != 0:
        out.release()
    cv2.destroyAllWindows()

def main():
    print("Starting real-time PPE detection...")
    print("Press 'q' to quit")
    
    # Load the model
    model = load_model()
    if model is None:
        print("Failed to load the model. Exiting...")
        return
    
    print("Initializing webcam...")
    # Try the default camera first
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open default camera. Trying external camera...")
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("Error: Could not open any camera. Exiting...")
            return
    
    # Set optimal webcam properties for real-time processing
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("Starting detection loop...")
    while True:
        fps_start = cv2.getTickCount()
        
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break
        
        # Process frame
        processed_frame = process_frame(frame, model, fps_start)
        if processed_frame is None:
            break
        
        # Display the frame
        cv2.imshow('Real-time PPE Detection', processed_frame)
        
        # Break if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    print("PPE detection stopped")

if __name__ == "__main__":
    main()
