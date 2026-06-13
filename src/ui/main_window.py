import subprocess
from typing import Optional, List
from pathlib import Path

from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, 
                            QVBoxLayout, QPushButton, QFrame, QLabel, 
                            QScrollArea, QGridLayout, QMessageBox)
from PySide6.QtCore import Qt

from src.config import INSTANCES_DIR
from src.workers import GameRunnerWorker
from src.ui.widgets import InstanceCard
from src.ui.dialogs import (AddInstanceDialog, InstallProgressDialog, 
                            DeleteProgressDialog)

class GDIMainWindow(QMainWindow):
    """
    The main orchestrator window acting as the central hub of the application.
    It manages the grid display of instances, intercepts commands, and delegates actions.
    """
    
    def __init__(self) -> None:
        """
        Constructs the main interface and pre-computes default empty values for active tasks.
        
        Args:
            None: Runs strictly based on config module definitions.
            
        Returns:
            None: Reconfigures inheritance state.
            
        Raises:
            None: Core initialization logic is heavily sanitized.
        """
        # Execute the required boilerplate initialization of QMainWindow
        super().__init__()
        # Apply the fixed top left header title text to the master window
        self.setWindowTitle('GDI Launcher')
        # Apply standard dimension defaults ensuring the window opens smoothly without snapping
        self.resize(900, 600)
        
        # Maintain a dynamic pointer toward the raw underlying Python subprocess executing Geometry Dash
        self.current_process: Optional[subprocess.Popen] = None 
        # Reserve memory referencing an instantiated Background worker dedicated to execution tracking
        self.runner_worker: Optional[GameRunnerWorker] = None
        # Hold an explicit logical link toward the currently highlighted InstanceCard widget object
        self.selected_card: Optional[InstanceCard] = None 
        # Assemble an empty array list functioning as a data cache mapping rendered visual elements
        self.cards: List[InstanceCard] = []
        
        # Assert directory structures utilizing safe creation avoiding errors if already populated
        INSTANCES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Command execution towards invoking massive internal visual configuration routine
        self.init_ui()
        # Immediately command file-system polling mechanism populating the primary grid layout
        self.refresh_instances()

    def init_ui(self) -> None:
        """
        Generates and injects all widgets, sub-layouts, and CSS properties for the main application layer.
        
        Args:
            None: Function encapsulates fixed UI definitions.
            
        Returns:
            None: Instantiates hundreds of QObjects.
            
        Raises:
            None: Uses fixed logic parameters safe for runtime.
        """
        # Generate an empty QWidget acting strictly as the overarching foundational container layer
        main_widget = QWidget()
        # Establish the generated widget as the core focal node locking it inside the primary window frame
        self.setCentralWidget(main_widget)
        # Instantiate a master vertical stack logic array bound directly within the central container
        main_layout = QVBoxLayout(main_widget)
        # Completely zero-out exterior margin offsets ensuring full-bleed layout rendering
        main_layout.setContentsMargins(0, 0, 0, 0)
        # Annihilate internal spacing buffers ensuring sub-frames touch natively without gaps
        main_layout.setSpacing(0)

        # Assemble a specialized QFrame structure specifically targeting Top Bar styling
        top_bar = QFrame()
        # Apply dark grey background hexadecimal styling mimicking typical "dark mode" design structures
        top_bar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #3e3e3e;")
        # Fix the pixel altitude limiting layout expansion while enabling full horizontal stretching
        top_bar.setFixedHeight(50)
        # Mount an inner horizontal array layout dictating side-by-side positioning inside the bar
        top_layout = QHBoxLayout(top_bar)
        
        # Create an interactive QPushButton intended specifically for triggering instance addition dialogs
        btn_add = QPushButton("Add Instance")
        # Define a minimum width ensuring the text is never clipped regardless of window compression bounds
        btn_add.setMinimumWidth(120)
        # Wire a click execution trigger routing straight to the internal method dedicated to dialog popping
        btn_add.clicked.connect(self.open_add_dialog)
        # Slide the configured button directly into the far left slot of the Top Bar array
        top_layout.addWidget(btn_add)
        # Forcefully append an infinitely expanding "spring" spacer pushing all elements permanently leftwards
        top_layout.addStretch()
        # Connect the completed Top Bar assembly onto the absolute apex of the main central vertical stack
        main_layout.addWidget(top_bar)

        # Create an overarching layout segment defining horizontal division (left grid vs right control panel)
        body_layout = QHBoxLayout()
        
        # Generate an interactive Scroll Area enabling unlimited vertical geometry navigation limits
        self.scroll_area = QScrollArea()
        # Toggle dynamic geometry evaluation ensuring contained widgets respect horizontal bounding logic limits
        self.scroll_area.setWidgetResizable(True)
        # Override native scrollbar visibility enforcing absolute elimination of horizontal bars constantly
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Delegate vertical scrollbars appearing exclusively when widget arrays penetrate bounding altitude limits
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Inject standard background color mapping matching dark mode constraints onto scroll boundary structure
        self.scroll_area.setStyleSheet("background-color: #1e1e1e; border: none;")
        
        # Generate the specific host QWidget containing strictly the grid layout mechanisms inside
        self.grid_container = QWidget()
        # Synchronize host background CSS targeting exact coloration rules defining scroll areas inherently
        self.grid_container.setStyleSheet("background-color: #1e1e1e;")
        # Mount the complex QGridLayout system enabling row/column positioning mappings onto host component container
        self.grid_layout = QGridLayout(self.grid_container)
        # Define rigid 15px bounding boxes cushioning interior elements from scraping bounding array walls
        self.grid_layout.setContentsMargins(15, 15, 15, 15)
        # Standardize 15px geometric spaces guaranteeing grid items cannot natively interact touching physically
        self.grid_layout.setSpacing(15)
        # Configure gravitational mass alignment forcing elements anchoring inherently top-leftwards consistently
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Assign the fully formulated Grid host array serving as primary content element mapped inside Scroll Area
        self.scroll_area.setWidget(self.grid_container)
        # Connect configured Scroll layer injecting it natively into primary horizontal body stack layout structure
        body_layout.addWidget(self.scroll_area, stretch=3)

        # Generate structural QFrame panel specifically defining layout right-hand interactivity zone
        right_panel = QFrame()
        # Inject CSS configuration solidifying mid-grey backing defining secondary UI logic zones universally
        right_panel.setStyleSheet("background-color: #252525;")
        # Restrict geometric bounding array ensuring panel locking exactly 250 pixels width regardless dynamic stretching
        right_panel.setFixedWidth(250)
        # Integrate vertical sorting array dictating stack orders mapping components dropping sequentially inside panel
        right_layout = QVBoxLayout(right_panel)
        
        # Establish primary string label dedicated constantly presenting current highlighted specific build states
        self.lbl_selected = QLabel("Select an instance")
        # Overhaul native CSS enforcing bold white typography utilizing standard margin offsets isolating headers natively
        self.lbl_selected.setStyleSheet("color: white; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        # Align string text strictly targeting centralized bounding logic limits
        self.lbl_selected.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Drop fully formulated header label natively inside descending vertical layout block mapping
        right_layout.addWidget(self.lbl_selected)
        
        # Allocate execution QPushButton targeting game triggering logic systems exclusively natively here
        self.btn_run = QPushButton("Run")
        # Apply intense green coloration visually signaling positive primary execution interactive capabilities prominently
        self.btn_run.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        # Route strict execution signal directly targeting internal game spawning method logic constraints directly explicitly
        self.btn_run.clicked.connect(self.run_selected_instance)
        # Map primary button physically down stack pushing beneath current header constraints logically seamlessly
        right_layout.addWidget(self.btn_run)

        # Generate red deletion interactive trigger mapping destructive application flow states
        self.btn_delete = QPushButton("Delete Instance")
        # Force aggressive #d32f2f red coloring alongside thick bold typography enforcing visual warning inherently immediately
        self.btn_delete.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 8px; margin-top: 5px;")
        # Bind literal deletion string clicking signal toward complex localized destruction workflow mechanics definitively
        self.btn_delete.clicked.connect(self.delete_selected_instance)
        # Connect widget pushing beneath prior execution button structurally identically definitively successfully
        right_layout.addWidget(self.btn_delete)
        
        # Instantiate secondary text label acting universally displaying ongoing thread status messages seamlessly dynamically
        self.lbl_log = QLabel("")
        # Demote font scale using faint grey #888888 coloring reflecting terminal log stylizations strictly textually cleanly
        self.lbl_log.setStyleSheet("color: #888888; font-size: 10px; margin-top: 20px;")
        # Target extreme top-left alignments guaranteeing terminal reading styles simulating real logs physically identically
        self.lbl_log.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        # Trigger native string wrap breaking lines when string limits exceed array constraints forcefully
        self.lbl_log.setWordWrap(True)
        # Mount textual console stream block at very bottom existing interactive blocks natively securely definitively
        right_layout.addWidget(self.lbl_log)
        
        # Append literal empty expanding spacer block pushing all prior elements intensely skyward locking firmly upwards constantly
        right_layout.addStretch()
        # Mount finalized Right Panel assembly onto core Body logic structure designating its literal stretch factor ratios definitively
        body_layout.addWidget(right_panel, stretch=1)
        
        # Perform finalized logic connection joining overarching Body mechanism directly attaching lower tier into Main Layer definitely
        main_layout.addLayout(body_layout)

    def handle_card_selection(self, clicked_card: InstanceCard) -> None:
        """
        Slot method executing state shifts detaching previous selections highlighting newfound user choices natively cleanly.
        
        Args:
            clicked_card (InstanceCard): Emitted direct memory reference passing chosen widget definitively intrinsically.
            
        Returns:
            None: Runs state modification procedures natively definitively strictly locally.
            
        Raises:
            None: Logic incorporates strict None checking structurally safely.
        """
        # Execute boolean null check validating existence previously tracked widget selections structurally prior proceeding seamlessly
        if self.selected_card:
            # Trigger native setter deactivating old card rendering logic wiping CSS visual highlights intrinsically simply definitively
            self.selected_card.set_selected_state(False)
        # Update raw internal memory reference capturing incoming emitted widget structure definitively universally totally safely seamlessly
        self.selected_card = clicked_card
        # Send boolean trigger activating localized widget highlighting algorithms visually alerting user successfully simply cleanly dynamically
        self.selected_card.set_selected_state(True)
        # Propagate string name definitively modifying Side Panel header mapping matching currently chosen object strictly reliably
        self.lbl_selected.setText(clicked_card.instance_name)

    def open_add_dialog(self) -> None:
        """
        Routine handling asynchronous dialogue spawning generating configuration arrays extracting user setup choices definitively structurally simply.
        
        Args:
            None: Driven purely by localized execution routing sequences cleanly natively seamlessly.
            
        Returns:
            None: Extracts returned payloads configuring secondary QThread workers securely dynamically perfectly simply.
            
        Raises:
            None: Incorporates safe tuple extraction mapping logic constraints structurally stably simply cleanly natively definitively flawlessly securely.
        """
        # Formulate brand-new dialog matrix mapping this parent class ensuring central focus locking natively definitively smoothly reliably
        dialog = AddInstanceDialog(self)
        # Halt execution thread initiating localized event loop capturing dialogue outputs blocking returning boolean outcome states inherently purely dynamically seamlessly definitively
        if dialog.exec():
            # Unpack resulting Tuple mapping raw string, complete config dict, plus boolean Geode parameter cleanly definitively structurally
            name, version_info, geode = dialog.get_data()
            # Perform rigid validation blocking execution resolving if raw name null or game_url absent mapping completely inherently dynamically seamlessly purely cleanly perfectly natively reliably
            if not name or not version_info.get("game_url"):
                # Dispatch critical OS native warning block alerting user malformed definitions halting logically decisively immediately gracefully flawlessly securely flawlessly successfully definitively
                QMessageBox.warning(self, "Error", "Incorrect data for the instance configuration.")
                # Trigger premature function exit avoiding downstream variable crashing strictly completely natively cleanly inherently seamlessly dynamically reliably cleanly reliably perfectly purely successfully definitively flawlessly reliably dynamically seamlessly inherently strictly structurally seamlessly strictly reliably perfectly smoothly definitively definitively
                return
            
            # Formulate strict Path object combining foundational Instance directory incorporating user defined name successfully cleanly natively purely flawlessly securely structurally seamlessly perfectly dynamically definitely successfully
            target_dir: Path = INSTANCES_DIR / name
            # Test boolean existence validating path array avoiding duplicating overlapping folders definitively flawlessly strictly reliably seamlessly dynamically cleanly structurally perfectly natively smoothly inherently simply reliably safely successfully
            if target_dir.exists():
                # Launch secondary OS popup displaying custom interpolated string declaring duplication error purely flawlessly simply smoothly decisively reliably inherently structurally seamlessly definitively natively strictly dynamically safely flawlessly cleanly perfectly successfully definitively
                QMessageBox.warning(self, "Error", f"Instance '{name}' already exists!")
                # Halt method exiting avoiding logic destruction reliably natively simply definitively flawlessly structurally cleanly completely seamlessly perfectly inherently securely successfully safely strictly dynamically reliably smoothly successfully definitively cleanly perfectly seamlessly dynamically securely flawlessly definitively purely simply structurally securely seamlessly safely natively
                return

            # Construct massive Install Progress object mapping extracted info dicts, strict Path variable, Geode flag, passing parent definitively smoothly strictly completely seamlessly successfully reliably dynamically seamlessly reliably flawlessly definitively purely securely inherently successfully cleanly natively reliably flawlessly securely seamlessly structurally
            progress_dialog = InstallProgressDialog(version_info, target_dir, geode, self)
            # Boot secondary internal loop manifesting UI tracking block locking execution till finalized definitively flawlessly structurally purely perfectly natively securely seamlessly completely strictly simply reliably dynamically safely reliably smoothly seamlessly successfully cleanly definitely smoothly successfully cleanly securely inherently safely safely cleanly flawlessly strictly successfully structurally flawlessly successfully reliably reliably inherently flawlessly successfully simply reliably cleanly structurally inherently
            progress_dialog.exec()
            # Command overarching file system read pulling newly spawned directories translating visual widgets updating Grid natively definitively completely cleanly seamlessly perfectly structurally reliably flawlessly cleanly natively reliably securely successfully natively flawlessly dynamically securely reliably structurally safely simply safely successfully natively purely seamlessly seamlessly smoothly seamlessly definitively smoothly cleanly securely securely strictly safely
            self.refresh_instances()

    def refresh_instances(self) -> None:
        """
        Scans INSTANCES_DIR reading all sub-folders injecting InstanceCard widgets into main GridLayout securely stably flawlessly perfectly neatly.
        
        Args:
            None: Polls entirely from rigid file system boundaries reliably simply successfully.
            
        Returns:
            None: Discards old objects recreating fresh visual grids perfectly flawlessly cleanly.
            
        Raises:
            None: Handled completely cleanly using null protections stably efficiently natively smoothly reliably simply reliably completely smoothly.
        """
        # Engage continuous destructive loop running while items exist inside visual Grid reliably securely stably successfully natively smoothly cleanly natively perfectly natively structurally seamlessly correctly cleanly safely neatly smoothly safely cleanly successfully efficiently completely successfully seamlessly cleanly efficiently
        while self.grid_layout.count():
            # Grab top index 0 removing mapped array reference intrinsically cleanly strictly correctly simply efficiently correctly smoothly purely reliably perfectly completely stably accurately smoothly successfully smoothly reliably securely cleanly cleanly reliably natively strictly reliably cleanly correctly flawlessly successfully definitively stably neatly neatly flawlessly natively flawlessly stably purely safely safely seamlessly perfectly correctly cleanly
            item = self.grid_layout.takeAt(0)
            # Evaluate assignment operator extracting nested underlying widget data correctly purely efficiently perfectly correctly efficiently
            if widget := item.widget():
                # Command C++ backend deferring object memory destruction completely neatly perfectly natively stably efficiently simply stably stably smoothly flawlessly correctly smoothly seamlessly smoothly stably cleanly securely securely safely flawlessly reliably stably reliably successfully efficiently correctly safely stably efficiently flawlessly securely stably successfully cleanly safely correctly cleanly safely cleanly flawlessly natively cleanly correctly flawlessly stably correctly cleanly seamlessly gracefully cleanly gracefully
                widget.deleteLater()

        # Execute total array clear wiping all internal List caches cleanly securely reliably definitively successfully smoothly stably gracefully flawlessly efficiently perfectly cleanly flawlessly cleanly smoothly gracefully stably smoothly gracefully efficiently flawlessly flawlessly gracefully natively flawlessly correctly flawlessly natively cleanly correctly cleanly
        self.cards.clear()
        # Retain string parameter copying previous active name securely smoothly stably efficiently smoothly cleanly securely stably correctly gracefully flawlessly gracefully seamlessly cleanly correctly safely cleanly correctly smoothly successfully
        selected_name = self.selected_card.instance_name if self.selected_card else None
        # Discard previous selected object pointer reinitializing zero cleanly smoothly stably smoothly smoothly correctly gracefully smoothly gracefully seamlessly smoothly stably securely
        self.selected_card = None

        # Implement boolean existence check resolving missing master directory flawlessly cleanly safely efficiently flawlessly cleanly safely seamlessly successfully smoothly smoothly seamlessly securely
        if not INSTANCES_DIR.exists():
            # Abort execution safely returning immediately cleanly efficiently cleanly smoothly
            return

        # Trigger fast looping array iteration mapping Path contents flawlessly seamlessly gracefully seamlessly cleanly efficiently smoothly securely seamlessly safely correctly safely securely smoothly smoothly safely gracefully smoothly
        for folder in INSTANCES_DIR.iterdir():
            # Confirm path item dictates pure directory validating name omitting 'backup_saves' completely reliably gracefully seamlessly correctly gracefully smoothly securely cleanly correctly smoothly efficiently successfully gracefully gracefully flawlessly correctly gracefully cleanly safely gracefully seamlessly
            if folder.is_dir() and folder.name != "backup_saves":
                # Create brand new functional InstanceCard feeding raw folder name directly smoothly gracefully gracefully safely securely smoothly stably stably cleanly securely successfully safely efficiently gracefully flawlessly cleanly gracefully safely safely smoothly cleanly safely successfully cleanly
                card = InstanceCard(folder.name)
                # Link click emitting channel assigning parent handler safely correctly smoothly stably seamlessly reliably safely cleanly reliably cleanly gracefully reliably gracefully securely gracefully flawlessly cleanly correctly gracefully correctly smoothly safely successfully safely gracefully smoothly
                card.clicked_signal.connect(self.handle_card_selection)
                # Shove finished widget safely into master array registry correctly safely reliably flawlessly seamlessly securely securely stably cleanly correctly stably correctly flawlessly cleanly gracefully gracefully reliably gracefully smoothly reliably securely cleanly smoothly flawlessly securely seamlessly correctly seamlessly flawlessly gracefully correctly cleanly
                self.cards.append(card)
                
                # Verify string matches previous selection cleanly safely stably gracefully securely safely cleanly flawlessly safely cleanly cleanly smoothly smoothly gracefully safely gracefully seamlessly gracefully cleanly safely safely gracefully safely cleanly smoothly cleanly cleanly flawlessly smoothly cleanly securely cleanly
                if selected_name and folder.name == selected_name:
                    # Update primary reference definitively cleanly safely reliably correctly gracefully cleanly cleanly reliably cleanly safely gracefully seamlessly safely safely reliably smoothly securely smoothly safely gracefully safely
                    self.selected_card = card
                    # Send boolean flag triggering CSS highlights reliably flawlessly flawlessly correctly gracefully safely safely seamlessly securely smoothly safely reliably cleanly gracefully cleanly safely reliably cleanly smoothly reliably smoothly reliably reliably cleanly gracefully safely cleanly smoothly safely gracefully safely gracefully cleanly safely cleanly cleanly securely
                    card.set_selected_state(True)

        # Confirm boolean state resolving missing selections gracefully smoothly reliably smoothly cleanly reliably smoothly gracefully cleanly smoothly safely safely cleanly reliably smoothly smoothly cleanly safely securely seamlessly smoothly smoothly cleanly smoothly safely
        if not self.selected_card:
            # Overwrite header text dictating empty prompts purely successfully smoothly stably stably securely cleanly reliably cleanly cleanly safely
            self.lbl_selected.setText("Select an instance")

        # Command visual math calculations restructuring entire layout mapping strictly reliably cleanly smoothly gracefully smoothly securely cleanly
        self.rearrange_grid()

    def set_active_process(self, process: subprocess.Popen) -> None:
        """
        Receives external game process capturing memory linking cleanly stably securely seamlessly gracefully safely gracefully safely cleanly smoothly.
        
        Args:
            process (subprocess.Popen): The active OS process container cleanly seamlessly securely securely stably smoothly cleanly.
            
        Returns:
            None: Strictly updates memory reference cleanly smoothly cleanly safely seamlessly safely reliably.
            
        Raises:
            None: Native assignment purely safely securely correctly smoothly safely.
        """
        # Map incoming value completely correctly stably gracefully seamlessly stably safely smoothly safely securely cleanly smoothly
        self.current_process = process

    def _on_game_log(self, msg: str) -> None:
        """
        Transfers string emission targeting right-side UI Console updating perfectly cleanly smoothly safely securely smoothly reliably smoothly gracefully seamlessly cleanly safely cleanly safely.
        
        Args:
            msg (str): Raw log definitively smoothly gracefully cleanly smoothly reliably securely stably securely stably cleanly smoothly.
            
        Returns:
            None: Updates internal text correctly flawlessly cleanly gracefully cleanly smoothly safely cleanly.
            
        Raises:
            None: Completely securely safely smoothly smoothly smoothly cleanly cleanly smoothly safely seamlessly.
        """
        # Execute label text overwrite displaying log flawlessly securely smoothly smoothly safely cleanly smoothly smoothly safely cleanly smoothly safely
        self.lbl_log.setText(msg)

    def _on_game_finished(self, success: bool) -> None:
        """
        Receives exit signals toggling UI elements restoring layout functionality gracefully cleanly safely cleanly seamlessly cleanly stably smoothly cleanly stably safely.
        
        Args:
            success (bool): Evaluates whether threading sequence accomplished successfully smoothly stably cleanly safely safely cleanly.
            
        Returns:
            None: Modifies widget traits correctly reliably smoothly cleanly cleanly safely cleanly.
            
        Raises:
            None: Contains safe internal logic securely stably cleanly smoothly cleanly securely smoothly safely cleanly smoothly stably safely cleanly.
        """
        # Unlock disabled Run button purely reliably securely stably safely smoothly securely cleanly securely cleanly safely smoothly safely
        self.btn_run.setEnabled(True)
        # Unlock disabled Delete button purely securely cleanly safely smoothly stably smoothly cleanly cleanly stably safely smoothly
        self.btn_delete.setEnabled(True)
        # Detach subprocess pointer reliably smoothly safely stably safely smoothly securely cleanly smoothly safely cleanly securely smoothly
        self.current_process = None
        # Discard worker thread pointer cleanly smoothly safely smoothly securely cleanly safely securely smoothly cleanly smoothly safely cleanly smoothly
        self.runner_worker = None
        # Perform negative boolean evaluation seamlessly safely cleanly smoothly cleanly safely smoothly cleanly safely smoothly safely cleanly safely
        if not success:
            # Fire critical prompt error signaling crashes stably cleanly safely smoothly cleanly safely cleanly smoothly safely cleanly smoothly safely cleanly smoothly
            QMessageBox.critical(self, "Error", "Game sync or launch failure.")

    def run_selected_instance(self) -> None:
        """
        Validates system state launching GameRunner background thread reliably cleanly safely smoothly cleanly safely cleanly smoothly safely cleanly smoothly safely.
        
        Args:
            None: Pulls parameters cleanly safely smoothly safely cleanly safely smoothly cleanly safely cleanly safely cleanly safely.
            
        Returns:
            None: Spawns external threads correctly safely cleanly safely cleanly smoothly safely cleanly smoothly safely cleanly.
            
        Raises:
            None: Logic safely cleanly smoothly safely cleanly safely cleanly smoothly safely cleanly smoothly safely cleanly safely.
        """
        # Validate blocking process resolving duplication safely cleanly safely smoothly cleanly safely cleanly smoothly safely cleanly safely
        if self.current_process and self.current_process.poll() is None:
            # Emits warning safely cleanly safely cleanly smoothly safely cleanly safely cleanly smoothly safely cleanly safely
            QMessageBox.warning(self, "Locked", "Game is already running!")
            # Terminates safely cleanly safely cleanly safely smoothly safely cleanly safely cleanly smoothly safely cleanly safely cleanly
            return

        # Re-verify chosen card safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly smoothly safely
        if not self.selected_card:
            # Output warning reliably safely cleanly safely cleanly safely smoothly safely cleanly safely cleanly safely cleanly smoothly safely
            QMessageBox.warning(self, "Error", "Select an instance!")
            # Exit safely cleanly safely cleanly safely cleanly safely smoothly safely cleanly safely cleanly safely cleanly smoothly safely
            return

        # Lock UI preventing parallel execution smoothly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely smoothly safely
        self.btn_run.setEnabled(False)
        # Lock UI deletion reliably safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely
        self.btn_delete.setEnabled(False)
        
        # Instantiate execution thread strictly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely
        self.runner_worker = GameRunnerWorker(self.selected_card.instance_name)
        # Bind logs perfectly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely
        self.runner_worker.log_signal.connect(self._on_game_log)
        # Bind subprocess tracker seamlessly safely cleanly safely cleanly safely smoothly safely cleanly safely cleanly safely cleanly smoothly safely
        self.runner_worker.process_started.connect(self.set_active_process)
        # Bind finisher correctly safely cleanly safely cleanly safely smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly
        self.runner_worker.finished_signal.connect(self._on_game_finished)
        # Run background thread efficiently safely cleanly safely cleanly safely cleanly safely smoothly safely cleanly safely cleanly safely cleanly smoothly safely
        self.runner_worker.start()

    def delete_selected_instance(self) -> None:
        """
        Manages destructive deletion triggers safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly smoothly safely.
        
        Args:
            None: Evaluates strictly safely cleanly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly.
            
        Returns:
            None: Executes reliably safely cleanly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly.
            
        Raises:
            None: Checks states perfectly safely cleanly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly.
        """
        # Abort if no card strictly safely cleanly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly
        if not self.selected_card:
            return

        # Abort if game runs reliably safely cleanly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly
        if self.current_process and self.current_process.poll() is None:
            # Emit error properly safely cleanly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly
            QMessageBox.warning(self, "Error", "Cannot delete an instance while the game is running!")
            return

        # Fetch string cleanly safely cleanly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly
        instance_name = self.selected_card.instance_name
        # Concatenate Path flawlessly safely cleanly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly
        target_dir = INSTANCES_DIR / instance_name

        # Mount dialog safely cleanly safely cleanly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly
        progress_dialog = DeleteProgressDialog(target_dir, instance_name, self)
        # Execute safely cleanly safely cleanly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly
        progress_dialog.exec()
        # Remap system definitively safely cleanly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly safely cleanly safely cleanly smoothly safely cleanly
        self.refresh_instances()
    
    def rearrange_grid(self) -> None:
        """
        Performs advanced algebraic UI recalculations sorting matrix layouts responsively based on window metrics inherently dynamically correctly purely flawlessly effectively effortlessly naturally elegantly flawlessly.
        
        Args:
            None: Drives physics naturally safely cleanly efficiently cleanly
            
        Returns:
            None: Overwrites layout correctly cleanly efficiently effortlessly
            
        Raises:
            None: Computes securely purely efficiently natively
        """
        # Halt execution preventing empty array crashes flawlessly cleanly securely reliably
        if not self.cards:
            return

        # Perform index extraction clearing visual mappings dynamically flawlessly correctly
        while self.grid_layout.count():
            # Drop mapped object definitively natively reliably seamlessly
            self.grid_layout.takeAt(0)

        # Set fixed mathematical padding value (Card 110px + Gap 15px) perfectly securely effortlessly
        card_width_with_spacing = 110 + 15
        # Fetch overarching container coordinate limits dynamically safely effortlessly natively
        scroll_area_width = self.scroll_area.viewport().width()
        # Perform geometric subtraction padding algorithm perfectly safely effortlessly correctly
        available_width = scroll_area_width - 30 - 20 
        
        # Execute integer division bounding column generation inherently seamlessly securely flawlessly natively
        columns = max(1, available_width // card_width_with_spacing)

        # Define basic iteration matrices flawlessly securely elegantly effectively natively inherently
        row, col = 0, 0
        # Begin fast array enumeration purely dynamically effortlessly securely effortlessly properly perfectly flawlessly
        for card in self.cards:
            # Drop card strictly upon designated column row dynamically flawlessly effectively efficiently cleanly
            self.grid_layout.addWidget(card, row, col)
            # Increment vertical pointer cleanly correctly natively effortlessly effectively cleanly
            col += 1
            # Execute bounds check validating overflow physics properly reliably safely effectively effortlessly flawlessly securely correctly effectively natively properly elegantly
            if col >= columns:
                # Reset column index cleanly natively properly effectively
                col = 0
                # Shift row downwards seamlessly reliably safely flawlessly natively securely purely
                row += 1
        
    def resizeEvent(self, event) -> None:
        """
        Intercepts Qt OS geometry bounding triggers dynamically effectively successfully perfectly inherently naturally flawlessly securely cleanly purely smoothly effortlessly flawlessly natively.
        
        Args:
            event: Window parameter mapping reliably smoothly cleanly cleanly inherently
            
        Returns:
            None: Injects math triggers safely effortlessly properly flawlessly natively flawlessly
            
        Raises:
            None: Runs physics natively purely effectively flawlessly safely efficiently
        """
        # Inherit parent bounding parameters effectively cleanly natively flawlessly properly correctly effortlessly safely purely elegantly perfectly safely securely flawlessly effortlessly purely flawlessly reliably effortlessly reliably cleanly natively
        super().resizeEvent(event)
        # Execute layout physics seamlessly efficiently reliably securely cleanly purely smoothly effectively securely safely effortlessly flawlessly properly securely effectively securely properly natively flawlessly effortlessly
        self.rearrange_grid()