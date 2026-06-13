import os
import sys
from pathlib import Path

def get_base_run_dir() -> Path:
    """
    Determines the base execution directory depending on the current environment (IDE or compiled .exe).
    
    Args:
        None: The function does not accept any arguments.
        
    Returns:
        Path: An absolute path object pointing to the application's root directory.
        
    Raises:
        None: The function handles environment checks safely.
    """
    # Check if the program is running as a compiled PyInstaller executable
    if hasattr(sys, '_MEIPASS'):
        # Return the directory containing the compiled .exe file
        return Path(sys.executable).parent.resolve()
    # If running from source, return the project root directory (two levels up from this file)
    return Path(__file__).resolve().parent.parent

def get_base_assets_dir() -> Path:
    """
    Determines the correct path to the assets directory based on the execution environment.
    
    Args:
        None: The function does not accept any arguments.
        
    Returns:
        Path: An absolute path object pointing to the assets directory.
        
    Raises:
        None: The function handles environment checks safely.
    """
    # Check if the program is compiled via PyInstaller
    if hasattr(sys, '_MEIPASS'):
        # Return the temporary _MEIPASS directory where PyInstaller unpacks internal assets
        return Path(getattr(sys, '_MEIPASS')) / "assets"
    # If running from source, append the "assets" folder to the base run directory
    return get_base_run_dir() / "assets"

# Initialize a constant for the base execution directory path
BASE_RUN_DIR: Path = get_base_run_dir()
# Initialize a constant for the base assets directory path
BASE_ASSETS_DIR: Path = get_base_assets_dir()
# Define the absolute path where all Geometry Dash instances will be stored
INSTANCES_DIR: Path = BASE_RUN_DIR / "instances"

# Define the standard width for UI icons in pixels
ICON_WIDTH: int = 48
# Define the standard height for UI icons in pixels
ICON_HEIGHT: int = 48
# Define the maximum number of instance columns allowed in the main grid
MAX_COLUMNS: int = 6

# Create a strict path object for the default Geometry Dash instance icon
GD_ICON_DEFAULT: Path = BASE_ASSETS_DIR / "gd_icon.png"
# Create a strict path object for the default Geode modloader icon
GEODE_ICON_DEFAULT: Path = BASE_ASSETS_DIR / "geode_icon.png"
# Create a strict path object for the main launcher window icon
MAIN_ICON: Path = BASE_ASSETS_DIR / "GDI.ico"

# Define the absolute URL for fetching the JSON manifest of available game versions
GITHUB_MANIFEST_URL: str = "https://raw.githubusercontent.com/BlueAxolotLArseniy/GDI-Launcher/refs/heads/main/versions.json"