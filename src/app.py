import sys
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from src.config import MAIN_ICON
from src.ui.main_window import GDIMainWindow

def run_application() -> int:
    """
    Initializes the PySide6 application, configures OS-level settings, and launches the main window.
    
    Args:
        None: The function does not accept any arguments.
        
    Returns:
        int: The exit status code of the application (0 for successful termination).
        
    Raises:
        None: All internal setup exceptions are handled or ignored safely.
    """
    # Check if the application is running on a Windows operating system
    if sys.platform == 'win32':
        # Define a unique Application User Model ID for the GDI Launcher
        my_app_id = 'geometry.dash.instances.launcher.2.0'
        # Force Windows taskbar to group windows based on this specific AppID
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)

    # Initialize the core Qt application instance with command line arguments
    app = QApplication(sys.argv)
    # Apply the cross-platform 'Fusion' style for a modern and consistent look
    app.setStyle('Fusion')
    
    # Verify if the main executable icon exists at the specified path
    if MAIN_ICON.exists():
        # Set the application-wide icon for all windows and dialogs
        app.setWindowIcon(QIcon(str(MAIN_ICON)))
    else:
        # Print an error to the console if the icon file is missing
        print(f'[log][error] ATTENTION: Icon not found at "{MAIN_ICON}"')
    
    # Instantiate the main graphic window for the Geometry Dash launcher
    main_window = GDIMainWindow()
    # Command the Qt event loop to render and display the main window
    main_window.show()
    
    # Start the application's event loop and return its execution result code
    return app.exec()