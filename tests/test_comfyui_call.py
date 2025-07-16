import json
from pathlib import Path
import sys
from PIL import Image
import io
import logging
from datetime import datetime
import time
import modal

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Use Cls.from_name to reference the deployed class from another app
comfy_cls = modal.Cls.from_name("imagegen-comfyui", "ComfyUI")

def test_comfyui_api():
    # Load the workflow from the JSON file
    #workflow_path = "configs/imgen_NEWEST.json"
    workflow_path = "configs/2025-07-15_mago_v027_API.json"
    

    try:
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)
            logger.info(f"Successfully loaded workflow from {workflow_path}")
            logger.info(f"Workflow contains {len(workflow_data)} nodes")
    except FileNotFoundError:
        logger.error(f"Error: Could not find workflow file at {workflow_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Error: Invalid JSON in workflow file {workflow_path}")
        sys.exit(1)
    
    # Clean up the workflow data - remove problematic elements
    cleaned_workflow = workflow_data

    comfy_instance = comfy_cls()
    img_bytes = comfy_instance.infer.remote(cleaned_workflow)
    
    if img_bytes is not None:
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"outputs/output_{timestamp}.jpg"
        logger.info(f"Will save output to: {output_path}")
        
        # Save the image
        with open(output_path, 'wb') as f:
            f.write(img_bytes)
        logger.info(f"Success! Output saved to {output_path}")
    else:
        logger.error(f"Error")


if __name__ == "__main__":
    test_comfyui_api() 