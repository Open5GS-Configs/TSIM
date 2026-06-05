import subprocess

from os import listdir
from os.path import isfile, join

DAEMON_CONFIG_DIR = "/root/scripts/multi-user.target.wants"


onlyfiles = [f for f in listdir(DAEMON_CONFIG_DIR) if isfile(join(DAEMON_CONFIG_DIR, f))]
open5gsFiles = []

subprocess.run(["systemctl", "daemon-reload"])

for file in onlyfiles:
    if not file.startswith("open5gs-"):
        continue

    print(f"\n\nEnabling {file}...\n")
    subprocess.run(["chmod", "644", f"/etc/systemd/system/{file}"])
    subprocess.run(["systemctl", "enable", file])
    subprocess.run(["systemctl", "start", file])

print("\n\nAll services have been enabled and started!")