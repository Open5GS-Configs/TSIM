import yaml
import jinja2

from .InfrastructureManager import InfrastructureManager
from .CommandLineManager import CommandLineManager


VARS_PATH = "vagrant-config/vars.yaml"

VARS = """general:
    ansible_ssh_key: {{ ansible_ssh_key }}
    user_ssh_key: {{ user_ssh_key }}
    provider: {{ provider }}

boxes:
{{ boxes }}

"""

BOX = """ {{ name }}:
    private_ip: 
{{ private_ip }}
    hostname: "{{ hostname }}"
    memory: {{ memory }}
    disk: {{ disk }}
    cpu: {{ cpu }}
"""

PRIVATE_IP = """      {{name}}: {{ ip }}
"""

class Vagrant(InfrastructureManager, CommandLineManager):
    def __init__(self, config, cwd):
        super().__init__(config)

        environment = jinja2.Environment()
        self.varsTemplate = environment.from_string(VARS)
        self.boxTemplate = environment.from_string(BOX)
        self.networkTemplate = environment.from_string(PRIVATE_IP)

        self.cwd = cwd


    def callInfManager(self):
        self._populateVars()
        
        if self.runCommand(["vagrant", "up"], cwd=(self.cwd / "vagrant-config")).returncode != 0:
            raise Exception("Error applying Vagrant plan") 

        print("\n\nSuccesfully created the following machines:\n")
        for box in self.config["boxes"]: print(f"- {box.upper()}") 
        print("\n\n")

        print("\n\n Vagrant completed succesfully!")


    def _populateVars(self):
        print("Populating Vagrant Vars...")

        boxes = ""
        for box in self.config["boxes"]:
          private_ip = ""
          for net in self.config["boxes"][box]["private_ip"]:
            private_ip += self.networkTemplate.render(
              name=net,
              ip=self.config["boxes"][box]["private_ip"][net]["ip"]
            )
            private_ip += "\n"

          boxes += self.boxTemplate.render(
            name=box,
            private_ip=private_ip,
            hostname=self.config["boxes"][box]["hostname"],
            memory=self.config["boxes"][box]["vagrant"]["ram"],
            disk=self.config["boxes"][box]["vagrant"]["disk"],
            cpu=self.config["boxes"][box]["vagrant"]["cpu"]
          )
          boxes += "\n\n"

        content = self.varsTemplate.render(
            provider=self.config["provider"],
            ansible_ssh_key=self.config["ansible_ssh_key"],
            user_ssh_key=self.config["user_ssh_key"],
            boxes=boxes
        )

        with open(self.cwd / VARS_PATH, 'w') as f:
            f.write(content)
        
        print("Vars created successfully!")


    def provision(self):
        res = self.runCommand(["vagrant", "provision"],  cwd=(self.cwd / "vagrant-config")) 
        if res.returncode != 0:
            raise Exception("Error in provisioning with Vagrant: " + res.stderr)


    def destroy(self):
        res = self.runCommand(["vagrant", "destroy"],  cwd=(self.cwd / "vagrant-config")) 
        if res.returncode != 0:
            raise Exception("Error destroying Vagrant VMs: ")


    def readIPs(self):
        res = self.runCommand(["vagrant", "ssh-config", "--machine-readable"], noOutput=True,  cwd=(self.cwd / "vagrant-config"))
        if res.returncode != 0:
            raise Exception("Error collecting VM IPs")

        plmn = ""
        ip = ""
        port = ""

        for t in res.stdout.split("\n"):
            data = t.split(",")
            if "ssh-config" in data:
                for c in data[3].split("\\n"):
                    sshConfig = c.split()
                    if "Host" in sshConfig:
                        plmn = sshConfig[1]
                    if "HostName" in sshConfig:
                        ip = sshConfig[1]
                    if "Port" in sshConfig:
                        port = sshConfig[1]
                self.config[plmn]["public_ip"] = ip
                self.config[plmn]["port"] = port
                print(f"SSH Config: {plmn} {ip} {port}")

