from typing import Tuple, List, Dict, Any, Optional
from pathlib import Path

from PySide6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox, 
                             QCheckBox, QHBoxLayout, QPushButton, QVBoxLayout, 
                             QLabel, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt

from src.workers import DownloadExtractWorker, DeleteWorker, FetchManifestWorker

class AddInstanceDialog(QDialog):
    """
    A pop-up modal responsible for asynchronously loading manifest data 
    and capturing user inputs to configure a new instance download.
    """
    def __init__(self, parent=None) -> None:
        """
        Sets up the dialog UI and immediately spawns a background fetch thread.
        
        Args:
            parent: The optional QWidget serving as the parent window.
            
        Returns:
            None: Generates the internal layout and launches QThread.
            
        Raises:
            None: Operations are wrapped.
        """
        # Initialize the base QDialog class inheriting parent parameters
        super().__init__(parent)
        # Override the window title string while the networking thread is active
        self.setWindowTitle("Loading data...")
        # Lock the width of the dialog box to maintain a clean layout constraint
        self.setFixedWidth(340)
        # Instantiate an empty list placeholder expecting dictionary structures containing version data
        self.versions_data: List[Dict[str, Any]] = []
        
        # Attach a master vertical layout to the dialog to stack sub-widgets
        self.layout = QVBoxLayout(self)
        
        # Create a temporary informational label notifying the user of network operations
        self.lbl_loading = QLabel("Connecting to GitHub repository...")
        # Center the text of the loading notification
        self.lbl_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Push the notification into the vertical layout stack
        self.layout.addWidget(self.lbl_loading)
        
        # Instantiate the custom network worker class designed to fetch the JSON manifest
        self.fetch_worker = FetchManifestWorker()
        # Bind the worker's completion signal directly to the internal _on_manifest_loaded processor method
        self.fetch_worker.finished_signal.connect(self._on_manifest_loaded)
        # Command the QThread to begin execution in a separate CPU core
        self.fetch_worker.start()

    def _on_manifest_loaded(self, success: bool, data: list, message: str) -> None:
        """
        Slot method invoked automatically upon completion of the GitHub fetch sequence.
        
        Args:
            success (bool): Indicates whether the HTTP call and parsing succeeded.
            data (list): A list containing version configuration dictionaries.
            message (str): Log or error message associated with the fetch.
            
        Returns:
            None: Triggers a secondary UI build method.
            
        Raises:
            None: Executes purely synchronous UI manipulation.
        """
        # Ingest the delivered list array into the object's memory scope
        self.versions_data = data
        # Immediately queue the temporary loading label for destruction within the C++ backend
        self.lbl_loading.deleteLater()
        # Rename the window title to reflect readiness
        self.setWindowTitle("Create Instance")
        # Proceed to inject the interactive forms into the UI
        self._build_ui()

    def _build_ui(self) -> None:
        """
        Constructs the interactive data collection form post-fetch.
        
        Args:
            None: Pulls from internal state variables.
            
        Returns:
            None: Modifies internal QDialog layout arrays.
            
        Raises:
            None: Pure UI allocation logic.
        """
        # Instantiate a highly structured form layout for label-input pairing
        form_layout = QFormLayout()
        # Create an empty single-line text input field intended for the instance name
        self.name_input = QLineEdit()
        # Create an empty dropdown menu container intended for game versions
        self.version_combo = QComboBox()
        
        # Iterate over the previously downloaded and parsed list of version dictionaries
        for v in self.versions_data:
            # Push an item to the dropdown using 'display_name' as text, and passing the raw dict object as hidden data
            self.version_combo.addItem(v["display_name"], v)
            
        # Instantiate a toggleable checkbox with a descriptive string for Geode integration
        self.geode_check = QCheckBox("Bind Geode framework")
        
        # Append a new row mapping a literal string label to the text input box
        form_layout.addRow("Name:", self.name_input)
        # Append a new row mapping a literal string label to the dropdown menu
        form_layout.addRow("Version:", self.version_combo)
        # Append the checkbox beneath the previous rows
        form_layout.addRow(self.geode_check)
        
        # Push the assembled structured form into the master layout of the dialog
        self.layout.addLayout(form_layout)
        
        # Instantiate a horizontal box layout intended specifically to organize bottom buttons
        btn_layout = QHBoxLayout()
        # Create the primary confirm button
        btn_ok = QPushButton("OK")
        # Bind the click event of the OK button to the inherited QDialog.accept() exit routine
        btn_ok.clicked.connect(self.accept) 
        # Create the secondary cancellation button
        btn_cancel = QPushButton("Cancel")
        # Bind the click event of the Cancel button to the inherited QDialog.reject() exit routine
        btn_cancel.clicked.connect(self.reject) 
        
        # Push the accept button into the horizontal structure
        btn_layout.addWidget(btn_ok)
        # Push the reject button adjacent to the accept button
        btn_layout.addWidget(btn_cancel)
        # Push the entire horizontal button layout to the absolute bottom of the master layout
        self.layout.addLayout(btn_layout)

        # Wire an event listener to trigger whenever the dropdown selection changes to update Geode limits
        self.version_combo.currentIndexChanged.connect(self.sync_geode_checkbox_state)
        # Trigger the sync function immediately once to configure initial UI constraints
        self.sync_geode_checkbox_state()

    def sync_geode_checkbox_state(self) -> None:
        """
        Evaluates the currently selected version to dynamically enable/disable the Geode checkbox.
        
        Args:
            None: Inspects internal QComboBox state.
            
        Returns:
            None: Alters QCheckBox availability properties.
            
        Raises:
            None: Only runs simple boolean checks.
        """
        # Retrieve the mathematical integer index of the currently highlighted dropdown row
        idx = self.version_combo.currentIndex()
        # Verify the integer index is within a valid bounds structure
        if idx >= 0:
            # Extract the hidden dictionary object embedded within the dropdown item
            version_info = self.version_combo.itemData(idx)
            # Traverse the dictionary safely assessing if geode is flagged as supported
            is_supported = version_info.get("geode", {}).get("supported", False)
            # Toggle the physical state (grayed out or interactive) of the checkbox
            self.geode_check.setEnabled(is_supported)
            # If the current version inherently does not support Geode integration
            if not is_supported:
                # Forcefully uncheck the box to prevent invalid configuration states
                self.geode_check.setChecked(False)

    def get_data(self) -> Tuple[str, dict, bool]:
        """
        A getter method invoking collection of all values across the form's input elements.
        
        Args:
            None: Scrapes internal widget data.
            
        Returns:
            Tuple[str, dict, bool]: The clean name string, raw version dict, and geode toggle state.
            
        Raises:
            None: Ensures safe extraction using index bound checks.
        """
        # Fetch the integer index indicating the current dropdown selection
        idx = self.version_combo.currentIndex()
        # Retrieve the dictionary from the index using ternary logic fallback if invalid
        version_info = self.version_combo.itemData(idx) if idx >= 0 else {}
        # Return a Python Tuple packaging the stripped string, dictionary, and boolean tick state
        return self.name_input.text().strip(), version_info, self.geode_check.isChecked()


class InstallProgressDialog(QDialog):
    """
    A strictly controlled modal window that renders download metrics
    and manages the lifecycle of the download worker thread.
    """
    def __init__(self, version_info: dict, target_dir: Path, install_geode: bool, parent=None) -> None:
        """
        Builds the visual progress monitor and primes background logic.
        
        Args:
            version_info (dict): The dictionary harboring the URLs necessary for fetching.
            target_dir (Path): The strict path referencing the new instance installation sector.
            install_geode (bool): Boolean condition marking Geode modloader necessity.
            parent: The optional parent window maintaining hierarchical flow.
            
        Returns:
            None: Initializes UI and launches worker.
            
        Raises:
            None: Configuration handles itself securely.
        """
        # Standardize initialization with inherited class methods
        super().__init__(parent)
        # Update the top bar string indicating the ongoing installation
        self.setWindowTitle("Installing build...")
        # Restrict window resizing completely by locking absolute dimensions
        self.setFixedSize(420, 110)
        # Apply a bitwise modification removing the standard top right 'X' closing button completely
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        
        # Maintain an internal lock assessing whether the installation thread exited properly
        self.is_finished = False
        # Store the thread initialization variables as an immutable tuple for later consumption
        self.worker_args = (version_info, target_dir, install_geode)
        
        # Instantiate a vertical layout stacking textual context above progress visualization
        layout = QVBoxLayout(self)
        # Define uniform padding margins across the top, left, bottom, and right axis
        layout.setContentsMargins(15, 12, 15, 12)
        # Mandate an 8 pixel spacing buffer between stacked widgets
        layout.setSpacing(8)
        
        # Create a dynamic label describing the granular operational phase
        self.lbl_status = QLabel("Preparing for installation...")
        # Inject raw CSS styling altering color and typography size
        self.lbl_status.setStyleSheet("font-size: 11px; color: #bbbbbb;")
        # Enable multi-line text wrapping specifically to accommodate extremely lengthy file names
        self.lbl_status.setWordWrap(True) 
        # Inject the textual label into the layout stream
        layout.addWidget(self.lbl_status)
        
        # Allocate a memory segment for the visual percentage tracking bar
        self.progress_bar = QProgressBar()
        # Calibrate the mathematical range of the tracking widget explicitly from 0 to 100
        self.progress_bar.setRange(0, 100)
        # Mount the visual tracking bar directly below the textual notification label
        layout.addWidget(self.progress_bar)
        
        # Initialize an inline horizontal layout to specifically flush buttons toward the right edge
        btn_layout = QHBoxLayout()
        # Add an expanding blank space stretching dynamically to push following widgets right
        btn_layout.addStretch()
        # Create the sole interactive widget permitting thread cancellation
        self.btn_cancel = QPushButton("Cancel")
        # Direct the user click event exclusively to the cancellation handler slot
        self.btn_cancel.clicked.connect(self._handle_cancellation)
        # Attach the cancellation button next to the expanding spacer
        btn_layout.addWidget(self.btn_cancel)
        # Finally push the entire lower button block to the absolute bottom of the main layout
        layout.addLayout(btn_layout)
        
        # Call the internal method delegating execution logic to the worker
        self.start_worker()

    def start_worker(self) -> None:
        """
        Unpacks internal configuration tuple and spawns the background QThread execution process.
        
        Args:
            None: Pulls parameters directly from class internals.
            
        Returns:
            None: Instantiates threads and binds PyQt signals.
            
        Raises:
            None: Pure logic flow control.
        """
        # Unpack the stored variables into three discrete local references
        version_info, target_dir, install_geode = self.worker_args
        # Create a new instance of the specialized DownloadExtraction threaded worker
        self.worker = DownloadExtractWorker(version_info, target_dir, install_geode)
        # Wire the textual update emissions directly to the text-changing slot of the Label
        self.worker.status_changed.connect(self.lbl_status.setText)
        # Wire the integer-based progress emissions straight to the internal setter of the progress bar
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        # Bind the conclusive result emission to the custom teardown processing slot
        self.worker.installation_finished.connect(self.on_process_finished)
        # Fire the thread triggering execution in a separate memory space
        self.worker.start()

    def _handle_cancellation(self) -> None:
        """
        Intercepts the cancel button click validating user intent before signaling thread termination.
        
        Args:
            None: Reacts directly to the button logic.
            
        Returns:
            None: Edits UI properties and triggers thread methods.
            
        Raises:
            None: Safe validation checks.
        """
        # Determine whether the download thread is still technically alive
        if not self.is_finished:
            # Produce a blocking dialogue window requesting a definitive boolean choice
            reply = QMessageBox.question(
                self, "Cancel", "Stop installation? Files will be deleted.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                QMessageBox.StandardButton.No
            )
            # Evaluate if the user clicked the affirmative confirmation button
            if reply == QMessageBox.StandardButton.Yes:
                # Hard lock the cancellation button mitigating duplicate click sequences
                self.btn_cancel.setEnabled(False)
                # Alter the current visual status to denote cleanup sequences
                self.lbl_status.setText("Cancelling and cleaning up garbage...")
                # Dispatch the internal soft-kill boolean setter to the active thread
                self.worker.cancel()

    def on_process_finished(self, success: bool, message: str) -> None:
        """
        Consumes the final emit signal from the worker resolving UI state and logging errors.
        
        Args:
            success (bool): A rigid True/False dictating endstate result.
            message (str): Contextual logging details regarding success or failure.
            
        Returns:
            None: Transitions dialog state towards finalization.
            
        Raises:
            None: Triggers parent acceptance routines.
        """
        # Set the lock state denoting completion logic triggered properly
        self.is_finished = True
        # Evaluate if the boolean result indicates flawless execution
        if success:
            # Forcefully jam the percentage visualization directly to absolute maximum
            self.progress_bar.setValue(100)
            # Overwrite the textual label solidifying success feedback
            self.lbl_status.setText("Done!")
            # Triggers QDialog's intrinsic method validating completion and closing the window
            self.accept()
        # Execute secondary fallback routine when errors were encountered
        else:
            # Spawns a blocking OS-styled critical error dialogue window with detailed string data
            QMessageBox.critical(self, "Error", message)
            # Demands QDialog's intrinsic failure state causing destructive UI shutdown
            self.reject()


class DeleteProgressDialog(QDialog):
    """
    A lightweight, non-interactive modal designed to exhibit deletion status
    while masking blocking filesystem I/O operations from main execution flows.
    """
    def __init__(self, target_dir: Path, instance_name: str, parent=None) -> None:
        """
        Configures rapid instantiation properties linking layout geometry and worker deployment.
        
        Args:
            target_dir (Path): The designated absolute folder earmarked for erasure.
            instance_name (str): The logical UI name allocated to the targeted build.
            parent: The QWidget context calling this prompt.
            
        Returns:
            None: Bootstraps the visual skeleton and triggers QThread immediately.
            
        Raises:
            None: Follows safe procedural assignment bounds.
        """
        # Standard PySide6 constructor hierarchy inheritance initialization
        super().__init__(parent)
        # Apply the localized dialogue title reflecting destructive context
        self.setWindowTitle("Deleting build...")
        # Bind strict, inflexible horizontal and vertical constraints upon UI
        self.setFixedSize(400, 110)
        
        # Initiate a standard top-to-bottom widget organizational alignment layout
        layout = QVBoxLayout(self)
        # Assemble string concatenating contextual variable data mapping to initial phase
        self.lbl_status = QLabel(f"Preparing to delete '{instance_name}'...")
        # Drop the textual element securely into the vertical structure stream
        layout.addWidget(self.lbl_status)
        
        # Generate the standard progress tracking element widget
        self.progress_bar = QProgressBar()
        # Configure operational bounds ensuring 0-100 logic limits
        self.progress_bar.setRange(0, 100)
        # Place widget beneath prior text label into overarching layout matrix
        layout.addWidget(self.progress_bar)
        
        # Compile instance details initializing targeted worker processing thread object
        self.worker = DeleteWorker(target_dir, instance_name)
        # Connect explicit textual updates from thread towards modifying widget string values
        self.worker.status_changed.connect(self.lbl_status.setText)
        # Connect explicit percentage updates from thread towards driving widget length
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        # Link success completion trigger directly towards initiating inherent acceptance sequence
        self.worker.deletion_finished.connect(self.accept)
        # Force the worker loop initialization sequence immediately spawning detached logic block
        self.worker.start()