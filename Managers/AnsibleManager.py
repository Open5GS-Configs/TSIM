from pathlib import Path

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
        if(self.runCommand(["git", "ls-remote", self.config["ogs_repo"]]) != 0):
            self._raiseWrongConfig("ogs_repo")
        
        with open("roles/Open5GS Setup/vars/main.yml", "w") as f:
            f.write(f"ogs_repo: {config["ogs_repo"]}")
            f.write(f"ogs_version: {config["ogs_version"]}")

        for c in [["hplmn_config_path", "hplmn_config_repo"], ["vplmn_config_path", "vplmn_config_repo"], ["hplmn_hosts_path", "hplmn_hosts_repo"], ["vplmn_hosts_path", "vplmn_hosts_repo"]]:
            if self.config[c[0]] != None:
                # path is present
            else:
                if(self.runCommand(["git", "ls-remote", config[c[1]]]) != 0):
                    self._raiseWrongConfig(c[1])
        
                #  repo is present
                pass
            
        

    def _writeInventory():
        newInv = INVENTORY.replace("HPLMN_PUBLIC_IP", config["HPLMN_PUBLIC_IP"])
        newInv = INVENTORY.replace("VPLMN_PUBLIC_IP", config["VPLMN_PUBLIC_IP"])

        return newInv


    def _raiseWrongConfig(self, par):
        errorMsg = f"Required paramater was provided incorrectly: {par}"
        raise Exception(errorMsg)

    
    