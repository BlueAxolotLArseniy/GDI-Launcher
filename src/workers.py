import json
import urllib.request
import zipfile
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List

from PySide6.QtCore import QThread, Signal

from src.core import get_appdata_path, copy_directory_contents, clear_directory
from src.config import INSTANCES_DIR, GITHUB_MANIFEST_URL

class FetchManifestWorker(QThread):
    """
    An asynchronous background worker dedicated to downloading the JSON version manifest from GitHub.
    """
    # Define a Qt Signal that emits a boolean (success), a list (data), and a string (status message)
    finished_signal = Signal(bool, list, str)

    def run(self) -> None:
        """
        Executes the thread logic to download and parse the remote JSON manifest.
        
        Args:
            None: This method relies solely on global constants.
            
        Returns:
            None: Results are emitted exclusively via Qt Signals.
            
        Raises:
            None: Exceptions are caught internally and emitted as string messages.
        """
        # Start a generic try-except block to handle network or parsing errors safely
        try:
            # Create an HTTP request object with a custom User-Agent to avoid generic blocking
            req = urllib.request.Request(GITHUB_MANIFEST_URL, headers={'User-Agent': 'GDI-Launcher'})
            # Open a synchronous connection to the URL with a strict 5-second timeout
            with urllib.request.urlopen(req, timeout=5) as response:
                # Read the raw byte response and decode it into a standard UTF-8 string
                raw_data = response.read().decode('utf-8')
                # Parse the UTF-8 string into a Python dictionary
                data = json.loads(raw_data)
                # Extract the 'versions' list from the dictionary, defaulting to an empty list if missing
                versions = data.get("versions", [])
                # Emit a successful signal containing the parsed versions data
                self.finished_signal.emit(True, versions, "Success")
        # Catch any exception (e.g., TimeoutError, URLError, JSONDecodeError)
        except Exception as e:
            # Create a fallback dictionary mimicking the expected structure for offline mode
            fallback = [{
                "id": "offline_fallback",
                "display_name": "No internet connection",
                "game_url": "",
                "geode": {"supported": False, "url": None}
            }]
            # Emit a failure signal containing the offline fallback data and the error message
            self.finished_signal.emit(False, fallback, str(e))

class DownloadExtractWorker(QThread):
    """
    An asynchronous worker handling the downloading and extraction of game and Geode zip files.
    """
    # Define a Qt Signal that emits text updates for the UI status label
    status_changed = Signal(str)
    # Define a Qt Signal that emits an integer representing the current progress percentage
    progress_changed = Signal(int)
    # Define a Qt Signal that emits the final installation status (success boolean and message)
    installation_finished = Signal(bool, str)

    def __init__(self, version_info: Dict[str, Any], target_dir: Path, install_geode: bool) -> None:
        """
        Initializes the installation thread with the required instance configurations.
        
        Args:
            version_info (Dict[str, Any]): Dictionary containing download URLs.
            target_dir (Path): The absolute path where the instance will be installed.
            install_geode (bool): Flag dictating whether the Geode modloader should be installed.
            
        Returns:
            None: The constructor initializes class attributes.
            
        Raises:
            None: No logic is executed that could raise an exception.
        """
        # Call the parent QThread constructor to initialize the threading backend
        super().__init__()
        # Store the dictionary containing the version details and download URLs
        self.version_info = version_info
        # Store the absolute path where the game files should be extracted
        self.target_dir = target_dir
        # Store the boolean flag indicating if Geode integration is requested
        self.install_geode = install_geode
        # Initialize an internal boolean flag to allow safe cancellation of the thread
        self._is_cancelled = False

    def cancel(self) -> None:
        """
        Safely signals the running loop to abort its current operation.
        
        Args:
            None: The function relies on object state.
            
        Returns:
            None: The function only modifies an internal attribute.
            
        Raises:
            None: It performs a simple boolean assignment.
        """
        # Set the internal cancellation flag to True, which will be checked in processing loops
        self._is_cancelled = True

    def _download_file(self, url: str, dest_path: Path, prefix_msg: str) -> bool:
        """
        Downloads a file from a URL in small chunks, allowing for progress tracking and safe cancellation.
        
        Args:
            url (str): The direct download link to the file.
            dest_path (Path): The absolute path where the file will be saved.
            prefix_msg (str): A string prefix used for logging (unused in current iteration).
            
        Returns:
            bool: True if the file downloaded successfully, False if it was cancelled mid-way.
            
        Raises:
            RuntimeError: Raised if a critical network or disk error occurs during download.
        """
        # Start a try-except block to wrap network and IO operations
        try:
            # Create the HTTP request with a custom User-Agent
            req = urllib.request.Request(url, headers={'User-Agent': 'GDI-Launcher'})
            # Open the URL connection and simultaneously open a local file in binary write mode
            with urllib.request.urlopen(req, timeout=10) as response, open(dest_path, 'wb') as out_file:
                # Retrieve the total expected file size from the HTTP headers
                total_size = int(response.headers.get('content-length', 0))
                # Initialize a counter for the total number of bytes downloaded so far
                downloaded = 0
                # Define the chunk size to read from the socket (8 Kilobytes)
                chunk_size = 8192

                # Enter an infinite loop to download the file chunk by chunk
                while True:
                    # Check if the user triggered the cancellation mechanism
                    if self._is_cancelled:
                        # Return False immediately to signal an aborted operation
                        return False

                    # Read a specific chunk of bytes from the network response
                    chunk = response.read(chunk_size)
                    # If the chunk is empty, the download is complete
                    if not chunk:
                        # Break out of the infinite while loop
                        break
                    
                    # Write the received chunk of bytes to the local file
                    out_file.write(chunk)
                    # Increment the total downloaded counter by the length of the new chunk
                    downloaded += len(chunk)

                    # Ensure the total size is greater than zero to avoid division by zero errors
                    if total_size > 0:
                        # Calculate the current progress percentage
                        percent = int((downloaded / total_size) * 100)
                        # Emit the calculated percentage, capping it strictly at 100
                        self.progress_changed.emit(min(percent, 100))
            
            # Return True indicating the entire file was downloaded successfully
            return True
        # Catch any unexpected network or disk write exceptions
        except Exception as e:
            # Wrap the raw exception in a generic RuntimeError and raise it to the run() method
            raise RuntimeError(f"Download error: {e}")

    def run(self) -> None:
        """
        The main execution loop of the thread, orchestrating downloading, extracting, and setup.
        
        Args:
            None: Retrieves data from class attributes.
            
        Returns:
            None: Results are passed out via Qt Signals.
            
        Raises:
            None: Internal exceptions are caught and emitted via installation_finished.
        """
        # Start a generic try-except block to guarantee safe thread closure
        try:
            # Create the target instance directory, ignoring errors if it already exists
            self.target_dir.mkdir(parents=True, exist_ok=True)
            
            # Retrieve the direct download URL for the main game zip file
            game_url = self.version_info.get("game_url")
            # Validate that the URL is not empty or missing
            if not game_url:
                # Raise a strict ValueError if the configuration manifest is broken
                raise ValueError("The manifest does not contain a link to the game.")
                
            # Construct an absolute path for the temporary game zip file
            game_zip = self.target_dir / "game_temp.zip"
            # Emit a UI status update informing the user of the ongoing download
            self.status_changed.emit("Downloading Geometry Dash files...")
            
            # Execute the internal download method, checking if it was cancelled
            if not self._download_file(game_url, game_zip, "Game Download"):
                # Run the cleanup routine to delete partial files upon cancellation
                self._cleanup_temp_files(game_zip)
                # Terminate the thread execution early
                return

            # Emit a UI status update indicating the extraction phase has begun
            self.status_changed.emit("Extracting clean Geometry Dash build...")
            # Reset the UI progress bar back to 0% for the new phase
            self.progress_changed.emit(0)
            
            # Open the downloaded zip file in read-only mode
            with zipfile.ZipFile(game_zip, 'r') as zip_ref:
                # Retrieve the full list of file names contained within the archive
                files = zip_ref.namelist()
                # Store the total count of files to calculate extraction progress
                total_files = len(files)
                # Iterate over the file list along with an integer index
                for idx, file in enumerate(files):
                    # Check if the user triggered the cancellation mechanism during extraction
                    if self._is_cancelled:
                        # Clean up the zip file to avoid leaving garbage behind
                        self._cleanup_temp_files(game_zip)
                        # Terminate the extraction loop and the thread
                        return
                    # Extract the individual file into the target instance directory
                    zip_ref.extract(file, self.target_dir)
                    # Calculate the extraction progress percentage based on the file count
                    percent = int(((idx + 1) / total_files) * 100)
                    # Emit the new progress percentage to update the UI
                    self.progress_changed.emit(percent)
            
            # Delete the temporary game zip file since extraction is complete
            game_zip.unlink(missing_ok=True)

            # Check if Geode installation was requested AND if the current version supports it
            if self.install_geode and self.version_info.get("geode", {}).get("supported", False):
                # Retrieve the download URL for the specific Geode build
                geode_url = self.version_info["geode"]["url"]
                # Construct an absolute path for the temporary Geode zip file
                geode_zip = self.target_dir / "geode_temp.zip"
                
                # Emit a status update for the UI informing about Geode downloading
                self.status_changed.emit("Downloading compatible version of Geode...")
                # Reset the progress bar for the Geode download phase
                self.progress_changed.emit(0)
                
                # Execute the download method for Geode, checking for cancellation
                if not self._download_file(geode_url, geode_zip, "Geode Download"):
                    # Delete the partial Geode archive if the user clicked cancel
                    self._cleanup_temp_files(geode_zip)
                    # Terminate the thread execution early
                    return
                
                # Emit a status update indicating the start of Geode injection
                self.status_changed.emit("Injecting Geode framework...")
                # Reset the progress bar for the extraction phase
                self.progress_changed.emit(0)
                
                # Open the downloaded Geode zip archive in read-only mode
                with zipfile.ZipFile(geode_zip, 'r') as zip_ref:
                    # Retrieve the list of internal files from the Geode archive
                    files = zip_ref.namelist()
                    # Store the total number of items to measure progress
                    total_files = len(files)
                    # Iterate through each file within the archive alongside its index
                    for idx, file in enumerate(files):
                        # Verify that the cancellation flag is still False
                        if self._is_cancelled:
                            # Run the cleanup logic for the Geode zip
                            self._cleanup_temp_files(geode_zip)
                            # Abort the process immediately
                            return
                        # Extract the Geode component directly into the instance directory
                        zip_ref.extract(file, self.target_dir)
                        # Recalculate the current progress out of 100 percent
                        percent = int(((idx + 1) / total_files) * 100)
                        # Emit the updated percentage to the main GUI thread
                        self.progress_changed.emit(percent)
                            
                # Delete the temporary Geode zip file to save disk space
                geode_zip.unlink(missing_ok=True)

            # Construct the absolute path for the instance's isolated 'saves' folder
            saves_path = self.target_dir / "saves"
            # Create the saves directory on the disk
            saves_path.mkdir(exist_ok=True)
            
            # Construct the path for the required Steam App ID text file
            steam_appid_path = self.target_dir / "steam_appid.txt"
            # Create the file and write the standard Geometry Dash Steam ID (322170) inside it
            steam_appid_path.write_text("322170", encoding="utf-8")

            # Define a list of standard Geometry Dash save file names
            empty_files = ["CCGameManager.dat", "CCLocalLevels.dat", "CCGameManager2.dat", "CCLocalLevels2.dat"]
            # Iterate through the expected save file names
            for file_name in empty_files:
                # Construct the absolute path for the individual save file
                file_path = saves_path / file_name
                # Verify that the file does not already exist
                if not file_path.exists():
                    # Create an empty file in binary write mode to satisfy the game's startup checks
                    file_path.write_bytes(b"")

            # Emit a final success signal conveying the installation is completely finished
            self.installation_finished.emit(True, "Installation completed successfully.")

        # Catch any unexpected errors that bypassed the localized try-except blocks
        except Exception as e:
            # Emit a failure signal alongside the captured error string
            self.installation_finished.emit(False, str(e))

    def _cleanup_temp_files(self, zip_path: Path) -> None:
        """
        Deletes temporary files ensuring no corrupted archives are left behind upon cancellation.
        
        Args:
            zip_path (Path): The absolute path to the target temporary zip file.
            
        Returns:
            None: Emits a final signal upon completion.
            
        Raises:
            None: The unlink method suppresses missing file exceptions.
        """
        # Delete the zip file from the disk, ignoring errors if it's already missing
        zip_path.unlink(missing_ok=True)
        # Emit a failure signal explicitly stating the user cancelled the process
        self.installation_finished.emit(False, "Installation cancelled by the user.")

class DeleteWorker(QThread):
    """
    An asynchronous background worker for safely deleting an instance folder and its contents.
    """
    # Define a signal emitting textual status updates
    status_changed = Signal(str)
    # Define a signal emitting integer progress percentages
    progress_changed = Signal(int)
    # Define a signal conveying the final boolean outcome and a status string
    deletion_finished = Signal(bool, str)

    def __init__(self, target_dir: Path, instance_name: str) -> None:
        """
        Initializes the deletion thread with path and instance data.
        
        Args:
            target_dir (Path): The absolute directory path of the instance to delete.
            instance_name (str): The logical string name of the instance.
            
        Returns:
            None: Initializes the QThread base and class variables.
            
        Raises:
            None: Variable assignment only.
        """
        # Initialize the underlying Qt Thread object
        super().__init__()
        # Store the target path object representing the root of the instance folder
        self.target_dir = target_dir
        # Store the human-readable string name of the instance
        self.instance_name = instance_name

    def run(self) -> None:
        """
        Executes the deletion logic traversing the filesystem asynchronously.
        
        Args:
            None: Logic relies entirely on class properties.
            
        Returns:
            None: Operates through signals.
            
        Raises:
            None: Internal exceptions are caught and passed via signals.
        """
        # Try-except block to wrap potentially volatile OS file deletion operations
        try:
            # Check if the folder we are trying to delete actually exists on disk
            if not self.target_dir.exists():
                # If missing, emit a failure state detailing the absence of the folder
                self.deletion_finished.emit(False, "[-] Folder not found.")
                # Exit the method to prevent further execution
                return

            # Emit a status update stating that file cleanup has begun
            self.status_changed.emit("Cleaning files...")
            # Set the progress bar strictly to 50% as a visual placeholder during IO operations
            self.progress_changed.emit(50)
            
            # Delegate the recursive deletion of all inner contents to the core function
            clear_directory(self.target_dir)
            # Remove the now-empty root instance directory itself
            self.target_dir.rmdir()
            
            # Set the progress bar completely to 100% since all IO is finished
            self.progress_changed.emit(100)
            # Emit a success signal confirming the instance was successfully wiped
            self.deletion_finished.emit(True, f"[+] Instance '{self.instance_name}' successfully deleted.")
        # Catch strict OSError or permission errors triggered by file locks
        except Exception as e:
            # Emit a false signal indicating failure alongside the stringified error data
            self.deletion_finished.emit(False, f"[-] Deletion error: {str(e)}")

class GameRunnerWorker(QThread):
    """
    The main orchestrator thread handling save-state rotation, launching the executable, 
    and waiting for game closure in the background.
    """
    # Signal to transmit terminal-like string logs to the UI
    log_signal = Signal(str)
    # Signal transmitting the active Python subprocess object (to monitor or kill if needed)
    process_started = Signal(object)
    # Signal transmitting a boolean representing if the launch cycle finished safely
    finished_signal = Signal(bool)

    def __init__(self, instance_name: str) -> None:
        """
        Initializes the game runner thread calculating all critical paths.
        
        Args:
            instance_name (str): The targeted instance string identifier.
            
        Returns:
            None: The constructor merely populates internal references.
            
        Raises:
            None: Pathing operations do not throw errors here.
        """
        # Call the parent QThread initialization function
        super().__init__()
        # Store the target instance name
        self.instance_name = instance_name
        # Build the absolute path linking to the root instance directory
        self.target_dir: Path = INSTANCES_DIR / instance_name
        # Build the path to the isolated saves repository inside the instance folder
        self.instance_saves: Path = self.target_dir / "saves"
        # Define the path to the global backup vault for the vanilla local appdata saves
        self.backup_dir: Path = INSTANCES_DIR / "backup_saves"
        # Define the path to the expected Geometry Dash binary executable
        self.exe_path: Path = self.target_dir / "GeometryDash.exe"

    def run(self) -> None:
        """
        Manages the intricate process of backing up, swapping, launching, and restoring save states.
        
        Args:
            None: Method executes based on pre-initialized paths.
            
        Returns:
            None: All outputs are dispatched to the UI via signals.
            
        Raises:
            None: Heavy reliance on try-except ensures the thread never crashes silently.
        """
        # Start a massive try block to manage file IO and process creation
        try:
            # Resolve the live environment variable path for the real LocalAppData/GeometryDash
            appdata_gd = get_appdata_path()
            # Verify that the custom GD executable actually exists inside the instance
            if not self.exe_path.exists():
                # Dispatch an error log to the UI indicating the binary is missing
                self.log_signal.emit(f"[-] Error: {self.exe_path.name} not found!")
                # End the sequence prematurely reporting failure
                self.finished_signal.emit(False)
                # Halt execution
                return

            # Dispatch an informational log stating the save swap process has begun
            self.log_signal.emit(f"--- PREPARING SAVES FOR '{self.instance_name}' ---")
            
            # Step 1: Backup logic - Check if the original appdata save folder is present and not empty
            if appdata_gd.exists() and any(appdata_gd.iterdir()):
                # Critical Safety Check: Ensure a backup doesn't already exist (meaning a previous launch crashed)
                if not (self.backup_dir.exists() and any(self.backup_dir.iterdir())):
                    # If the backup dir exists but is empty, delete it first to avoid copytree errors
                    if self.backup_dir.exists():
                        # Destroy the empty directory
                        shutil.rmtree(self.backup_dir)
                    # Recursively copy the entire appdata save structure into the secure backup directory
                    shutil.copytree(appdata_gd, self.backup_dir)
                    # Dispatch a success log regarding the backup creation
                    self.log_signal.emit("[+] Original saves safely backed up.")
                # If a backup already exists
                else:
                    # Inform the user that the safety mechanism blocked overwriting the backup
                    self.log_signal.emit("[!] Old backup detected. Overwrite protection activated.")
                # Delete the original appdata folder structure entirely to prepare a blank slate
                shutil.rmtree(appdata_gd)

            # Recreate an empty Geometry Dash appdata folder to receive the instance saves
            appdata_gd.mkdir(parents=True, exist_ok=True)

            # Step 2: Instance save transfer - Check if the instance has custom saves to inject
            if self.instance_saves.exists() and any(self.instance_saves.iterdir()):
                # Physically copy all save files from the instance into the real system appdata folder
                copy_directory_contents(self.instance_saves, appdata_gd)
                # Dispatch an update indicating successful save file injection
                self.log_signal.emit(f"[+] Saves for instance '{self.instance_name}' injected.")

            # Step 3: Process Execution
            self.log_signal.emit(f"[+] Launching {self.instance_name}...")
            # Create a detached OS subprocess pointing to the instance's executable, using its own folder as CWD
            process = subprocess.Popen(str(self.exe_path), cwd=str(self.target_dir))
            # Emit the active subprocess object back to the main window for potential management
            self.process_started.emit(process)
            
            # BLOCKING CALL: Suspend this specific background thread until the game window is closed
            process.wait()
            
            # The game process has ended. Log the start of the synchronization phase
            self.log_signal.emit("--- SYNCHRONIZING AFTER EXIT ---")
            
            # Step 4: Extract the modified save files back out of the appdata folder
            self.instance_saves.mkdir(exist_ok=True)
            # Check if the appdata folder survived the game session
            if appdata_gd.exists():
                # Erase the outdated saves inside the instance folder
                clear_directory(self.instance_saves)
                # Copy the fresh saves from appdata directly into the instance folder
                copy_directory_contents(appdata_gd, self.instance_saves)
                # Destroy the appdata folder entirely to prepare for backup restoration
                shutil.rmtree(appdata_gd)
                # Dispatch a success message regarding the save progress
                self.log_signal.emit(f"[+] Progress for '{self.instance_name}' successfully saved.")

            # Step 5: Original Save Restoration
            if self.backup_dir.exists() and any(self.backup_dir.iterdir()):
                # Rebuild an empty appdata directory
                appdata_gd.mkdir(exist_ok=True)
                # Push the backed up files back into their rightful place in appdata
                copy_directory_contents(self.backup_dir, appdata_gd)
                # Completely wipe the backup vault now that restoration is complete
                shutil.rmtree(self.backup_dir)
                # Dispatch a celebratory log confirming system state normalcy
                self.log_signal.emit("[EXCELLENT] Original saves successfully restored!")

            # Broadcast the ultimate success signal concluding the launch routine
            self.finished_signal.emit(True)

        # Catch unexpected permission, IO, or system execution errors
        except Exception as e:
            # Push the literal exception string to the UI logs
            self.log_signal.emit(f"[-] CRITICAL ERROR: {e}")
            # Emit failure to reset UI states
            self.finished_signal.emit(False)