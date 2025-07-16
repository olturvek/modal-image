# ComfyUI Web Interface

This is a simple web interface for ComfyUI running on Modal.

## Quick Start

1. **Deploy the web interface:**
   ```bash
   python run_web_ui.py
   ```

2. **Access the interface:**
   - Modal will provide a URL when the deployment is complete
   - Open that URL in your web browser
   - The ComfyUI interface will be available for 60 seconds

## Features

- **Full ComfyUI Interface**: Complete web-based interface for creating and running workflows
- **Model Caching**: Uses the same cached models as your main application
- **Custom Nodes**: Includes all the custom nodes from your main setup:
  - TBox pack
  - WAS Node Suite
  - ComfyUI Manager
  - Impact Pack
  - ComfyUI Tweaks
- **GPU Acceleration**: Runs on A10G GPU for fast inference

## Configuration

### GPU Selection
The web interface uses an A10G GPU by default. You can change this in `web_ui.py`:

```python
@app.function(
    max_containers=1,
    gpu="A10G",  # Change to "L40S", "H100", etc.
    volumes={"/cache": vol},
)
```

### Port Configuration
The interface runs on port 8000 by default. You can change this in the `@modal.web_server()` decorator:

```python
@modal.web_server(8000, startup_timeout=60)  # Change port number here
```

### Session Duration
The interface stays active for 60 seconds after startup. You can modify this by changing the `startup_timeout` parameter.

## Usage Tips

1. **Workflow Creation**: Use the drag-and-drop interface to create workflows
2. **Model Selection**: Your cached models will be available in the interface
3. **Custom Nodes**: All your installed custom nodes will be available
4. **Saving Workflows**: You can save and load workflows through the interface

## Troubleshooting

- **Interface not loading**: Check that the Modal deployment completed successfully
- **Models not found**: Ensure your volume cache is properly set up
- **Custom nodes missing**: Verify that the custom nodes were installed during image build

## Integration with Main App

This web interface uses the same image and volume as your main `main.py` application, so:
- All models are shared between both applications
- Custom nodes are available in both
- Workflows created in the web interface can be used with the API

## Cost Considerations

- The web interface runs on Modal's GPU instances
- Costs are based on the GPU type and runtime duration
- The interface automatically scales down when not in use 