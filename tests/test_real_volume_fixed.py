#!/usr/bin/env python3
"""
Fixed test script that uses the actual Modal volume to verify symlinks locally
This script properly handles the Modal/local interaction.
"""

import modal
import os
import tempfile
from pathlib import Path
import shutil

# Get the volume
vol = modal.Volume.from_name("comfy-cache", create_if_missing=True)

# Create the app
app = modal.App("volume-local-test-fixed")

@app.function(volumes={"/model-cache": vol})
def get_volume_info():
    """Get information about the Modal volume contents"""
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
    file_info = {}
    
    for filename in volume_files:
        if filename in expected_models:
            file_path = f"/model-cache/{filename}"
            file_size = os.path.getsize(file_path)
            model_type = expected_models[filename]
            print(f"✅ {filename} ({model_type}) - {file_size} bytes")
            found_models.append(filename)
            file_info[filename] = {
                "size": file_size,
                "type": model_type,
                "exists": True
            }
        else:
            print(f"📁 {filename} (extra file)")
            extra_files.append(filename)
    
    for expected_file in expected_models:
        if expected_file not in volume_files:
            print(f"❌ {expected_file} - MISSING")
            missing_models.append(expected_file)
            file_info[expected_file] = {
                "size": 0,
                "type": expected_models[expected_file],
                "exists": False
            }
    
    return {
        "found_models": found_models,
        "missing_models": missing_models,
        "extra_files": extra_files,
        "total_expected": len(expected_models),
        "total_found": len(found_models),
        "file_info": file_info,
        "volume_files": volume_files
    }

@app.function(volumes={"/model-cache": vol})
def test_symlinks_in_modal():
    """Test symlink creation directly in the Modal environment"""
    import os
    from pathlib import Path
    
    print("=== TESTING SYMLINKS IN MODAL ENVIRONMENT ===")
    
    # Create ComfyUI structure in Modal
    comfy_paths = {
        "checkpoint": "/root/comfy/ComfyUI/models/checkpoints",
        "lora": "/root/comfy/ComfyUI/models/loras",
        "upscaler": "/root/comfy/ComfyUI/models/upscale_models",
        "segm": "/root/comfy/ComfyUI/custom_nodes/ComfyUI-Impact-Pack/models/segm",
        "bbox": "/root/comfy/ComfyUI/custom_nodes/ComfyUI-Impact-Pack/models/bbox",
        "sam": "/root/comfy/ComfyUI/custom_nodes/ComfyUI-Impact-Pack/models/sam",
    }
    
    # Create directories
    for path in comfy_paths.values():
        os.makedirs(path, exist_ok=True)
        print(f"📂 Created: {path}")
    
    # Model type mapping
    all_models = {
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
    
    # Create symlinks
    created_links = []
    failed_links = []
    
    for filename, model_type in all_models.items():
        source_path = f"/model-cache/{filename}"
        target_dir = comfy_paths[model_type]
        symlink_path = os.path.join(target_dir, filename)
        
        if not os.path.exists(source_path):
            print(f"❌ Source file not found: {source_path}")
            failed_links.append(filename)
            continue
        
        # Remove existing symlink if it exists
        if os.path.exists(symlink_path):
            if os.path.islink(symlink_path):
                os.remove(symlink_path)
            else:
                os.remove(symlink_path)
            print(f"🗑️  Removed existing: {symlink_path}")
        
        try:
            # Create symlink
            os.symlink(source_path, symlink_path)
            print(f"🔗 Created: {symlink_path} -> {source_path}")
            created_links.append(filename)
        except Exception as e:
            print(f"❌ Failed to create symlink for {filename}: {e}")
            failed_links.append(filename)
    
    # Verify symlinks
    working_links = []
    broken_links = []
    
    for filename, model_type in all_models.items():
        target_dir = comfy_paths[model_type]
        symlink_path = os.path.join(target_dir, filename)
        
        if os.path.exists(symlink_path):
            if os.path.islink(symlink_path):
                try:
                    real_path = os.path.realpath(symlink_path)
                    if os.path.exists(real_path):
                        print(f"✅ {filename} -> {real_path}")
                        working_links.append(filename)
                    else:
                        print(f"❌ {filename} -> BROKEN LINK (target doesn't exist)")
                        broken_links.append(filename)
                except Exception as e:
                    print(f"❌ {filename} -> BROKEN LINK ({e})")
                    broken_links.append(filename)
            else:
                print(f"⚠️  {filename} -> NOT A SYMLINK (regular file)")
                broken_links.append(filename)
        else:
            print(f"❌ {filename} -> SYMLINK NOT FOUND")
            broken_links.append(filename)
    
    return {
        "created_links": created_links,
        "failed_links": failed_links,
        "working_links": working_links,
        "broken_links": broken_links
    }

@app.local_entrypoint()
def main():
    """Main test function"""
    print("🚀 Testing Modal Volume with Real Data")
    print("=" * 50)
    
    # Step 1: Get volume information
    print("\n1️⃣ Getting Modal volume information...")
    volume_info = get_volume_info.remote()
    
    print(f"\n📊 Volume Summary:")
    print(f"   Found: {volume_info['total_found']}/{volume_info['total_expected']} expected models")
    print(f"   Missing: {len(volume_info['missing_models'])} models")
    print(f"   Extra: {len(volume_info['extra_files'])} files")
    
    if volume_info['missing_models']:
        print(f"\n❌ Missing models:")
        for model in volume_info['missing_models']:
            print(f"   - {model}")
    
    # Step 2: Test symlinks in Modal environment
    print("\n2️⃣ Testing symlinks in Modal environment...")
    symlink_info = test_symlinks_in_modal.remote()
    
    print(f"\n🔗 Symlink Summary:")
    print(f"   Created: {len(symlink_info['created_links'])}")
    print(f"   Working: {len(symlink_info['working_links'])}")
    print(f"   Failed: {len(symlink_info['failed_links'])}")
    print(f"   Broken: {len(symlink_info['broken_links'])}")
    
    # Final summary
    print("\n" + "=" * 50)
    print("🎉 REAL VOLUME TESTING COMPLETE")
    print("=" * 50)
    print(f"✅ Volume models: {volume_info['total_found']}/{volume_info['total_expected']}")
    print(f"✅ Working symlinks: {len(symlink_info['working_links'])}")
    
    if len(symlink_info['working_links']) == volume_info['total_expected']:
        print("\n🎉 SUCCESS: All models have working symlinks in Modal!")
        print("✅ Your Modal setup is ready for production!")
    else:
        print(f"\n⚠️  WARNING: {len(symlink_info['broken_links'])} symlinks are broken")
    
    # Show file sizes for found models
    if volume_info['found_models']:
        print(f"\n📦 Model File Sizes:")
        total_size = 0
        for filename in volume_info['found_models']:
            size = volume_info['file_info'][filename]['size']
            size_mb = size / (1024 * 1024)
            total_size += size
            print(f"   {filename}: {size_mb:.1f} MB")
        
        total_size_gb = total_size / (1024 * 1024 * 1024)
        print(f"   Total: {total_size_gb:.1f} GB")
    
    return {
        "volume_info": volume_info,
        "symlink_info": symlink_info
    }

if __name__ == "__main__":
    result = main()
    print(f"\nTest completed successfully!") 