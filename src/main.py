import sys
from pathlib import Path

# Resolve the absolute path of the current file being executed
current_file_path = Path(__file__).resolve()
# Navigate two levels up in the directory tree to reach the project root
root_directory = current_file_path.parent.parent
# Insert the project root path at the very beginning of the system path list
# This ensures that absolute imports starting with 'src.' work correctly from anywhere
sys.path.insert(0, str(root_directory))

# Import the core application runner function from the newly created app module
from src.app import run_application

# Check if this script is being run directly by the Python interpreter
if __name__ == "__main__":
    # Execute the application runner and pass its return code to sys.exit()
    # This ensures the OS receives the correct exit code when the app closes
    sys.exit(run_application())