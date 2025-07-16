import os
import subprocess
import shutil

import modal
from modal import App, Volume, Image

# Persisted volume where your models are stored
tmp_volume = Volume.from_name("comfy-cache", create_if_missing=True)

# App definition with wget installed
app = App(
    "comfy-civitai-downloader",
    image=Image.debian_slim().apt_install("wget"),
    volumes={"/model-cache": tmp_volume},
    secrets=[modal.Secret.from_name("civit-key")]
)

# Mapping of model types to ComfyUI subdirectories
COMFY_PATHS = {
    "checkpoint": "/root/comfy/ComfyUI/models/checkpoints",
    "lora":       "/root/comfy/ComfyUI/models/loras",
    "upscaler":   "/root/comfy/ComfyUI/models/upscale_models",
    "segm":       "/root/comfy/ComfyUI/custom_nodes/ComfyUI-Impact-Pack/models/segm",
    "bbox":       "/root/comfy/ComfyUI/custom_nodes/ComfyUI-Impact-Pack/models/bbox",
    "sam":        "/root/comfy/ComfyUI/custom_nodes/ComfyUI-Impact-Pack/models/sam",
}

# Define which models to download: {model_type: model_id}
MODELS = {
    "1": {
        "type": "checkpoint",  # e.g., Stable-diffusion model ID
        "id": "1764228",  # e.g., LoRA model ID
        "name": "untitled_pony.safetensors"
    },
    "2": {
        "type": "upscaler",
        "id": "164821",
        "name": "4x_foolhardy_Remacri.pth"
    },
    "3": {
        "type": "lora",
        "id": "1242203",
        "name": "dramatic_lightning.safetensors"
    },
    "4": {
        "type": "lora",
        "id": "1681921",
        "name": "RealSkin_xxXL_v1.safetensors"
    },
    "5": {
        "type": "lora",
        "id": "1594293",
        "name": "amateur_slider.safetensors"
    },
    "6": {
        "type": "lora",
        "id": "1854599",
        "name": "LUT_color_grading.safetensors"
    },
}

NEW_MODELS = {
    "14": {
        "type": "checkpoint",
        "id": "1971591",
        "name": "lucentxlPonyByKlaabu_b20.safetensors"
    },
    "15": {
        "type": "lora",
        "id": "1627770",
        "name": "leaked_nudes_style_v1_fixed.safetensors"
    },
    "16": {
        "type": "lora",
        "id": "1726904",
        "name": "puffytits_PONY_v1.safetensors"
    },
}

FURTHER_MODELS = {
    "17": {
        "type": "lora",
        "id": "1356581",
        "name": "hand_pony_style_v1.safetensors"
    },
    "18": {
        "type": "lora",
        "id": "1386847",
        "name": "body_weight_slider_v1.safetensors"
    },
}

LOCAL_MODELS = {
    "8": {
        "type": "lora",
        "name": "mayafoxx_SDXL-000002-e750.safetensors"
    },
    "10": {
        "type": "lora",
        "name": "add_brightness_XL.safetensors"
    },
}

FACEDETAILER_MODELS = {
    "11": {
        "type": "segm",
        "name": "person_yolov8m-seg.pt"
    },
    "12": {
        "type": "bbox",
        "name": "face_yolov8m.pt"
    },
    "13": {
        "type": "sam",
        "name": "sam_vit_b_01ec64.pth"
    },
}

# Merge the dictionaries
ALL_MODELS = MODELS | NEW_MODELS | FURTHER_MODELS | LOCAL_MODELS | FACEDETAILER_MODELS

@app.function(volumes={"/model-cache": tmp_volume})
def download_and_link_civitai_model(model_type: str, model_id: str, desired_filename: str):
    """Download a Civitai model, rename it to desired filename, and symlink it for ComfyUI."""
    if model_type not in COMFY_PATHS:
        raise ValueError(f"Unknown model_type: {model_type}")

    # Get the API key from Modal's secret management
    token = os.environ["CIVIT_API_KEY"]

    # Construct download URL and temporary path
    url = f"https://civitai.com/api/download/models/{model_id}?token={token}"
    temp_path = f"/model-cache/temp_{model_id}"
    final_cache_path = f"/model-cache/{desired_filename}"

    print(f"Downloading {model_type} {model_id} to temporary location...")
    
    # Download to temporary file first
    result = subprocess.run(["wget", "-q", "-O", temp_path, url], check=True)
    
    # Check if file was downloaded successfully
    if not os.path.exists(temp_path):
        raise RuntimeError(f"Download failed for model {model_id}")
    
    # Remove existing file if it exists
    if os.path.exists(final_cache_path):
        os.remove(final_cache_path)
        print(f"Removed existing file: {final_cache_path}")
    
    # Rename to desired filename
    shutil.move(temp_path, final_cache_path)
    print(f"Renamed downloaded file to: {desired_filename}")

    # Prepare ComfyUI folder and symlink
    target_dir = COMFY_PATHS[model_type]
    os.makedirs(target_dir, exist_ok=True)
    symlink_path = os.path.join(target_dir, desired_filename)

    # Remove existing symlink if it exists
    if os.path.exists(symlink_path):
        os.remove(symlink_path)
        print(f"Removed existing symlink: {symlink_path}")

    # Create new symlink
    os.symlink(final_cache_path, symlink_path)
    print(f"Created symlink: {symlink_path} -> {final_cache_path}")

    # Verify the symlink was created correctly
    if os.path.islink(symlink_path):
        print(f"Verified symlink exists and points to: {os.path.realpath(symlink_path)}")
    else:
        raise RuntimeError(f"Failed to create symlink at {symlink_path}")

@app.function(volumes={"/model-cache": tmp_volume})
def create_symlinks_for_models():
    """Create symlinks for existing models in the cache."""
    for key, model in ALL_MODELS.items():
        model_type = model["type"]
        filename = model["name"]
        
        if model_type not in COMFY_PATHS:
            raise ValueError(f"Unknown model_type: {model_type}")

        # Check if the model file exists in cache
        cache_path = f"/model-cache/{filename}"
        if not os.path.exists(cache_path):
            print(f"Warning: Model file not found in cache: {filename}")
            continue

        # Prepare ComfyUI folder and symlink
        target_dir = COMFY_PATHS[model_type]
        os.makedirs(target_dir, exist_ok=True)
        symlink_path = os.path.join(target_dir, filename)

        # Remove existing symlink if it exists
        if os.path.exists(symlink_path):
            os.remove(symlink_path)
            print(f"Removed existing symlink: {symlink_path}")

        # Create new symlink
        os.symlink(cache_path, symlink_path)
        print(f"Created symlink: {symlink_path} -> {cache_path}")

        # Verify the symlink was created correctly
        if os.path.islink(symlink_path):
            print(f"Verified symlink exists and points to: {os.path.realpath(symlink_path)}")
        else:
            raise RuntimeError(f"Failed to create symlink at {symlink_path}")

@app.function(volumes={"/model-cache": tmp_volume})
def check_volume_contents():
    """Check what files are actually in the volume and compare with defined models."""
    print("=== VOLUME CONTENTS CHECK ===")
    
    # Get all files in the volume
    volume_files = []
    if os.path.exists("/model-cache"):
        volume_files = os.listdir("/model-cache")
    
    print(f"Files found in volume: {len(volume_files)}")
    for file in sorted(volume_files):
        file_path = os.path.join("/model-cache", file)
        file_size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
        print(f"  - {file} ({file_size} bytes)")
    
    print("\n=== EXPECTED FILES ===")
    expected_files = []
    for key, model in ALL_MODELS.items():
        filename = model["name"]
        expected_files.append(filename)
        print(f"  - {filename}")
    
    print("\n=== COMPARISON ===")
    missing_files = []
    extra_files = []
    
    for expected in expected_files:
        if expected not in volume_files:
            missing_files.append(expected)
    
    for actual in volume_files:
        if actual not in expected_files:
            extra_files.append(actual)
    
    if missing_files:
        print(f"❌ MISSING FILES ({len(missing_files)}):")
        for file in missing_files:
            print(f"  - {file}")
    else:
        print("✅ All expected files are present!")
    
    if extra_files:
        print(f"📁 EXTRA FILES ({len(extra_files)}):")
        for file in extra_files:
            print(f"  - {file}")
    
    print(f"\nSummary: {len(volume_files)} files in volume, {len(expected_files)} expected")
    print(f"Missing: {len(missing_files)}, Extra: {len(extra_files)}")
    
    return {
        "volume_files": volume_files,
        "expected_files": expected_files,
        "missing_files": missing_files,
        "extra_files": extra_files
    }


@app.local_entrypoint()
def main():
    # Check volume contents first
    print("Checking volume contents...")
    result = check_volume_contents.remote()
    
    # Choose one of these options:
    # 1. Download and create symlinks
    # for key, model in MODELS.items():
    #     download_and_link_civitai_model.remote(model["type"], model["id"], model["name"])

    # 1. Download and create symlinks - WAIT for completion
    download_futures = []
    for key, model in FURTHER_MODELS.items():
        future = download_and_link_civitai_model.remote(model["type"], model["id"], model["name"])
        download_futures.append(future)
    
    # Wait for all downloads to complete
    #for future in download_futures:
    #    future.get()
    
    # 2. Just create symlinks for existing models (LOCAL_MODELS, FACEDETAILER_MODELS)
    create_symlinks_for_models.remote()
    
    # 3. Upload local models using batch upload
    #with tmp_volume.batch_upload() as batch:
    #    batch.put_file(
    #        "/Users/samuelharck/Desktop/own-projects/MODELS/add_brightness_XL.safetensors",
    #        "/add_brightness_XL.safetensors"
    #    )
    #    batch.put_file(
    #        "/Users/samuelharck/Desktop/own-projects/MODELS/mayafoxx_SDXL-000002-e750.safetensors",
    #        "/mayafoxx_SDXL-000002-e750.safetensors"
    #    )
    
    #with tmp_volume.batch_upload() as batch:
        #batch.put_file(
        #    "/Users/samuelharck/Desktop/own-projects/VIXENTRA/MODELS/person_yolov8m-seg.pt",
        #    "/person_yolov8m-seg.pt"
        #)
        #batch.put_file(
        #    "/Users/samuelharck/Desktop/own-projects/VIXENTRA/MODELS/face_yolov8m.pt",
        #    "/face_yolov8m.pt"
        #)
        #batch.put_file(
        #    "/Users/samuelharck/Desktop/own-projects/VIXENTRA/MODELS/sam_vit_b_01ec64.pth",
        #    "/sam_vit_b_01ec64.pth"
        #)
        #batch.put_file(
        #    "/Users/samuelharck/Desktop/own-projects/VIXENTRA/MODELS/hand_pony_v1.safetensors",
        #    "/hand_pony_v1.safetensors"
        #)
    
    # Then create symlinks for models that weren't downloaded (LOCAL_MODELS, FACEDETAILER_MODELS)
    # create_symlinks_for_models.remote()
    pass
