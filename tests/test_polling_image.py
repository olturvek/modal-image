#!/usr/bin/env python3
"""
Test script for polling-based image generation.
This script tests the complete polling flow with Modal.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from onlyfreaks.image_gen.modal_api import call_comfyui_async_polling
from onlyfreaks.image_gen.utils import load_and_modify_workflow
from onlyfreaks.image_gen.prompt_builder import build_payload
from onlyfreaks.chat_service.utils import get_openrouter_client

def test_polling_image_generation():
    """Test polling-based image generation end-to-end"""
    print("🧪 Testing polling-based image generation...")
    
    try:
        # Get OpenRouter client and build payload
        client = get_openrouter_client()
        chat_turns = "User: Show me a sexy photo of yourself\nYou: I'd love to share a photo with you!"
        
        # Build payload and workflow
        workflow_path = "onlyfreaks/image_gen/workflows/imgen_NEWEST.json"
        payload = build_payload(client, chat_turns)
        workflow = load_and_modify_workflow(workflow_path, payload)
        
        print(f"📝 Chat context: {chat_turns[:50]}...")
        print(f"📝 Using workflow: {workflow_path}")
        
        # Call polling API
        result = call_comfyui_async_polling(
            workflow=workflow,
            user_id="test_user_123",
            session_key="test_user_123:test_persona",
            poll_interval=2,  # Check every 2 seconds
            max_wait_time=120  # Wait up to 2 minutes for testing
        )
        
        print(f"✅ Polling result: {result}")
        
        if result.get("success"):
            image_data = result.get("image")
            if image_data:
                print(f"🎉 Image generation completed successfully!")
                print(f"   Job ID: {result.get('job_id', 'N/A')}")
                print(f"   Image size: {len(image_data)} bytes")
                print(f"   Time taken: {result.get('elapsed_time', 0):.2f} seconds")
                
                # Save test image
                with open("test_polling_image.jpg", "wb") as f:
                    f.write(image_data)
                print("   Test image saved as: test_polling_image.jpg")
            else:
                print("❌ No image data in result")
        else:
            print("❌ Polling image generation failed")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🤖 Testing Polling-Based Image Generation")
    print("=" * 50)
    
    try:
        test_polling_image_generation()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}") 