#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import subprocess
import sys
from datetime import datetime

APP = Path("/opt/JeremiahsPart/JeremiahsPart.py")
RESTORE = Path("/opt/JeremiahsPart/restore.py")
BACKUP_DIR = Path("/home/we6jbo/backup-this")

def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not RESTORE.exists():
        raise SystemExit("Missing /opt/JeremiahsPart/restore.py")
    if APP.exists():
        backup = BACKUP_DIR / f"JeremiahsPart.before-small-restore.{datetime.now().strftime('%Y%m%d-%H%M%S')}.py"
        shutil.copy2(APP, backup)
        print(f"Backed up current app to {backup}")
    shutil.copy2(RESTORE, APP)
    os.chmod(APP, 0o755)
    print("Copied /opt/JeremiahsPart/restore.py to /opt/JeremiahsPart/JeremiahsPart.py")
    subprocess.Popen([sys.executable, str(APP)])
    print("Reran /opt/JeremiahsPart/JeremiahsPart.py")

if __name__ == "__main__":
    main()
