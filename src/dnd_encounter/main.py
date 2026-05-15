# src/dnd_encounter/main.py
from PySide6.QtWidgets import QApplication
import sys


def main():
    app = QApplication(sys.argv)
    print("D&D Encounter Manager starting...")
    # Full UI will be added later
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
