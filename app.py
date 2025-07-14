import logging
import os
from PyQt6.QtWidgets import QApplication
from src.core.launcher import Launcher


def main():
    set_logging()
    logging.info("Starting FFT Minecraft Launcher")
    app = QApplication([])
    launcher = Launcher()
    launcher.run()
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
