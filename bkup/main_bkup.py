import subprocess
import json
from pathlib import Path
from typing import Dict
import uuid
import os
import logging
import time

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress hpack debug logs
logging.getLogger('hpack').setLevel(logging.WARNING)

import modal

import socket
import urllib.request
import urllib.error
import time


vol = modal.Volume.from_name("comfy-cache", create_if_missing=True)

# Use a community ComfyUI image (ComfyUI pre-installed, no models)
image = (  # build up a Modal Image to run ComfyUI, step by step
    modal.Image.debian_slim(  # start from basic Linux with Python
        python_version="3.11"
    )
    .apt_install("git")  # install git to clone ComfyUI
    .pip_install("fastapi[standard]==0.115.4")  # install web dependencies
    .pip_install("comfy-cli==1.4.1")  # install latest comfy-cli
    .run_commands(  # use comfy-cli to install ComfyUI and its dependencies
        "comfy --skip-prompt install --fast-deps --nvidia",  # Remove version constraint to use latest
        # 3) install TBox pack from GitHub
        #"comfy node install --fast-deps https://github.com/ai-shizuka/ComfyUI-tbox.git",
        # 4) install WAS Node Suite from the comfy registry
        "comfy node install --fast-deps was-node-suite-comfyui@1.0.2",
        "comfy node install --fast-deps https://github.com/palant/image-resize-comfyui",
        #"comfy node install --fast-deps https://github.com/ltdrdata/ComfyUI-Manager.git",
        "comfy node install --fast-deps https://github.com/ltdrdata/ComfyUI-Impact-Pack.git",
        #"comfy node install --fast-deps https://github.com/Fannovel16/ComfyUI_Tweaks.git"
    )
)

def create_all_symlinks():
    """Create symlinks for all models in the cache at image build time."""
    import os
    from pathlib import Path

    model_paths = {
        "checkpoint": "/root/comfy/ComfyUI/models/checkpoints/untitled_pony.safetensors",
        "upscaler": "/root/comfy/ComfyUI/models/upscale_models/4x_foolhardy_Remacri.pth",
        "loras": [
            "/root/comfy/ComfyUI/models/loras/dramatic_lightning.safetensors",
            "/root/comfy/ComfyUI/models/loras/RealSkin_xxXL_v1.safetensors",
            "/root/comfy/ComfyUI/models/loras/amateur_slider.safetensors",
            "/root/comfy/ComfyUI/models/loras/LUT_color_grading.safetensors",
            "/root/comfy/ComfyUI/models/loras/mayafoxx_SDXL-000002-e750.safetensors",
            "/root/comfy/ComfyUI/models/loras/perfect_hands.safetensors",
            "/root/comfy/ComfyUI/models/loras/add_brightness_XL.safetensors"
        ]
    }

    # Create directories first
    for path in model_paths.values():
        if isinstance(path, list):
            for p in path:
                Path(p).parent.mkdir(parents=True, exist_ok=True)
        else:
            Path(path).parent.mkdir(parents=True, exist_ok=True)

    # Create symlinks during build time when volume is mounted
    for path in model_paths.values():
        if isinstance(path, list):
            for p in path:
                filename = Path(p).name
                cache_path = f"/cache/{filename}"
                if Path(cache_path).exists():
                    # Remove existing file/symlink if it exists
                    if Path(p).exists():
                        Path(p).unlink()
                    # Create symlink
                    Path(p).symlink_to(cache_path)
                    logger.info(f"Created symlink: {p} -> {cache_path}")
                else:
                    logger.warning(f"Model file not found in cache: {cache_path}")
        else:
            filename = Path(path).name
            cache_path = f"/cache/{filename}"
            if Path(cache_path).exists():
                # Remove existing file/symlink if it exists
                if Path(path).exists():
                    Path(path).unlink()
                # Create symlink
                Path(path).symlink_to(cache_path)
                logger.info(f"Created symlink: {path} -> {cache_path}")
            else:
                logger.warning(f"Model file not found in cache: {cache_path}")

# Update the image build to run create_all_symlinks at build time with volume mounted
image = (
    image.run_commands(
        "mkdir -p /cache",
    )
    .run_function(
        create_all_symlinks,
        volumes={"/cache": vol},  # Mount the volume during build time
    )
)

app = modal.App(
    name="imagegen-comfyui", 
    image=image
)

@app.function(volumes={"/cache": vol})
def check_symlinks():
    """Check if symlinks exist in the volume and print their status."""
    # No need to create runtime symlinks anymore since they're created at build time
    
    model_paths = [
        "/root/comfy/ComfyUI/models/checkpoints/untitled_pony.safetensors",
        "/root/comfy/ComfyUI/models/upscale_models/4x_foolhardy_Remacri.pth",
        "/root/comfy/ComfyUI/models/loras/dramatic_lightning.safetensors",
        "/root/comfy/ComfyUI/models/loras/RealSkin_xxXL_v1.safetensors",
        "/root/comfy/ComfyUI/models/loras/amateur_slider.safetensors",
        "/root/comfy/ComfyUI/models/loras/LUT_color_grading.safetensors",
        "/root/comfy/ComfyUI/models/loras/mayafoxx_SDXL-000002-e750.safetensors",
        "/root/comfy/ComfyUI/models/loras/perfect_hands.safetensors",
        "/root/comfy/ComfyUI/models/loras/add_brightness_XL.safetensors"
    ]
    
    logger.info("Checking symlinks in volume:")
    for path in model_paths:
        p = Path(path)
        if p.exists():
            if p.is_symlink():
                logger.info(f"✓ {path} exists and is a symlink")
                logger.info(f"  Points to: {p.readlink()}")
            else:
                logger.warning(f"! {path} exists but is not a symlink")
        else:
            logger.error(f"✗ {path} does not exist")
    
    # Also check the cache directory
    logger.info("\nChecking cache directory contents:")
    cache_path = Path("/cache")
    if cache_path.exists():
        for item in cache_path.iterdir():
            logger.info(f"- {item.name}")

@app.function(volumes={"/cache": vol})
def check_available_nodes():
    """Check what custom nodes are available in the installed ComfyUI."""
    import os
    from pathlib import Path
    
    logger.info("Checking available custom nodes:")
    
    # Check custom_nodes directory
    custom_nodes_dir = Path("/root/comfy/ComfyUI/custom_nodes")
    if custom_nodes_dir.exists():
        logger.info(f"Custom nodes directory exists: {custom_nodes_dir}")
        for item in custom_nodes_dir.iterdir():
            if item.is_dir():
                logger.info(f"- {item.name}")
    else:
        logger.warning("Custom nodes directory does not exist")
    
    # Check if specific nodes are available by looking for their Python files
    nodes_to_check = [
        "CLIPSetLastLayer",
        "ImageUpscaleWithModel", 
        "ImageScaleBy",
        "ImageResize"
    ]
    
    logger.info("\nChecking for specific nodes:")
    for node_name in nodes_to_check:
        # Look for Python files that might contain this node
        found = False
        for root, dirs, files in os.walk("/root/comfy/ComfyUI"):
            for file in files:
                if file.endswith('.py'):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if node_name in content:
                                logger.info(f"✓ {node_name} found in {os.path.join(root, file)}")
                                found = True
                                break
                    except:
                        continue
            if found:
                break
        
        if not found:
            logger.warning(f"✗ {node_name} not found")
    
    # Also check what's in the ComfyUI nodes directory
    nodes_dir = Path("/root/comfy/ComfyUI/nodes")
    if nodes_dir.exists():
        logger.info(f"\nBuilt-in nodes directory: {nodes_dir}")
        node_files = list(nodes_dir.glob("*.py"))
        logger.info(f"Found {len(node_files)} built-in node files")
    else:
        logger.warning("Built-in nodes directory does not exist")

'''@app.function(
    max_containers=1,  # limit interactive session to 1 container
    gpu="A10G",  # using the same GPU as your ComfyUI class
    volumes={"/cache": vol},  # mounts our cached models
)
@modal.concurrent(max_inputs=10)  # required for UI startup process which runs several API calls concurrently
@modal.web_server(8000, startup_timeout=60)
def ui():
    """Serve the ComfyUI web interface."""
    subprocess.Popen("comfy launch -- --listen 0.0.0.0 --port 8000", shell=True)'''

@app.cls(
    scaledown_window=180,  # 5 minute container keep alive after it processes an input
    gpu="A10G",
    volumes={"/cache": vol},
)
@modal.concurrent(max_inputs=5)  # run 5 inputs per container
class ComfyUI:
    port: int = 8188
    _server_proc = None

    @modal.enter()
    def launch_comfy_background(self):
        # launch the ComfyUI server exactly once when the container starts
        cmd = f"comfy launch --background -- --port {self.port}"
        subprocess.run(cmd, shell=True, check=True)
        
        # Wait for ComfyUI server to be fully ready
        print("Waiting for ComfyUI server to start up...")
        
        # Initial sleep to give the server time to start
        time.sleep(10)
        
        # Poll the server until it's ready (with timeout)
        max_attempts = 30  # 30 attempts * 2 seconds = 60 seconds max
        for attempt in range(max_attempts):
            try:
                # Check if the server is responding
                req = urllib.request.Request(f"http://127.0.0.1:{self.port}/system_stats")
                urllib.request.urlopen(req, timeout=5)
                print(f"ComfyUI server is ready after {attempt + 1} attempts")
                return
            except (socket.timeout, urllib.error.URLError) as e:
                if attempt < max_attempts - 1:
                    print(f"Server not ready yet (attempt {attempt + 1}/{max_attempts}), waiting 2 seconds...")
                    time.sleep(2)
                else:
                    print(f"Server failed to start after {max_attempts} attempts")
                    raise Exception("ComfyUI server failed to start within timeout period")

    @modal.method()
    def infer(self, workflow_path: str = "/root/workflow_api.json"):
        # Guard the cold-start window
        #self._ensure_booted()
        # sometimes the ComfyUI server stops responding (we think because of memory leaks), so this makes sure it's still up
        self.poll_server_health()

        # Check if workflow file exists and show its contents
        if not Path(workflow_path).exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
        
        workflow_content = Path(workflow_path).read_text()
        print(f"Workflow file contents: {workflow_content}")

        # runs the comfy run --workflow command as a subprocess
        cmd = f"comfy run --workflow {workflow_path} --wait --timeout 1200 --verbose"
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"Comfy run stdout: {result.stdout}")
            if result.stderr:
                print(f"Comfy run stderr: {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"Comfy run failed with exit code {e.returncode}")
            print(f"Command stdout: {e.stdout}")
            print(f"Command stderr: {e.stderr}")
            raise

        # completed workflows write output images to this directory
        output_dir = "/root/comfy/ComfyUI/output"
        
        # Check if output directory exists
        if not Path(output_dir).exists():
            print(f"Output directory does not exist: {output_dir}")
            raise FileNotFoundError(f"Output directory not found: {output_dir}")
        
        print(f"Output directory contents: {list(Path(output_dir).iterdir())}")

        # looks up the name of the output image file based on the workflow
        workflow = json.loads(workflow_content)
        file_prefix = [
            node.get("inputs")
            for node in workflow.values()
            if node.get("class_type") == "SaveImage"
        ][0]["filename_prefix"]

        print(f"Looking for files with prefix: {file_prefix}")

        # returns the image as bytes
        for f in Path(output_dir).iterdir():
            if f.name.startswith(file_prefix):
                print(f"Found matching file: {f.name}")
                return f.read_bytes()
        
        print(f"No files found with prefix {file_prefix}")
        raise FileNotFoundError(f"No output file found with prefix {file_prefix}")

    @modal.fastapi_endpoint(method="POST")
    def api(self, item: Dict):
        from fastapi import Response

        # Use the provided workflow
        workflow_data = item
        print(f"Received workflow with {len(workflow_data)} nodes")
        
        # Show all node IDs and their class types
        print("Workflow nodes:")
        for node_id, node in workflow_data.items():
            class_type = node.get("class_type", "unknown")
            print(f"  Node {node_id}: {class_type}")
        
        # Show all connections
        print("Workflow connections:")
        for node_id, node in workflow_data.items():
            if "inputs" in node:
                for input_name, input_value in node["inputs"].items():
                    if isinstance(input_value, list) and len(input_value) == 2:
                        referenced_node = input_value[0]
                        output_index = input_value[1]
                        print(f"  Node {node_id}.{input_name} -> Node {referenced_node}[{output_index}]")
        
        print(f"Full workflow data: {json.dumps(workflow_data, indent=2)}")

        # give the output image a unique id per client request
        client_id = uuid.uuid4().hex
        print(f"Generated client ID: {client_id}")
        
        # Find the first SaveImage node and update its filename prefix
        save_image_found = False
        for node_id, node in workflow_data.items():
            if node.get("class_type") == "SaveImage":
                workflow_data[node_id]["inputs"]["filename_prefix"] = client_id
                print(f"Updated SaveImage node {node_id} with prefix {client_id}")
                
                # Fix the image input format if it's malformed
                if "images" in node["inputs"]:
                    images_input = node["inputs"]["images"]
                    print(f"Original images input: {images_input}")
                    
                    # Handle different malformed formats
                    if isinstance(images_input, list):
                        if len(images_input) == 1 and isinstance(images_input[0], list):
                            # Case: [["8", 0]] -> ["8", 0]
                            workflow_data[node_id]["inputs"]["images"] = images_input[0]
                            print(f"Fixed nested list format: {workflow_data[node_id]['inputs']['images']}")
                        elif len(images_input) == 2 and all(isinstance(x, (str, int)) for x in images_input):
                            # Case: ["8", 0] - this is already correct
                            print(f"Images input format is already correct: {images_input}")
                        else:
                            # Try to extract the first valid image reference
                            for item in images_input:
                                if isinstance(item, list) and len(item) == 2:
                                    workflow_data[node_id]["inputs"]["images"] = item
                                    print(f"Extracted image reference: {item}")
                                    break
                            else:
                                print(f"Warning: Could not fix images input format: {images_input}")
                    else:
                        print(f"Warning: Unexpected images input type: {type(images_input)}")
                
                save_image_found = True
                break
        
        if not save_image_found:
            print("No SaveImage node found in workflow!")
            return Response(content="No SaveImage node found in workflow", status_code=400)

        # save this updated workflow to a new file
        new_workflow_file = f"/root/{client_id}.json"
        with Path(new_workflow_file).open("w") as f:
            json.dump(workflow_data, f, indent=2)
        print(f"Saved workflow to {new_workflow_file}")

        try:
            # run inference on the currently running container
            img_bytes = self.infer.local(new_workflow_file)
            print(f"Inference completed, got {len(img_bytes)} bytes")
            return Response(img_bytes, media_type="image/jpeg")
        except Exception as e:
            print(f"Error during inference: {str(e)}")
            return Response(content=f"Error during inference: {str(e)}", status_code=500)
        finally:
            # Clean up the temporary workflow file
            try:
                Path(new_workflow_file).unlink()
                print(f"Cleaned up temporary workflow file: {new_workflow_file}")
            except:
                pass

    def _wait_until_ready(self, timeout: int = 60) -> None:
        """Block until GET /system_stats returns HTTP 200 (or give up)."""
        url = f"http://127.0.0.1:{self.port}/system_stats"
        deadline = time.time() + timeout
        backoff = 0.3

        while time.time() < deadline:
            try:
                urllib.request.urlopen(url, timeout=1)
                print("✔︎ ComfyUI is ready")
                return
            except Exception:
                time.sleep(backoff)
                backoff = min(backoff * 1.5, 5)

        # still not ready → kill the worker so Modal retries on next call
        print("✘ ComfyUI never became healthy – stopping container")
        modal.experimental.stop_fetching_inputs()
        raise RuntimeError("ComfyUI health-check failed")

    def _ensure_booted(self):
        if self._server_proc and self._server_proc.poll() is None:
            # server already alive
            return                               

        print("Cold start – launching ComfyUI …")
        self._server_proc = subprocess.Popen(
            ["python", "main.py", "--dont-print-server"],
            cwd="/root/comfy/ComfyUI",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._wait_until_ready()

    def poll_server_health(self) -> Dict:
        #ensure_comfy_ready(self.port)
        import socket
        import urllib

        try:
            # check if the server is up (response should be immediate)
            req = urllib.request.Request(f"http://127.0.0.1:{self.port}/system_stats")
            urllib.request.urlopen(req, timeout=5)
            print("ComfyUI server is healthy")
        except (socket.timeout, urllib.error.URLError) as e:
            # if no response in 5 seconds, stop the container
            print(f"Server health check failed: {str(e)}")
            modal.experimental.stop_fetching_inputs()
            raise Exception("ComfyUI server is not healthy, stopping container")

