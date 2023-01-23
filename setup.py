import os
import sys
from pathlib import Path

root = Path(__file__).parent

print("Installing requirements... ")
os.system(f"{sys.executable} -m pip install -r {root/'requirements.txt'}")

print("Set up complete.")

print("Note: This project uses selenium with either firefox or chrome browsers.")
print(
    "If you do not have the appropriate web driver for your browser and system in your PATH or in this directory, you can find them here:"
)
print("https://github.com/mozilla/geckodriver/releases")
print("https://chromedriver.chromium.org/downloads")
input("Press any key to close... ")
