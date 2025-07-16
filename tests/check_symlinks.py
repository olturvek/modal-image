import modal

# Connect to your Modal app
app = modal.App("imagegen-comfyui")

# Deploy the app and call the check_symlinks function
if __name__ == "__main__":
    with app.run() as app:
        print("Running check_symlinks...")
        result = app.check_symlinks.remote()
        print(result) 