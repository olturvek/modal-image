import modal

# Get the volume
vol = modal.Volume.from_name("comfy-cache", create_if_missing=True)

# Create the app
app = modal.App("volume-checker")

@app.function(volumes={"/cache": vol})
def check_volume_contents():
    """Check what's actually in the volume cache."""
    import os
    from pathlib import Path
    
    print("=== CHECKING VOLUME CONTENTS ===")
    
    # Check the cache directory
    cache_path = Path("/cache")
    if cache_path.exists():
        print(f"Cache directory exists: {cache_path}")
        print("\nFiles in cache:")
        for item in cache_path.iterdir():
            if item.is_file():
                size = item.stat().st_size
                size_mb = size / (1024 * 1024)
                print(f"  📁 {item.name} ({size_mb:.1f} MB)")
            else:
                print(f"  📂 {item.name} (directory)")
    else:
        print("❌ Cache directory does not exist")
    
    # Check for specific models we expect
    expected_models = [
        # CivitAI models
        "untitled_pony.safetensors",
        "4x_foolhardy_Remacri.pth", 
        "dramatic_lightning.safetensors",
        "RealSkin_xxXL_v1.safetensors",
        "amateur_slider.safetensors",
        "LUT_color_grading.safetensors",
        
        # Local models
        "mayafoxx_SDXL-000002-e750.safetensors",
        "perfect_hands.safetensors",
        "add_brightness_XL.safetensors",
        
        # Face detailer models
        "person_yolov8m-seg.pt",
        "face_yolov8m.pt", 
        "sam_vit_b_01ec64.pth"
    ]
    
    print(f"\n=== CHECKING EXPECTED MODELS ===")
    found_models = []
    missing_models = []
    
    for model in expected_models:
        model_path = cache_path / model
        if model_path.exists():
            size = model_path.stat().st_size
            size_mb = size / (1024 * 1024)
            print(f"✅ {model} ({size_mb:.1f} MB)")
            found_models.append(model)
        else:
            print(f"❌ {model} - NOT FOUND")
            missing_models.append(model)
    
    print(f"\n=== SUMMARY ===")
    print(f"Found: {len(found_models)}/{len(expected_models)} models")
    print(f"Missing: {len(missing_models)} models")
    
    if missing_models:
        print(f"\nMissing models:")
        for model in missing_models:
            print(f"  - {model}")
    
    return {
        "found": found_models,
        "missing": missing_models,
        "total_expected": len(expected_models)
    }

if __name__ == "__main__":
    # Run the check
    result = check_volume_contents.remote()
    print(f"\nCheck completed: {result}") 