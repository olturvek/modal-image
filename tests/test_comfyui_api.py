import requests
import json
from pathlib import Path
import sys
from PIL import Image
import io
import logging
from datetime import datetime
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_comfyui_api():
    # Load the workflow from the JSON file
    workflow_path = "imgen_NEWEST.json"

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
    
    # Send POST request to the endpoint
    endpoint_url = "https://olturvek--imagegen-comfyui-comfyui-api.modal.run"
    
    try:
        logger.info(f"Sending POST request to {endpoint_url}")
        logger.info(f"Using cleaned workflow with {len(cleaned_workflow)} nodes")
        
        # Use the same simple request configuration as the working test
        response = requests.post(
            endpoint_url,
            json=cleaned_workflow,
            headers={
                'Accept': 'image/*, application/json',
                'Content-Type': 'application/json'
            },
            timeout=600  # Increased timeout for complex workflow
        )
        
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output_{timestamp}.jpg"
            logger.info(f"Will save output to: {output_path}")
            
            # Save the image
            with open(output_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Success! Output saved to {output_path}")
        else:
            logger.error(f"Error: Received status code {response.status_code}")
            logger.error(f"Response headers: {response.headers}")
            logger.error(f"Response content: {response.text}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        import traceback
        logger.error("Full error traceback:")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_comfyui_api() 