
import logging
import os
# Force-inject GITHUB_TOKEN and GH_TOKEN from the current process environment (for VSCode/PowerShell/gh CLI compatibility)
import sys
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    # Running in a virtualenv, ensure env vars are present
    pass
for token_var in ("GITHUB_TOKEN", "GH_TOKEN"):
    if token_var in os.environ:
        os.environ[token_var] = os.environ[token_var]
from PySide6.QtWidgets import QApplication
from src.core.launcher import Launcher


def main():
    set_logging()
    # Debug: Print and log detected GitHub tokens at startup
    import os, logging
    for token_var in ("GITHUB_TOKEN", "GH_TOKEN"):
        val = os.environ.get(token_var)
        if val:
            print(f"[DEBUG] {token_var} detected: {val[:4]}...{val[-4:]}")
            logging.info(f"{token_var} detected: {val[:4]}...{val[-4:]}")
        else:
            print(f"[DEBUG] {token_var} not set")
            logging.info(f"{token_var} not set")
    app = QApplication([])
    launcher = Launcher()
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
