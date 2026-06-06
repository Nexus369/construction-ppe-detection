from ultralytics import YOLO
import torch

def inspect_model():
    try:
        # Monkey patch torch.load for weights_only compatibility if needed
        original_torch_load = torch.load
        def patched_torch_load(*args, **kwargs):
            kwargs['weights_only'] = False
            return original_torch_load(*args, **kwargs)
        torch.load = patched_torch_load

        model = YOLO('best.pt')
        names = model.names
        print(f"Number of classes: {len(names)}")
        print("Class names:")
        for idx, name in names.items():
            print(f"  {idx}: {name}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        torch.load = original_torch_load

if __name__ == "__main__":
    inspect_model()
