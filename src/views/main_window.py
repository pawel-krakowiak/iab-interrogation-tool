"""
src/views/main_window.py

Composes the LeftPanel and RightPanel, connecting their signals properly.
"""

import sys
import logging
from typing import Optional

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout

from src.views.left_panel import LeftPanel
from src.views.right_panel import RightPanel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window that arranges the LeftPanel and RightPanel,
    ensuring signals/slots are connected with matching signatures.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initializes the main window with LeftPanel and RightPanel,
        setting up signal connections.
        """
        super().__init__(parent)
        self.setWindowTitle("Interrogation Log Parser")
        self.setMinimumSize(1200, 900)  # Allows maximizing and large workspace

        # Create panels
        self.left_panel = LeftPanel()
        self.right_panel = RightPanel()

        # Set up main layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.left_panel, 1)
        main_layout.addWidget(self.right_panel, 3)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Connect signals/slots
        self._connect_signals()

    def _connect_signals(self) -> None:
        """
        Connects signals from the left panel to the right panel (and vice versa).
        Ensures synchronization between user selections and log filtering.
        """
        logger.debug("🔗 Connecting Signals...")

        # When logs are loaded (list[str]) => RightPanel sets them
        self.left_panel.logsLoaded.connect(self.right_panel.on_logs_loaded)

        # When interviewer/interrogated states change => Pass (List[str], List[str], bool) to RightPanel
        self.left_panel.namesUpdated.connect(self._on_names_updated)

        # RightPanel has signals for toggles/order => Connect to workspace methods
        self.right_panel.filterTogglesUpdated.connect(
            self.right_panel.workspace.on_filter_toggles_updated
        )
        self.right_panel.orderChanged.connect(
            self.right_panel.workspace.on_order_changed
        )

        logger.debug("✅ Signals Connected")

    def _on_names_updated(
        self, interviewers: list[str], interrogated: list[str], show_related: bool
    ) -> None:
        """
        Handles updates from LeftPanel when the user selects interviewers/interrogated persons.
        Passes the updated names to RightPanel's workspace.
        """
        logger.debug(
            f"📝 Name Selection  [I]: {interviewers}, [O]: {interrogated}, OnlyRelated: {show_related}"
        )
        self.right_panel.on_names_updated(interviewers, interrogated, show_related)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
