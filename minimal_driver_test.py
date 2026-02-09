#!/usr/bin/env python3
"""Minimal test using cached ChromeDriver directly"""

from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Use cached ChromeDriver
chromedriver_path = Path.home() / ".wdm" / "drivers" / "chromedriver" / "win64" / "144.0.7559.133" / "chromedriver-win32" / "chromedriver.exe"

print(f"ChromeDriver path: {chromedriver_path}")
print(f"Exists: {chromedriver_path.exists()}")

if not chromedriver_path.exists():
    print("ERROR: ChromeDriver not found!")
    exit(1)

options = Options()
options.add_argument("--start-maximized")

print("Creating ChromeDriver service...")
service = Service(str(chromedriver_path))

print("Initializing webdriver...")
driver = webdriver.Chrome(service=service, options=options)

print("Opening Google...")
driver.get("https://www.google.com")
print(f"Page title: {driver.title}")

print("Closing browser...")
driver.quit()

print("SUCCESS!")
