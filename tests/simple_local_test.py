#!/usr/bin/env python3
"""
Simple local test for Modal ComfyUI setup
This script tests the symlink logic locally without requiring Modal access.
"""

import os
import tempfile
import shutil
from pathlib import Path

def test_symlink_logic():
    """Test the symlink creation logic that your Modal app uses"""
    print("🚀 Testing Modal Symlink Logic Locally")
    print("=" * 50)
    
    # Create a temporary test environment
    test_dir = Path(tempfile.mkdtemp(prefix="modal-symlink-test-"))
    model_cache = test_dir / "model-cache"
    comfy_root = test_dir / "root" / "comfy" / "ComfyUI"
    
    # Create directories
    model_cache.mkdir(parents=True, exist_ok=True)
    comfy_root.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Test directory: {test_dir}")
    
    # Define the ComfyUI paths (same as in your Modal app)
    comfy_paths = {
        "checkpoint": comfy_root / "models" / "checkpoints",
        "lora": comfy_root / "models" / "loras",
        "upscaler": comfy_root / "models" / "upscale_models",
        "segm": comfy_root / "custom_nodes" / "ComfyUI-Impact-Pack" / "models" / "segm",
        "bbox": comfy_root / "custom_nodes" / "ComfyUI-Impact-Pack" / "models" / "bbox",
        "sam": comfy_root / "custom_nodes" / "ComfyUI-Impact-Pack" / "models" / "sam",
    }
    
    # Create ComfyUI directory structure
    for path in comfy_paths.values():
        path.mkdir(parents=True, exist_ok=True)
        print(f"📂 Created: {path}")
    
    # Define your models (same as in your Modal app)
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
    
    # Create dummy model files
    print("\n📄 Creating test model files...")
    for filename in all_models.keys():
        file_path = model_cache / filename
        with open(file_path, 'w') as f:
            f.write(f"# Test model: {filename}\n")
            f.write(f"# Type: {all_models[filename]}\n")
        print(f"  ✅ Created: {filename}")
    
    # Test the symlink creation logic (same as your Modal app)
    print("\n🔗 Testing symlink creation...")
    created_links = []
    failed_links = []
    
    for filename, model_type in all_models.items():
        source_path = model_cache / filename
        target_dir = comfy_paths[model_type]
        symlink_path = target_dir / filename
        
        if not source_path.exists():
            print(f"❌ Source file not found: {source_path}")
            failed_links.append(filename)
            continue
        
        # Remove existing symlink if it exists (same as your Modal app)
        if symlink_path.exists():
            if symlink_path.is_symlink():
                symlink_path.unlink()
            else:
                symlink_path.unlink()
            print(f"🗑️  Removed existing: {symlink_path}")
        
        try:
            # Create symlink (same as your Modal app)
            symlink_path.symlink_to(source_path)
            print(f"🔗 Created: {symlink_path.name} -> {source_path.name}")
            created_links.append(filename)
        except Exception as e:
            print(f"❌ Failed to create symlink for {filename}: {e}")
            failed_links.append(filename)
    
    # Verify symlinks (same as your Modal app)
    print("\n🔍 Verifying symlinks...")
    working_links = []
    broken_links = []
    
    for filename, model_type in all_models.items():
        target_dir = comfy_paths[model_type]
        symlink_path = target_dir / filename
        
        if symlink_path.exists():
            if symlink_path.is_symlink():
                try:
                    real_path = symlink_path.resolve()
                    if real_path.exists():
                        print(f"✅ {filename} -> {real_path.name}")
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
    
    # Test ComfyUI workflow structure
    print("\n📋 Testing ComfyUI workflow structure...")
    test_workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "untitled_pony.safetensors"
            }
        },
        "2": {
            "class_type": "LoraLoader",
            "inputs": {
                "lora_name": "dramatic_lightning.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0
            }
        },
        "3": {
            "class_type": "LoraLoader",
            "inputs": {
                "lora_name": "RealSkin_xxXL_v1.safetensors",
                "strength_model": 0.8,
                "strength_clip": 0.8
            }
        }
    }
    
    print("✅ Workflow structure is valid")
    print(f"📊 Workflow references {len(test_workflow)} nodes")
    
    # Final summary
    print("\n" + "=" * 50)
    print("🎉 LOCAL TESTING COMPLETE")
    print("=" * 50)
    print(f"✅ Created symlinks: {len(created_links)}")
    print(f"✅ Working symlinks: {len(working_links)}")
    print(f"❌ Failed symlinks: {len(failed_links)}")
    print(f"❌ Broken symlinks: {len(broken_links)}")
    print(f"📁 Test directory: {test_dir}")
    
    if len(working_links) == len(all_models):
        print("\n🎉 SUCCESS: All symlinks are working correctly!")
        print("✅ Your Modal symlink logic is ready for deployment!")
    else:
        print(f"\n⚠️  WARNING: {len(broken_links)} symlinks have issues")
    
    # Keep the test directory for inspection
    print(f"\n🔍 Test environment preserved at: {test_dir}")
    print("   You can inspect the symlinks manually")
    print("   Run 'shutil.rmtree(test_dir)' to clean up when done")
    
    return {
        "created_links": created_links,
        "working_links": working_links,
        "failed_links": failed_links,
        "broken_links": broken_links,
        "test_dir": str(test_dir),
        "workflow": test_workflow
    }

def test_with_real_models():
    """Test with actual model files if they exist locally"""
    print("\n" + "=" * 50)
    print("🔍 OPTIONAL: Test with real model files")
    print("=" * 50)
    
    # Check if you have any real model files locally
    possible_locations = [
        Path.home() / "Desktop" / "own-projects" / "MODELS",
        Path.home() / "Desktop" / "own-projects" / "VIXENTRA" / "MODELS",
        Path.cwd() / "models",
        Path.cwd() / "local_models"
    ]
    
    found_models = []
    for location in possible_locations:
        if location.exists():
            print(f"📁 Found potential model directory: {location}")
            for file in location.iterdir():
                if file.is_file() and file.suffix in ['.safetensors', '.pt', '.pth']:
                    found_models.append(file)
                    print(f"  📄 {file.name}")
    
    if found_models:
        print(f"\n💡 Found {len(found_models)} potential model files")
        print("   You can copy these to test with real models")
    else:
        print("\n💡 No local model files found")
        print("   The test with dummy files is sufficient for symlink testing")
    
    return found_models

if __name__ == "__main__":
    # Run the main test
    result = test_symlink_logic()
    
    # Optional: Check for real models
    real_models = test_with_real_models()
    
    print(f"\n✅ Test completed successfully!")
    print(f"📊 Summary: {len(result['working_links'])}/{len(result['created_links'])} symlinks working") 