import jinja2

from pathlib import Path
from .CommandLineManager import CommandLineManager

TEST_COMMAND_TIMEOUT = 120
INVENTORY = """
---
all:
  vars:
    ansible_user: {{ ansible_user }}
  children: 
    hplmn:  
      hosts:
        hplmn_node_1: 
          ansible_host: {{ hplmn_public_ip }}
        {% if provider == "local" %}
          ansible_port: {{ hplmn_port }}
        {% endif %}
    vplmn:  
      hosts:
        vplmn_node_1:
          ansible_host: {{ vplmn_public_ip }}
        {% if provider == "local" %}
          ansible_port: {{ vplmn_port }}
        {% endif %}
"""


class AnsibleManager(CommandLineManager):

    def __init__(self, config):
        self.config = config
        environment = jinja2.Environment()
        self.template = environment.from_string(INVENTORY)

    def configure(self, writeInventory):
        if writeInventory:
            print("Writing Inventory!")
            with open("ansible-setup/inventory/hosts.yaml", "w") as f:
                f.write(self._writeInventory())
            
        print("Writing Ansible variables!")
        self._writeVars()


    def setup(self, tags):
        command = ["ansible-playbook", "topssim_setup.yaml", "-vv"]
        if tags and len(tags) != 0:
            command.append("--tags")
            command.append(tags[0].replace(" ", ", "))
        res = self.runCommand(command, cwd="ansible-setup")
        if res.returncode != 0:
            raise Exception("Ansible Playbook presented an error!")
        

    def _writeVars(self):
        res = self.runCommand(["git", "ls-remote", self.config["ogs"]["repo"]], noOutput=True) 
        if res.returncode != 0:
            self._raiseWrongconfig("ogs_repo")
        else:
            print("Open5GS repo was found!")
        
        with open("ansible-setup/roles/Open5GS Setup/vars/main.yml", "w") as f:
            f.write(f"ogs_repo: {self.config['ogs']['repo']}\n")
            f.write(f"ogs_version: {self.config['ogs']['version']}")
        
        for plmn in ["hplmn", "vplmn"]:
            with open(f"ansible-setup/inventory/group_vars/{plmn}.yaml", "w") as f:
                f.write(f"private_ip: {self.config[plmn]['private_ip']}\n")
                
                for c in [["config_path", "config_repo"], ["hosts_path", "hosts_repo"]]:
                    if self.config[plmn][c[0]] != None:
                        f.write(f"use_{c[0].split('_')[0]}_path: true\n")
                        f.write(f"{c[0]}: {self.config[plmn][c[0]]}\n")
                    else:
                        res = self.runCommand(["git", "ls-remote", self.config[plmn][c[1]]], noOutput=True) 
                        if res.returncode != 0:
                            self._raiseWrongconfig(plmn + c[1])
                        else:
                            print(plmn + c[1] + " was found!")
                
                        f.write(f"use_{c[0].split('_')[0]}_path: false\n")
                        f.write(f"{c[1]}: {self.config[plmn][c[1]]}\n")

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
                    
                    g.write("vpc_v4_subnet_mask: "  + f'\"{self.config["vultr"]["vpc"]["v4_subnet_mask"]}\"' + "\n")
                else:
                    self.config["dest_netplan_path"] = "/etc/netplan/50-vagrant.yaml"
                
                f.write("provider: " + self.config["provider"])
                
                g.write("dest_netplan_path: "  + f'\"{self.config["dest_netplan_path"]}\"' + "\n")
                

        if "create_services" not in self.config.keys():
            self.config["create_services"] = "true"
        with open("ansible-setup/vars/vars.yaml", "w") as f:
            f.write("---\n")
            f.write("vplmn_test_script: "  + f'{self.config["vplmn"]["test_script"]}' + "\n")
            f.write("hplmn_test_script: "  + f'{self.config["hplmn"]["test_script"]}' + "\n")
            f.write("test_command_timeout: "  + str(TEST_COMMAND_TIMEOUT) + "\n")
            f.write("create_services: "  + f'\"{self.config["create_services"]}\"' + "\n")


    def _writeInventory(self):
        if self.config["location"] == "cloud":
            self.config["hplmn"]["ip"] = 22
            self.config["hplmn"]["ip"] = 22
            user = "root"
        else:
            user = "vagrant"

        content = self.template.render(
                hplmn_public_ip=self.config["hplmn"]["public_ip"],
                hplmn_port=self.config["hplmn"]["port"],
                vplmn_public_ip=self.config["vplmn"]["public_ip"],
                vplmn_port=self.config["vplmn"]["port"],
                provider=self.config["location"],
                ansible_user=user
                )

        return content


    def _raiseWrongconfig(self, par):
        errorMsg = f"Required paramater was provided incorrectly: {par}"
        raise Exception(errorMsg)

    
    
