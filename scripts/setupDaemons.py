
from os import listdir
from os.path import isfile, join

DAEMON_CONFIG_DIR = "/root/scripts/system"
SYSTEM_DIR = "/root/scripts/system"

onlyfiles = [f for f in listdir(DAEMON_CONFIG_DIR) if isfile(join(DAEMON_CONFIG_DIR, f))]
open5gsFiles = []
for file in onlyfiles:
    if file.startswith("open5gs-"):
        open5gsFiles.append(file)

for file in open5gsFiles:

    print(f"Reading file: {DAEMON_CONFIG_DIR}/{file}")
    with open(f"{DAEMON_CONFIG_DIR}/{file}", "r+") as f:
        text = f.read()

    text = text.replace("/root/open5gs-stable/", "/root/open5gs/")

    print(f"Writing to file: {SYSTEM_DIR}/{file}\n")
    with open(f"{SYSTEM_DIR}/{file}", "w") as daemonFile:
        daemonFile.write(text)


print("\nAll files have been written correctly!")

'''
for file in open5gsFiles:

    print(f"Reading file: {DAEMON_CONFIG_DIR}/{file}")
    with open(f"{DAEMON_CONFIG_DIR}/{file}", "r+") as f:
        text = f.read()

    text = text.replace("/usr/bin/", "/root/open5gs-stable/install/bin/")
    text = text.replace("/etc/open5gs/", "/root/open5gs-stable/install/etc/open5gs/")
    text = text.replace("User=open5gs", "User=root")
    text = text.replace("Group=open5gs", "Group=root")

    print(f"Writing to file: {SYSTEM_DIR}/{file}\n")
    with open(f"{SYSTEM_DIR}/{file}", "w") as daemonFile:
        daemonFile.write(text)


print("\nAll files have been written correctly!")
'''