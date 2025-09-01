from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EnvDocPanel(QWidget):
    """Placeholder Environment Doctor panel."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("EnvDoc (stub)"))
