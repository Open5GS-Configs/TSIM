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


    def configure(self, writeInventory):
        if writeInventory:
            print("Writing Inventory!")
            with open("ansible-setup/inventory/hosts.yaml", "w") as f:
                f.write(self._writeInventory())
            
        print("Writing Ansible variables!")
        self._writeVars()


    def setup(self, tags):
        command = ["ansible-playbook", "topssim_setup.yaml"]
        if tags and len(tags) != 0:
            command.append("--tags")
            command.append(tags[0].replace(" ", ", "))
        self.runCommand(command, cwd="ansible-setup")
        

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

        '''
        When a Vultr machine is created its /etc/hosts file has this information:
        # Your system has configured 'manage_etc_hosts' as True.
        # As a result, if you wish for changes to this file to persist
        # then you will need to either
        # a.) make changes to the master file in /etc/cloud/templates/hosts.debian.tmpl

        This var makes it so that the hosts file is written at that address
        '''
        with open("ansible-setup/roles/Open5GS Config/vars/main.yml", "w") as f:
            with open("ansible-setup/roles/Netplan Config/vars/main.yml", "w") as g:
                if self.config["provider"].lower() == "vultr":
                    self.config["provider"] = "vultr"
                    self.config["dest_netplan_path"] = "/etc/netplan/50-cloud-init.yaml"

                else:
                    # TODO 
                    # LOCAL PROVIDER
                    self.config["provider"] = "something else"
                    self.config["dest_netplan_path"] = "/etc/netplan/00-installer-config.yaml"
                
                f.write("provider: " + self.config["provider"])
                
                g.write("dest_netplan_path: "  + f'\"{self.config["dest_netplan_path"]}\"' + "\n")
                g.write("vpc_v4_subnet_mask: "  + f'\"{self.config["vpc_v4_subnet_mask"]}\"' + "\n")


        if "create_services" not in self.config.keys():
            self.config["create_services"] = "true"
        with open("ansible-setup/vars/vars.yaml", "w") as f:
            f.write("---\n")
            f.write("vplmn_test_command: "  + f'\"{self.config["vplmn_test_command"]}\"' + "\n")
            f.write("hplmn_test_command: "  + f'\"{self.config["hplmn_test_command"]}\"' + "\n")
            f.write("create_services: "  + f'\"{self.config["create_services"]}\"' + "\n")


    def _writeInventory(self):
        newInv = INVENTORY.replace("HPLMN_PUBLIC_IP", self.config["hplmn_public_ip"])
        newInv = newInv.replace("VPLMN_PUBLIC_IP", self.config["vplmn_public_ip"])

        return newInv


    def _raiseWrongconfig(self, par):
        errorMsg = f"Required paramater was provided incorrectly: {par}"
        raise Exception(errorMsg)

    
    