import os

os.environ.setdefault(
  "QTWEBENGINE_CHROMIUM_FLAGS",
  "--disable-logging --log-level=3 --disable-blink-features=AutomationControlled",
)

from browser import main

if __name__ == "__main__":
  main()
