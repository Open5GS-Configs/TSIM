from os import listdir
from os.path import isfile, join

CONFIG_DIR = "/root/open5gs-stable/install/etc/open5gs"


for el in listdir(CONFIG_DIR):
    if not isfile(join(CONFIG_DIR, el)):
        continue
    if not el.endswith(".yaml"):
        continue
    
    file = el
    text = ""
    with open(join(CONFIG_DIR, file), "r+") as f:
        text = f.read()

    text = text.replace("/var/log/open5gs/", "/root/open5gs-stable/install/var/log/open5gs/")
    text = text.replace("/root/open5gs-stable/install/root/open5gs-stable/install/var/log/open5gs/", "/root/open5gs-stable/install/var/log/open5gs/")
    
    print(f"Writing to: {file}")
    
    with open(f"{CONFIG_DIR}/{file}", "w") as f:
        f.write(text)
    
print("\nLog Paths corrected!")