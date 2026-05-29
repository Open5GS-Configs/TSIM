

from .CommandLineManager import CommandLineManager


INVENTORY = """all:
  vars:
    ansible_user: root
  hosts:
    hplmn:
      ansible_host: HPLMN_PUBLIC_IP
    vplmn:
      ansible_host: VPLMN_PUBLIC_IP
"""

class AnsibleManager(CommandLineManager):

    def __init__(self, config):
        self.config = config


    def configure(self):
        with open("ansible-setup/inventory.yaml", "w") as f:
            f.write(self._writeInventory())

        with open("ansible-setup/ansible-vars.yaml", "w") as f:
            f.write(self._writeVars())


    def _writeVars():
        if(self.runCommand(["git", "ls-remote", self.config["OGS_REPO"]]) != 0):
            self._raiseWrongConfig("OGS_REPO")

        for c in ["HPLMNConfigPath", "VPLMNConfigPath", "HPLMNHostsPath", "VPLMNHostsPath"]
        if self.config[c] != None:
            # path is present
        else:
            c = c.replace("Path", "Repo")
            if(self.runCommand(["git", "ls-remote", config[c]]) != 0):
                self._raiseWrongConfig(c)
            
            #  repo is present
        

    def _writeInventory():
        INVENTORY.replace("HPLMN_PUBLIC_IP", config["HPLMN_PUBLIC_IP"])
        INVENTORY.replace("VPLMN_PUBLIC_IP", config["VPLMN_PUBLIC_IP"])


    def _raiseWrongConfig(self, par):
        errorMsg = f"Required paramater was provided incorrectly: {par}"
        raise Exception(errorMsg)

    
    