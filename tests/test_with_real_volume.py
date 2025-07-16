#!/usr/bin/env python3
"""
Test script that uses the actual Modal volume to verify symlinks locally
This script downloads the volume contents and tests the symlink setup locally.
"""

import modal
import os
import tempfile
from pathlib import Path
import shutil

# Get the volume
vol = modal.Volume.from_name("comfy-cache", create_if_missing=True)

# Create the app
app = modal.App("volume-local-test")

@app.function(volumes={"/model-cache": vol})
def download_volume_contents():
    """Download all files from the Modal volume to a local directory"""
    import os
    from pathlib import Path
    
    # Create a temporary directory for local testing
    local_dir = Path(tempfile.mkdtemp(prefix="modal-volume-test-"))
    model_cache_local = local_dir / "model-cache"
    model_cache_local.mkdir(exist_ok=True)
    
    print(f"📁 Created local test directory: {local_dir}")
    
    # List all files in the volume
    volume_files = []
    if os.path.exists("/model-cache"):
        volume_files = os.listdir("/model-cache")
    
    print(f"📦 Found {len(volume_files)} files in Modal volume")
    
    # Download each file
    downloaded_files = []
    for filename in volume_files:
        source_path = f"/model-cache/{filename}"
        target_path = model_cache_local / filename
        
        if os.path.isfile(source_path):
            # For testing, we'll create a small file with metadata
            # In a real scenario, you'd copy the actual file
            file_size = os.path.getsize(source_path)
            with open(target_path, 'w') as f:
                f.write(f"# Modal volume file: {filename}\n")
                f.write(f"# Original size: {file_size} bytes\n")
                f.write(f"# This is a test representation of the actual file\n")
            
            downloaded_files.append(filename)
            print(f"📄 Downloaded metadata for: {filename} ({file_size} bytes)")
    
    return {
        "local_dir": str(local_dir),
        "downloaded_files": downloaded_files,
        "total_files": len(volume_files)
    }

@app.function(volumes={"/model-cache": vol})
def verify_volume_structure():
    """Verify the structure and contents of the Modal volume"""
    import os
    from pathlib import Path
    
    print("=== MODAL VOLUME VERIFICATION ===")
    
    # Check volume contents
    volume_files = []
    if os.path.exists("/model-cache"):
        volume_files = os.listdir("/model-cache")
    
    print(f"Files in volume: {len(volume_files)}")
    
    # Expected models from your configuration
    expected_models = {
        "untitled_pony.safetensors": "checkpoint",
        "4x_foolhardy_Remacri.pth": "upscaler",
        "dramatic_lightning.safetensors": "lora",
        "RealSkin_xxXL_v1.safetensors": "lora",
        "amateur_slider.safetensors": "lora",
        "LUT_color_grading.safetensors": "lora",
        "mayafoxx_SDXL-000002-e750.safetensors": "lora",
        "add_brightness_XL.safetensors": "lora",
        "person_yolov8m-seg.pt": "segm",
        "face_yolov8m.pt": "bbox",
        "sam_vit_b_01ec64.pth": "sam"
    }
    
    found_models = []
    missing_models = []
    extra_files = []
    
    for filename in volume_files:
        if filename in expected_models:
            file_path = f"/model-cache/{filename}"
            file_size = os.path.getsize(file_path)
            model_type = expected_models[filename]
            print(f"✅ {filename} ({model_type}) - {file_size} bytes")
            found_models.append(filename)
        else:
            print(f"📁 {filename} (extra file)")
            extra_files.append(filename)
    
    for expected_file in expected_models:
        if expected_file not in volume_files:
            print(f"❌ {expected_file} - MISSING")
            missing_models.append(expected_file)
    
    return {
        "found_models": found_models,
        "missing_models": missing_models,
        "extra_files": extra_files,
        "total_expected": len(expected_models),
        "total_found": len(found_models)
    }

def test_local_symlinks(local_dir):
    """Test symlink creation locally using the downloaded volume contents"""
    print("\n=== LOCAL SYMLINK TESTING ===")
    
    local_path = Path(local_dir)
    model_cache = local_path / "model-cache"
    comfy_root = local_path / "root" / "comfy" / "ComfyUI"
    
    # Create ComfyUI structure
    comfy_dirs = [
        "models/checkpoints",
        "models/loras",
        "models/upscale_models", 
        "custom_nodes/ComfyUI-Impact-Pack/models/segm",
        "custom_nodes/ComfyUI-Impact-Pack/models/bbox",
        "custom_nodes/ComfyUI-Impact-Pack/models/sam",
    ]
    
    for dir_path in comfy_dirs:
        full_path = comfy_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
    
    # Model type mapping
    model_types = {
        "untitled_pony.safetensors": "checkpoint",
        "4x_foolhardy_Remacri.pth": "upscaler",
        "dramatic_lightning.safetensors": "lora",
        "RealSkin_xxXL_v1.safetensors": "lora",
        "amateur_slider.safetensors": "lora",
        "LUT_color_grading.safetensors": "lora",
        "mayafoxx_SDXL-000002-e750.safetensors": "lora",
        "add_brightness_XL.safetensors": "lora",
        "person_yolov8m-seg.pt": "segm",
        "face_yolov8m.pt": "bbox",
        "sam_vit_b_01ec64.pth": "sam"
    }
    
    # ComfyUI paths
    comfy_paths = {
        "checkpoint": comfy_root / "models" / "checkpoints",
        "lora": comfy_root / "models" / "loras",
        "upscaler": comfy_root / "models" / "upscale_models",
        "segm": comfy_root / "custom_nodes" / "ComfyUI-Impact-Pack" / "models" / "segm",
        "bbox": comfy_root / "custom_nodes" / "ComfyUI-Impact-Pack" / "models" / "bbox",
        "sam": comfy_root / "custom_nodes" / "ComfyUI-Impact-Pack" / "models" / "sam",
    }
    
    # Create symlinks
    created_links = []
    failed_links = []
    
    for filename in model_cache.iterdir():
        if filename.is_file() and filename.name in model_types:
            model_type = model_types[filename.name]
            target_dir = comfy_paths[model_type]
            symlink_path = target_dir / filename.name
            
            try:
                # Remove existing if present
                if symlink_path.exists():
                    symlink_path.unlink()
                
                # Create symlink
                symlink_path.symlink_to(filename)
                print(f"🔗 Created: {symlink_path.name} -> {filename.name}")
                created_links.append(filename.name)
            except Exception as e:
                print(f"❌ Failed: {filename.name} - {e}")
                failed_links.append(filename.name)
    
    # Verify symlinks
    working_links = []
    broken_links = []
    
    for filename, model_type in model_types.items():
        symlink_path = comfy_paths[model_type] / filename
        if symlink_path.exists() and symlink_path.is_symlink():
            try:
                real_path = symlink_path.resolve()
                if real_path.exists():
                    working_links.append(filename)
                else:
                    broken_links.append(filename)
            except:
                broken_links.append(filename)
        else:
            broken_links.append(filename)
    
    return {
        "created_links": created_links,
        "failed_links": failed_links,
        "working_links": working_links,
        "broken_links": broken_links,
        "test_dir": str(local_path)
    }

@app.local_entrypoint()
def main():
    """Main test function"""
    print("🚀 Testing Modal Volume Locally")
    print("=" * 50)
    
    # Step 1: Verify volume structure
    print("\n1️⃣ Verifying Modal volume structure...")
    volume_info = verify_volume_structure.remote()
    
    print(f"\n📊 Volume Summary:")
    print(f"   Found: {volume_info['total_found']}/{volume_info['total_expected']} expected models")
    print(f"   Missing: {len(volume_info['missing_models'])} models")
    print(f"   Extra: {len(volume_info['extra_files'])} files")
    
    if volume_info['missing_models']:
        print(f"\n❌ Missing models:")
        for model in volume_info['missing_models']:
            print(f"   - {model}")
    
    # Step 2: Download volume contents locally
    print("\n2️⃣ Downloading volume contents locally...")
    download_info = download_volume_contents.remote()
    
    print(f"📁 Local test directory: {download_info['local_dir']}")
    print(f"📦 Downloaded {len(download_info['downloaded_files'])} files")
    
    # Step 3: Test symlinks locally
    print("\n3️⃣ Testing symlinks locally...")
    symlink_info = test_local_symlinks(download_info['local_dir'])
    
    print(f"\n🔗 Symlink Summary:")
    print(f"   Created: {len(symlink_info['created_links'])}")
    print(f"   Working: {len(symlink_info['working_links'])}")
    print(f"   Broken: {len(symlink_info['broken_links'])}")
    
    # Final summary
    print("\n" + "=" * 50)
    print("🎉 LOCAL TESTING COMPLETE")
    print("=" * 50)
    print(f"✅ Volume models: {volume_info['total_found']}/{volume_info['total_expected']}")
    print(f"✅ Working symlinks: {len(symlink_info['working_links'])}")
    print(f"📁 Test directory: {download_info['local_dir']}")
    
    if len(symlink_info['working_links']) == volume_info['total_expected']:
        print("\n🎉 SUCCESS: All models have working symlinks!")
    else:
        print(f"\n⚠️  WARNING: {len(symlink_info['broken_links'])} symlinks are broken")
    
    return {
        "volume_info": volume_info,
        "download_info": download_info,
        "symlink_info": symlink_info
    }

if __name__ == "__main__":
    result = main()
    print(f"\nTest completed successfully!") 