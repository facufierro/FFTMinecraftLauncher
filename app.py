import logging
import os
from PySide6.QtWidgets import QApplication
from src.core.launcher import Launcher


def main():
    set_logging()
    app = QApplication([])
    import sys

    root_dir = os.path.dirname(
        sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
    )
    launcher = Launcher(root_dir)
    launcher.start()
    app.exec()


def set_logging():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        datefmt="%H:%M:%S",
        format="[%(levelname)s] [%(asctime)s]: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/latest.log", encoding="utf-8", mode="a"),
        ],
    )


if __name__ == "__main__":
    main()
