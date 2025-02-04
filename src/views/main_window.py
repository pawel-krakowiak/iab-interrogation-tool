"""
src/views/main_window.py

Composes the LeftPanel and RightPanel, connecting their signals properly.
"""

import sys
from typing import Optional

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt

from src.views.left_panel import LeftPanel
from src.views.right_panel import RightPanel


class MainWindow(QMainWindow):
    """
    Main application window that arranges the LeftPanel and RightPanel,
    ensuring signals/slots are connected with matching signatures.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
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
        """
        # When logs are loaded (list[str]) => right panel sets them
        self.left_panel.logsLoaded.connect(self.right_panel.on_logs_loaded)

        # When interviewer/interrogated states change => pass (List[str], List[str], bool) to right panel
        self.left_panel.namesUpdated.connect(self.right_panel.on_names_updated)

        # Right panel has signals for toggles/order => connect to workspace methods
        self.right_panel.filterTogglesUpdated.connect(
            self.right_panel.workspace.on_filter_toggles_updated
        )
        self.right_panel.orderChanged.connect(
            self.right_panel.workspace.on_order_changed
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
