# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Core Modal Commands
- **Deploy main app**: `modal deploy main.py`
- **Run main app locally**: `modal run main.py`
- **Run volume population**: `modal run populate_volume.py`

### Testing Commands
- **Quick local symlink test**: `python tests/simple_local_test.py`
- **Modal volume test**: `modal run tests/test_with_real_volume.py`
- **Local environment test**: `python tests/test_local_setup.py`
- **ComfyUI API test**: `modal run tests/test_comfyui_api.py`
- **Modal webhook test**: `modal run tests/test_modal_webhook.py`

### Debugging Commands
- **Check volume contents**: `modal run tests/check_volume.py`
- **Verify symlinks**: `modal run tests/check_symlinks.py`

## Architecture Overview

### Core Components

1. **main.py**: The primary Modal app that runs ComfyUI with custom nodes and model management
   - Creates Modal image with ComfyUI and dependencies
   - Manages model symlinks at runtime
   - Provides FastAPI endpoints for inference and health checks
   - Handles ComfyUI server lifecycle

2. **populate_volume.py**: Downloads models from CivitAI to Modal volume
   - Uses Civit API tokens for model downloads
   - Maps model types to ComfyUI directory structure
   - Requires `civit-key` Modal secret

3. **Volume Management**: Uses Modal Volume "comfy-cache" for persistent model storage
   - Models are downloaded once and cached
   - Symlinks created at container startup for ComfyUI access

### Model Organization

The app uses a specific model type mapping in `COMFY_PATHS`:
- **checkpoint**: `/root/comfy/ComfyUI/models/checkpoints`
- **lora**: `/root/comfy/ComfyUI/models/loras` 
- **upscaler**: `/root/comfy/ComfyUI/models/upscale_models`
- **segm**: `/root/comfy/ComfyUI/custom_nodes/ComfyUI-Impact-Pack/models/segm`
- **bbox**: `/root/comfy/ComfyUI/custom_nodes/ComfyUI-Impact-Pack/models/bbox`
- **sam**: `/root/comfy/ComfyUI/custom_nodes/ComfyUI-Impact-Pack/models/sam`

### ComfyUI Setup

The Modal image includes these custom nodes:
- WAS Node Suite (was-node-suite-comfyui@1.0.2)
- Image Resize ComfyUI
- ComfyUI Impact Pack (for face detection/segmentation)
- ComfyUI Impact Subpack (for UltralyticsDetectorProvider)

### API Endpoints

The main app exposes:
- `POST /api`: Submit ComfyUI workflows for processing
- `GET /health`: Health check endpoint
- `GET /ui`: Web interface (runs for 60 seconds)

### Local Testing Strategy

The repository includes comprehensive local testing without Modal deployment:
- `simple_local_test.py`: Tests symlink logic with dummy files
- `test_local_setup.py`: Creates complete local ComfyUI simulation
- `test_with_real_volume.py`: Tests with actual Modal volume data

## Key Files

- **main.py**: Main Modal application (671 lines)
- **populate_volume.py**: Model downloader (271 lines) 
- **LOCAL_TESTING_GUIDE.md**: Comprehensive testing documentation
- **tests/**: Local testing utilities (10+ test files)
- **configs/**: ComfyUI workflow configurations

## Model Management

Models are managed through a two-step process:
1. **Population**: Run `populate_volume.py` to download models to volume
2. **Linking**: `create_all_symlinks()` creates symlinks at container startup

The symlink system allows ComfyUI to access cached models without duplication.