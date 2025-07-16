#!/usr/bin/env python3
"""
Test script for Modal webhook functionality.
This script tests the new webhook endpoint in your Modal app.
"""

import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from onlyfreaks.image_gen.utils import load_and_modify_workflow
from onlyfreaks.image_gen.prompt_builder import build_payload
from onlyfreaks.chat_service.utils import get_openrouter_client

def test_modal_webhook():
    """Test the Modal webhook endpoint directly"""
    print("🧪 Testing Modal webhook endpoint...")
    
    try:
        import requests
        
        # Get OpenRouter client and build payload
        client = get_openrouter_client()
        chat_turns = "User: Show me a sexy photo of yourself\nYou: I'd love to share a photo with you!"
        
        # Build payload and workflow
        workflow_path = "onlyfreaks/image_gen/workflows/imgen_NEWEST.json"
        payload = build_payload(client, chat_turns)
        workflow = load_and_modify_workflow(workflow_path, payload)
        
        # Modal webhook endpoint
        modal_endpoint = "https://olturvek--imagegen-comfyui-comfyui-api.modal.run/webhook"
        
        # Your webhook URL (replace with actual URL)
        webhook_url = "https://your-app.onrender.com/webhook/image"
        
        # Prepare webhook request
        webhook_request = {
            "workflow": workflow,
            "webhook_url": webhook_url,
            "user_id": "test_user_123",
            "session_key": "test_user_123:test_persona",
            "callback_data": {
                "test": True,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        print(f"📝 Sending request to: {modal_endpoint}")
        print(f"📝 Webhook URL: {webhook_url}")
        print(f"📝 User ID: {webhook_request['user_id']}")
        
        # Send request to Modal
        response = requests.post(
            modal_endpoint,
            json=webhook_request,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"✅ Response Status: {response.status_code}")
        print(f"✅ Response Headers: {dict(response.headers)}")
        
        if response.status_code == 202:
            response_data = response.json()
            print(f"🎉 Webhook request accepted!")
            print(f"   Request ID: {response_data.get('request_id', 'N/A')}")
            print(f"   Message: {response_data.get('message', 'N/A')}")
            print("   Modal will process the image and call your webhook when ready.")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🤖 Testing Modal Webhook Functionality")
    print("=" * 50)
    
    try:
        test_modal_webhook()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}") 