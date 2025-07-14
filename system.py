#!/usr/bin/env python3
import time
import platform
import socket
import subprocess
import os

def print_system_info():
    print("📡 Gathering system information...\n")
    
    # OS and hardware
    print("🖥️ System:", platform.system(), platform.release())
    print("📦 Platform:", platform.platform())
    print("🧠 Architecture:", platform.machine())

    # Hostname and IP
    hostname = socket.gethostname()
    print("🛰️ Hostname:", hostname)
    try:
        ip = socket.gethostbyname(hostname)
        print("🌐 IP Address:", ip)
    except:
        print("🌐 IP Address: Unavailable")

    # Check if Raspberry Pi
    if os.path.exists("/proc/device-tree/model"):
        with open("/proc/device-tree/model") as f:
            model = f.read().strip()
            print("🍓 Raspberry Pi Model:", model)

    # Uptime
    try:
        with open("/proc/uptime") as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_hours = uptime_seconds / 3600
            print(f"⏱️ Uptime: {uptime_hours:.2f} hours")
    except:
        print("⏱️ Uptime: Unavailable")

    # CPU Temp (if available)
    try:
        temp = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
        print("🔥 CPU Temp:", temp.strip())
    except:
        print("🔥 CPU Temp: Not available or not a Pi")

    # RAM usage
    try:
        meminfo = subprocess.check_output("free -h", shell=True).decode()
        print("💾 Memory Info:\n", meminfo)
    except:
        print("💾 Memory Info: Not available")

    # Disk space
    try:
        disk = subprocess.check_output("df -h /", shell=True).decode()
        print("📂 Disk Usage:\n", disk)
    except:
        print("📂 Disk Usage: Not available")

# Script flow
print("🤖 May I call you Quendor?")
time.sleep(3)

print("\n📋 Here's information about the system:\n")
print_system_info()

time.sleep(3)
print("\n⏳ Quendor, please hold on a sec...")
