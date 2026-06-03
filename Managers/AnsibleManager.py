from pathlib import Path

from .CommandLineManager import CommandLineManager


INVENTORY = """
---
all:
  vars:
    ansible_user: root
  children: 
    hplmn:  
      hosts:
        hplmn_node_1: 
          ansible_host: HPLMN_PUBLIC_IP
    vplmn:  
      hosts:
        vplmn_node_1:
          ansible_host: VPLMN_PUBLIC_IP
"""

class AnsibleManager(CommandLineManager):

    def __init__(self, config):
        self.config = config


    def configure(self):
        print("Writing Inventory!")
        with open("ansible-setup/inventory/hosts.yaml", "w") as f:
            f.write(self._writeInventory())
        
        print("Writing Ansible variables!")
        self._writeVars()


    def setup(self):
        self.runCommand(["ansible-playbook", "topssim_setup.yaml", "-v"], cwd="ansible-setup")
        

    def _writeVars(self):
        if(self.runCommand(["git", "ls-remote", self.config["ogs_repo"]], noOutput=True) != 0):
            self._raiseWrongconfig("ogs_repo")
        else:
            print("Open5GS repo was found!")
        
        with open("ansible-setup/roles/Open5GS Setup/vars/main.yml", "w") as f:
            f.write(f"ogs_repo: {self.config['ogs_repo']}\n")
            f.write(f"ogs_version: {self.config['ogs_version']}")
        
        for plmn in ["hplmn", "vplmn"]:
            with open(f"ansible-setup/inventory/group_vars/{plmn}.yaml", "w") as f:
                f.write(f"private_ip: {self.config[plmn + '_ip']}\n")
                
                for c in [["_config_path", "_config_repo"], ["_hosts_path", "_hosts_repo"]]:
                    if self.config[plmn + c[0]] != None:
                        f.write(f"use_{c[0].split('_')[1]}_path: true\n")
                        f.write(f"{c[0][1:]}: {self.config[plmn + c[0]]}\n")
                    else:
                        if(self.runCommand(["git", "ls-remote", self.config[plmn + c[1]]], noOutput=True) != 0):
                            self._raiseWrongconfig(plmn + c[1])
                        else:
                            print(plmn + c[1] + " was found!")
                
                        f.write(f"use_{c[0].split('_')[1]}_path: false\n")
                        f.write(f"{c[1][1:]}: {self.config[plmn + c[1]]}\n")
                

    def _writeInventory(self):
        newInv = INVENTORY.replace("HPLMN_PUBLIC_IP", self.config["hplmn_public_ip"])
        newInv = newInv.replace("VPLMN_PUBLIC_IP", self.config["vplmn_public_ip"])

        return newInv


    def _raiseWrongconfig(self, par):
        errorMsg = f"Required paramater was provided incorrectly: {par}"
        raise Exception(errorMsg)

    
    