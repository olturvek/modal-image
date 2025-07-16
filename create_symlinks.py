import modal
from main import app, create_runtime_symlinks

if __name__ == "__main__":
    with app.run() as app:
        print("Creating symlinks...")
        # Run the symlink creation function
        create_runtime_symlinks.remote()
        print("Symlinks created successfully!") 