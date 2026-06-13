from pathlib import Path
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap, QMouseEvent, QCursor
from PySide6.QtCore import Qt, Signal

from src.config import ICON_WIDTH, ICON_HEIGHT, GD_ICON_DEFAULT, GEODE_ICON_DEFAULT, INSTANCES_DIR

class InstanceCard(QFrame):
    """
    A custom QFrame widget functioning as an interactive instance tile.
    Implements the Observer pattern via signals to maintain loose coupling with the parent window.
    """
    # Define a Qt Signal that emits a reference to its own object instance upon being clicked
    clicked_signal = Signal(object)

    def __init__(self, instance_name: str) -> None:
        """
        Initializes the instance card widget with specific sizing and stylistic properties.
        
        Args:
            instance_name (str): The explicit string name of the bound instance folder.
            
        Returns:
            None: Instantiates internal Qt properties.
            
        Raises:
            None: Setup logic is purely functional.
        """
        # Initialize the base QFrame widget class from PySide6
        super().__init__()
        # Store the provided instance folder name for later referencing
        self.instance_name = instance_name
        # Initialize an internal boolean dictating if the tile is currently highlighted
        self.is_selected = False
        
        # Apply a transparent background and remove all borders using a CSS-like Qt stylesheet
        self.setStyleSheet("background: transparent; border: none;")
        # Lock the absolute dimensions of the widget to enforce the grid layout structure
        self.setFixedSize(110, 95)
        # Modify the mouse cursor to a pointing hand when hovering over this specific frame
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Delegate the construction of internal layouts and labels to a separate method
        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Private method to assemble and configure the visual children within the frame.
        
        Args:
            None: Accesses internal attributes.
            
        Returns:
            None: Executes rendering logic only.
            
        Raises:
            None: All QObjects are safely allocated.
        """
        # Create a vertical box layout to stack the icon above the text
        card_layout = QVBoxLayout(self)
        # Shrink the internal margins of the layout to maximize clickable real estate
        card_layout.setContentsMargins(4, 4, 4, 4)
        # Define a consistent 6-pixel gap between the icon image and the text label
        card_layout.setSpacing(6)
        # Ensure all items added to the layout are aligned directly to the center
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Instantiate a text label which will function as the container for the icon pixmap
        self.lbl_gd_icon = QLabel()
        # Lock the label dimensions to perfectly match the target icon constants
        self.lbl_gd_icon.setFixedSize(ICON_WIDTH, ICON_HEIGHT)
        # Center any content rendered within this specific label boundary
        self.lbl_gd_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Resolve the absolute path targeting this specific instance's root folder
        instance_path: Path = INSTANCES_DIR / self.instance_name
        # Evaluate boolean truth if either a 'geode' folder or a 'Geode.dll' file exists within
        has_geode = (instance_path / "geode").exists() or (instance_path / "Geode.dll").exists()
        
        # Determine the target icon path using a conditional ternary operator based on Geode status
        chosen_icon = GEODE_ICON_DEFAULT if has_geode else GD_ICON_DEFAULT
        
        # Verify if the chosen icon file actually exists on the disk
        if chosen_icon.exists():
            # Load the image into memory, scale it smoothly, and maintain its aspect ratio
            pix = QPixmap(str(chosen_icon)).scaled(
                ICON_WIDTH, ICON_HEIGHT, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            # Assign the scaled image matrix directly into the label container
            self.lbl_gd_icon.setPixmap(pix)
        # If the image file is mysteriously missing from the assets folder
        else:
            # Fallback to textual representations of the icon format
            text_label = "GEODE" if has_geode else "GD"
            # Choose a purple hex color for Geode mods, otherwise a standard green
            color = "#a855f7" if has_geode else "#4CAF50" 
            # Override the pixmap with raw fallback text
            self.lbl_gd_icon.setText(text_label)
            # Inject a dynamic stylesheet simulating a dashed border icon placeholder
            self.lbl_gd_icon.setStyleSheet(
                f"color: {color}; font-weight: bold; border: 1px dashed {color}; border-radius: 4px;"
            )

        # Inject the fully configured icon label into the top of the vertical layout stack
        card_layout.addWidget(self.lbl_gd_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        # Create the lower text label populated by the raw string instance name
        self.lbl_name = QLabel(self.instance_name)
        # Center the text internally within the label
        self.lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Enable text wrapping to prevent long names from destroying layout boundaries
        self.lbl_name.setWordWrap(True) 
        # Invoke the state setter to apply the default inactive CSS styling
        self.set_selected_state(False)
        # Inject the configured text label directly below the icon in the vertical stack
        card_layout.addWidget(self.lbl_name, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_selected_state(self, selected: bool) -> None:
        """
        Dynamically adjusts the CSS styling of the instance label based on selection state.
        
        Args:
            selected (bool): True if the card should appear active, False if inactive.
            
        Returns:
            None: Function purely manipulates the QLabel stylesheet.
            
        Raises:
            None: Simple string assignment.
        """
        # Store the passed parameter into the object's internal state tracker
        self.is_selected = selected
        # If the parameter dictates the card is now actively selected
        if self.is_selected:
            # Apply a dark grey background pill-shape around the white text for visual feedback
            self.lbl_name.setStyleSheet("QLabel { color: white; background-color: #4a4a4a; border-radius: 3px; padding: 2px 6px; font-size: 12px; }")
        # If the card is being deselected
        else:
            # Remove the background pill but maintain structural padding to prevent jittering
            self.lbl_name.setStyleSheet("QLabel { color: white; background-color: transparent; border-radius: 3px; padding: 2px 6px; font-size: 12px; }")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Overrides the low-level Qt mouse event listener to intercept left clicks.
        
        Args:
            event (QMouseEvent): The complex object holding coordinate and button data of the click.
            
        Returns:
            None: Dispatches signals.
            
        Raises:
            None: Safe event handling routine.
        """
        # Verify strictly that the user clicked using the primary Left mouse button
        if event.button() == Qt.MouseButton.LeftButton:
            # Trigger the custom Qt Signal, passing the entire instance of this card object
            self.clicked_signal.emit(self)
        # Pass the unhandled event back up the inheritance chain to prevent breaking default behaviors
        super().mousePressEvent(event)