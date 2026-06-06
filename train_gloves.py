from ultralytics import YOLO
import os

def train_model():
    # Path to the data.yaml file
    data_yaml_path = os.path.join(os.getcwd(), 'PPE Gloves.v1i.yolov8', 'data.yaml')
    
    if not os.path.exists(data_yaml_path):
        print(f"Error: Could not find data.yaml at {data_yaml_path}")
        return

    print(f"Starting training with dataset: {data_yaml_path}")
    
    # Load a pretrained YOLOv8n model
    model = YOLO('yolov8n.pt')
    
    # Train the model
    # Note: Using small number of epochs for demonstration. 
    # Increase epochs for better accuracy (e.g., 50 or 100)
    results = model.train(
        data=data_yaml_path,
        epochs=25,
        imgsz=640,
        batch=16,
        name='ppe_gloves_model'
    )
    
    print("Training completed!")
    print(f"Results saved to: {results.save_dir}")
    print("You can find your new model 'best.pt' in the weights folder of the results directory.")

if __name__ == "__main__":
    train_model()
