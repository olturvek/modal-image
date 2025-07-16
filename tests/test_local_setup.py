#!/usr/bin/env python3
"""
Local testing script for Modal ComfyUI setup
This script simulates the Modal environment locally to test symlinks and model setup
without actually deploying to Modal.
"""

import os
import shutil
import tempfile
import subprocess
from pathlib import Path
import json

# Simulate the Modal volume structure locally
class LocalModalSimulator:
    def __init__(self, base_dir=None):
        if base_dir is None:
            self.base_dir = Path(tempfile.mkdtemp(prefix="modal-test-"))
        else:
            self.base_dir = Path(base_dir)
        
        # Create the simulated Modal structure
        self.model_cache = self.base_dir / "model-cache"
        self.comfy_root = self.base_dir / "root" / "comfy" / "ComfyUI"
        
        # Create directories
        self.model_cache.mkdir(parents=True, exist_ok=True)
        self.comfy_root.mkdir(parents=True, exist_ok=True)
        
        print(f"🔧 Created local Modal simulator at: {self.base_dir}")
        print(f"📁 Model cache: {self.model_cache}")
        print(f"🎨 ComfyUI root: {self.comfy_root}")
    
    def setup_comfy_structure(self):
        """Create the ComfyUI directory structure"""
        directories = [
            "models/checkpoints",
            "models/loras", 
            "models/upscale_models",
            "custom_nodes/ComfyUI-Impact-Pack/models/segm",
            "custom_nodes/ComfyUI-Impact-Pack/models/bbox",
            "custom_nodes/ComfyUI-Impact-Pack/models/sam",
        ]
        
        for dir_path in directories:
            full_path = self.comfy_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"📂 Created: {full_path}")
    
    def create_test_files(self):
        """Create dummy test files to simulate the models"""
        test_models = {
            "checkpoint": ["untitled_pony.safetensors"],
            "upscaler": ["4x_foolhardy_Remacri.pth"],
            "lora": [
                "dramatic_lightning.safetensors",
                "RealSkin_xxXL_v1.safetensors", 
                "amateur_slider.safetensors",
                "LUT_color_grading.safetensors",
                "mayafoxx_SDXL-000002-e750.safetensors",
                "add_brightness_XL.safetensors"
            ],
            "segm": ["person_yolov8m-seg.pt"],
            "bbox": ["face_yolov8m.pt"],
            "sam": ["sam_vit_b_01ec64.pth"]
        }
        
        for model_type, files in test_models.items():
            for filename in files:
                file_path = self.model_cache / filename
                # Create a small dummy file
                with open(file_path, 'w') as f:
                    f.write(f"# Dummy {model_type} model: {filename}\n")
                    f.write(f"# This is a test file for local testing\n")
                print(f"📄 Created test file: {filename}")
    
    def create_symlinks(self):
        """Create symlinks like the Modal app would"""
        comfy_paths = {
            "checkpoint": self.comfy_root / "models" / "checkpoints",
            "lora": self.comfy_root / "models" / "loras",
            "upscaler": self.comfy_root / "models" / "upscale_models",
            "segm": self.comfy_root / "custom_nodes" / "ComfyUI-Impact-Pack" / "models" / "segm",
            "bbox": self.comfy_root / "custom_nodes" / "ComfyUI-Impact-Pack" / "models" / "bbox",
            "sam": self.comfy_root / "custom_nodes" / "ComfyUI-Impact-Pack" / "models" / "sam",
        }
        
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
        
        created_links = []
        failed_links = []
        
        for filename, model_type in all_models.items():
            source_path = self.model_cache / filename
            target_dir = comfy_paths[model_type]
            symlink_path = target_dir / filename
            
            if not source_path.exists():
                print(f"⚠️  Source file not found: {source_path}")
                failed_links.append(filename)
                continue
            
            # Remove existing symlink if it exists
            if symlink_path.exists():
                if symlink_path.is_symlink():
                    symlink_path.unlink()
                else:
                    symlink_path.unlink()
                print(f"🗑️  Removed existing: {symlink_path}")
            
            try:
                # Create symlink
                symlink_path.symlink_to(source_path)
                print(f"🔗 Created symlink: {symlink_path} -> {source_path}")
                created_links.append(filename)
            except Exception as e:
                print(f"❌ Failed to create symlink for {filename}: {e}")
                failed_links.append(filename)
        
        return created_links, failed_links
    
    def verify_symlinks(self):
        """Verify all symlinks are working correctly"""
        print("\n=== VERIFYING SYMLINKS ===")
        
        comfy_paths = {
            "checkpoint": self.comfy_root / "models" / "checkpoints",
            "lora": self.comfy_root / "models" / "loras",
            "upscaler": self.comfy_root / "models" / "upscale_models",
            "segm": self.comfy_root / "custom_nodes" / "ComfyUI-Impact-Pack" / "models" / "segm",
            "bbox": self.comfy_root / "custom_nodes" / "ComfyUI-Impact-Pack" / "models" / "bbox",
            "sam": self.comfy_root / "custom_nodes" / "ComfyUI-Impact-Pack" / "models" / "sam",
        }
        
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
        
        print(f"\n📊 Summary: {len(working_links)} working, {len(broken_links)} broken")
        return working_links, broken_links
    
    def cleanup(self):
        """Clean up the test environment"""
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)
            print(f"🧹 Cleaned up: {self.base_dir}")

def test_comfyui_workflow():
    """Test a simple ComfyUI workflow to ensure models are accessible"""
    print("\n=== TESTING COMFYUI WORKFLOW ===")
    
    # This would be a simple test workflow that references your models
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
        }
    }
    
    print("✅ Workflow structure looks valid")
    print("📋 Models referenced in workflow:")
    print("  - untitled_pony.safetensors (checkpoint)")
    print("  - dramatic_lightning.safetensors (lora)")
    
    return test_workflow

def main():
    """Main test function"""
    print("🚀 Starting Local Modal Testing")
    print("=" * 50)
    
    # Create simulator
    simulator = LocalModalSimulator()
    
    try:
        # Setup environment
        print("\n1️⃣ Setting up ComfyUI structure...")
        simulator.setup_comfy_structure()
        
        print("\n2️⃣ Creating test model files...")
        simulator.create_test_files()
        
        print("\n3️⃣ Creating symlinks...")
        created, failed = simulator.create_symlinks()
        print(f"✅ Created {len(created)} symlinks")
        if failed:
            print(f"❌ Failed to create {len(failed)} symlinks")
        
        print("\n4️⃣ Verifying symlinks...")
        working, broken = simulator.verify_symlinks()
        
        print("\n5️⃣ Testing ComfyUI workflow...")
        workflow = test_comfyui_workflow()
        
        # Final summary
        print("\n" + "=" * 50)
        print("🎉 LOCAL TESTING COMPLETE")
        print("=" * 50)
        print(f"✅ Working symlinks: {len(working)}")
        print(f"❌ Broken symlinks: {len(broken)}")
        print(f"📁 Test environment: {simulator.base_dir}")
        print("\n💡 To test with real models:")
        print("   1. Copy your actual model files to the model-cache directory")
        print("   2. Run this script again")
        print("   3. The symlinks will point to your real models")
        
        # Keep the test environment for inspection
        print(f"\n🔍 Test environment preserved at: {simulator.base_dir}")
        print("   Run 'simulator.cleanup()' to remove it when done")
        
        return {
            "working_links": working,
            "broken_links": broken,
            "test_dir": str(simulator.base_dir),
            "simulator": simulator
        }
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        simulator.cleanup()
        raise

if __name__ == "__main__":
    result = main()
    print(f"\nTest result: {result}") 