import os
import shutil
from pathlib import Path

def get_appdata_path() -> Path:
    """
    Calculates and returns the absolute path to the local Geometry Dash save directory.
    
    Args:
        None: The function does not accept any arguments.
        
    Returns:
        Path: The absolute path pointing to LocalAppData/GeometryDash.
        
    Raises:
        KeyError: Raised if the LOCALAPPDATA environment variable is missing from the system.
    """
    # Fetch the LOCALAPPDATA environment variable from the OS
    local_appdata = os.environ.get('LOCALAPPDATA')
    # If the variable does not exist (highly unlikely on Windows, but safe to check)
    if not local_appdata:
        # Raise a specific KeyError with an explanatory message
        raise KeyError("Environment variable LOCALAPPDATA was not found.")
    # Return the concatenated path pointing to the specific game folder
    return Path(local_appdata) / "GeometryDash"

def copy_directory_contents(src: Path, dst: Path) -> None:
    """
    Safely copies all contents (files and subdirectories) from a source directory to a destination.
    
    Args:
        src (Path): The absolute path object of the source directory.
        dst (Path): The absolute path object of the destination directory.
        
    Returns:
        None: The function does not return any data.
        
    Raises:
        OSError: Raised if the OS denies read/write access during the copy process.
    """
    # Check if the source directory does not exist or is not a valid directory
    if not src.exists() or not src.is_dir():
        # Exit the function early to avoid raising unnecessary errors
        return
        
    # Create the destination directory along with any necessary parent directories
    dst.mkdir(parents=True, exist_ok=True)
    
    # Iterate through every file and folder inside the source directory
    for item in src.iterdir():
        # Construct the absolute path for the current item inside the destination directory
        d_path = dst / item.name
        # Check if the current item is a subdirectory
        if item.is_dir():
            # Check if the destination subdirectory already exists
            if d_path.exists():
                # Recursively delete the existing destination subdirectory to prevent conflicts
                shutil.rmtree(d_path)
            # Recursively copy the entire subdirectory tree to the destination
            shutil.copytree(item, d_path)
        # If the item is a regular file
        else:
            # Copy the file along with its metadata (timestamps, permissions) to the destination
            shutil.copy2(item, d_path)

def clear_directory(target_dir: Path) -> None:
    """
    Completely clears a directory by deleting all of its nested files and subdirectories.
    
    Args:
        target_dir (Path): The absolute path object of the directory to clear.
        
    Returns:
        None: The function does not return any data.
        
    Raises:
        OSError: Raised if the OS denies deletion due to locked files or missing permissions.
    """
    # Check if the target directory does not exist
    if not target_dir.exists():
        # Exit the function early to avoid runtime errors
        return
        
    # Iterate through every item inside the target directory
    for item in target_dir.iterdir():
        # Check if the current item is a subdirectory
        if item.is_dir():
            # Recursively delete the entire subdirectory tree
            shutil.rmtree(item)
        # If the current item is a regular file
        else:
            # Unlink (delete) the file from the filesystem
            item.unlink()