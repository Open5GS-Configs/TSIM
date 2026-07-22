from subprocess import run
from pathlib import Path
from json import loads
from time import time
from os import getenv

import argparse 
import requests
import yaml

from Managers.InfrastructureManager import InfrastructureManager
from Managers.CommandLineManager import CommandLineManager
from Managers.AnsibleManager import AnsibleManager
from Managers.OpenTofu import OpenTofu
from Managers.Vagrant import Vagrant


CLOUD_PROVIDERS = ["vultr"]
LOCAL_PROVIDERS = ["vb", "vmware"]

COMMON_REQUIRED_PARAMETERS = ["provider"]
VAGRANT_REQUIRED_PARAMETERS = ["ram", "disk", "cpu"]
VULTR_CLOUD_REQUIRED_PARAMETERS = []
VPC_CLOUD_REQUIRED_PARAMETERS = []

SEPARATOR = ' '+'='*10+' '
DEFAULT_BRANCH = "main"
DEFAULT_REPO = "https://github.com/open5gs/open5gs"


class setupTOPSSIM(CommandLineManager):

    def __init__(self, config, run, cwd):
        self.config = config
        self.run = run
        self.cwd = cwd

        self.strategy = None
        self.ansibleManager = None
        try:
            if not self._checkConfigurationValid():
                return
        except AttributeError as e:
            print(f"Error present in configuration:(\n{e}")
            return

        print("Adding Control Node's SSH key to config\n")
        self._addAnsibleSSHKey()

        self.ansibleManager = AnsibleManager(self.config, self.run, self.cwd)


    def setup(self, runTest=False):
        if self.strategy == None or self.ansibleManager == None: return

        self.consoleRule(f"Calling {self.strategy.__class__.__name__}")
        self.strategy.callInfManager()

        # now the VMs have been created and the IPs to ssh into the machines are stored within config
        self.consoleRule("Start Ansible Configuration")
        self.callAnsible(self.config["ansible_tags"])

        if runTest or "ansible_tags" not in self.config.keys() or "testing_stage" in self.config["ansible_tags"]:
            self.consoleRule("Run File Execution")
            self.ansibleManager.runFileCommands()
        
        self.printVMIPs()


    def destroy(self):
        if self.config["provider"].lower() in CLOUD_PROVIDERS:
            strategy = OpenTofu(self.config, self.cwd)
        elif self.config["provider"].lower() in LOCAL_PROVIDERS:
            strategy = Vagrant(self.config, self.cwd)
        else:
            raise Exception("provider not recognized. Available providers are: VirtualBox, VMWare and Vultr")

        strategy.destroy()

        return False


    def callAnsible(self, tags, writeInventory=True):
        self.ansibleManager.configure(writeInventory)
        self.consoleRule(f"Start Ansible Setup in VMs")
         
        self.ansibleManager.setup(tags)


    def getVultrPlans(self, apiKey):
        availVultrPlans = requests.get("https://api.vultr.com/v2/plans", headers={"Authorization": f"Bearer {apiKey}"})

        if availVultrPlans.status_code != 200:
            raise Exception(f"Error retrieving Vultr plans. Check internet connection or API key. [Status Code: {availVultrPlans.status_code}]")
        
        jsonVultrPlans = loads(str(availVultrPlans.content)[2:-1])['plans']
        return jsonVultrPlans


    def getVultrRegions(self, apiKey):
        availVultrRegions = requests.get("https://api.vultr.com/v2/regions", headers={"Authorization": f"Bearer {apiKey}"})    
        
        if availVultrRegions.status_code != 200:
            raise Exception(f"Error retrieving Vultr plans. Check internet connection or API key. [Status Code: {availVultrPlans.status_code}]")
        
        jsonVultrRegions = loads(str(availVultrRegions.content)[2:-1])['regions']
        return jsonVultrRegions


    def printVMIPs(self):
        boxConfigKeys = self.config["boxes"][list(self.config["boxes"].keys())[0]].keys()
        if self.config["location"] == "cloud":
            if "public_ip" not in boxConfigKeys:
                self.strategy.readIPs()
            print(f'\n\nThe public IPs of the VMs are:') 
            for box in self.config["boxes"]:
                print(f'- {box.upper()}: {self.config["boxes"][box]["public_ip"]}')
        else:
            if "port" not in boxConfigKeys:
                self.strategy.readIPs()
            print(f'\n\nYour VMs are available through localhost with ports:') 
            for box in self.config["boxes"]:
                print(f'- {box.upper()}: {self.config["boxes"][box]["port"]}')


    def printVultrRegions(self):
        regions = self.getVultrRegions(self.config['vultr_api_key'])
        [print(f"City: {region['city']}, ID: {region['id']}\n") for region in regions]


    def printVultrPlans(self):
        plans = self.getVultrPlans(self.config['vultr_api_key'])
        [print(f"ID: {plan['id']}\n") for plan in plans]


    def printReadme(self):
        with open((self.cwd / "README.md"), "r") as f:
            print(f.read())


    def dictCopy(self, a, b):
        for key in a.keys():
            if isinstance(a[key], dict):
                b[key] = {}
                self.dictCopy(a[key], b[key])
            else:
                b[key] = a[key]


    def _checkConfigurationValid(self):
        configKeys = self.config.keys()
                
        if "vultr_regions" in configKeys or "vultr_plans" in configKeys:
            self.config["vultr"] = {}
            self.config["vultr_api_key"] = getenv("VULTR_API_KEY")
            return False
        elif "readme" in configKeys:
            return False

        self.consoleRule("Asserting necessary parameters")
        for p in COMMON_REQUIRED_PARAMETERS:
            if p not in configKeys:
                self._raiseMissingConfig(p)

        self.config["ogs_boxes"] = []
        for box in self.config["boxes"]:
            if "private_ip" not in self.config["boxes"][box]:
                self.config["boxes"][box]["private_ip"] = {}
                
            if "config" in self.config["boxes"][box].keys() and self.config["boxes"][box]["config"] in self.config["configs"]:
                tmp = {}
                self.dictCopy(self.config["boxes"][box], tmp)

                self.dictCopy(self.config["configs"][self.config["boxes"][box]["config"]], self.config["boxes"][box])
                
                self.dictCopy(tmp, self.config["boxes"][box])
            
            if "ogs" in self.config["boxes"][box].keys(): 
                self.config["ogs_boxes"].append(box)
                self.config["boxes"][box]["provisioning_script"] = ""
        
        self.config.pop("config", None)
        self.config["provider"] = self.config["provider"].lower()
        if self.config["provider"] in CLOUD_PROVIDERS:
            print("\nCloud provider Recognized!")
            self.config["location"] = "cloud"

            self.config["vultr_api_key"] = getenv("VULTR_API_KEY")
            if self.config["vultr_api_key"] == None or self.config["vultr_api_key"] == "":
                self._raiseMissingConfig("vultr_api_key")
            
            for box in self.config["boxes"]:
                self.config["boxes"][box]["port"] = ""

                print("Checking Vultr plan availability for " + box.upper())
                availPlans = self.getVultrPlans(self.config["vultr_api_key"])
                idAvailPlans = [plan['id'] for plan in availPlans]
                if self.config["boxes"][box]["vultr"]["plan_id"] not in idAvailPlans:
                    self._raiseWrongConfig(f"Error in box {box}: vultr_plan_id")

                print("Checking Vultr region availability for " + box.upper())
                availRegions = self.getVultrRegions(self.config["vultr_api_key"])
                idAvailRegions = [region['id'] for region in availRegions]
                if self.config["boxes"][box]["vultr"]["region"] not in idAvailRegions:
                    self._raiseWrongConfig(f"Error in box {box}: {region} not available")

                self.config["boxes"][box]["vagrant"] = {}
                self.config["boxes"][box]["vagrant"]["use_netem"] = False
                self.config["boxes"][box]["vagrant"]["netem"] = ""
            
            self.strategy = OpenTofu(self.config, self.cwd)

        elif self.config["provider"] in LOCAL_PROVIDERS:
            print("\nLocal provider Recognized!")
            self.config["location"] = "local"

            for box in self.config["boxes"]:
                for p in VAGRANT_REQUIRED_PARAMETERS:
                    if p not in self.config["boxes"][box]["vagrant"]:
                        self._raiseMissingConfig(p)

            self.strategy = Vagrant(self.config, self.cwd)
        
        else:
            raise Exception("provider not recognized. Available providers are: VirtualBox, VMWare and Vultr")

        for box in self.config["boxes"]:
            self.config["boxes"][box]["hostname"] = box.upper() + "-TEST"
            
            if box not in self.config["ogs_boxes"]: 
                self.config["boxes"][box]["ogs"] = {}

            boxKeys = self.config["boxes"][box].keys()
            
            for i in range(len(self.config["peering"])):
                if box in self.config["peering"][i]["members"]:
                    if "interface_number" not in self.config["boxes"][box]: self.config["boxes"][box]["interface_number"] = 8        
                    self.config["boxes"][box]["private_ip"][self.config["peering"][i]["name"]]["interface"] = f'enp{self.config["boxes"][box]["interface_number"]}s0'
                    self.config["boxes"][box]["interface_number"] += 1


            for c in [["config_path", "config_repo"], ["hosts_path", "hosts_repo"]]:
                configPresent = False

                if c[0] in boxKeys:
                    configPresent = True
                else:
                    self.config["boxes"][box][c[0]] = ""

                if c[1] in boxKeys:
                    configPresent = True
                else:
                    self.config["boxes"][box][c[1]] = ""
                
                if not configPresent and box in self.config["ogs_boxes"]:
                    self._raiseMissingConfig(f"Either {c[0]} or {c[1]} must be present")

            if "repo" not in self.config["boxes"][box]["ogs"].keys():
                self.config["boxes"][box]["ogs"]["repo"] = DEFAULT_REPO
            elif self.config["boxes"][box]["ogs"]["repo"] == None:
                self.config["boxes"][box]["ogs"]["repo"] = DEFAULT_REPO
            if "version" not in self.config["boxes"][box]["ogs"].keys():
                self.config["boxes"][box]["ogs"]["version"] = DEFAULT_BRANCH
            elif self.config["boxes"][box]["ogs"]["version"] == None:
                self.config["boxes"][box]["ogs"]["version"] = DEFAULT_BRANCH

            if "mongodb" not in self.config["boxes"][box]:
                self.config["boxes"][box]["mongodb"] = False

        if "create_services" not in configKeys:
            self.config["create_services"] = False

        if "capture_packets" not in configKeys:
            self.config["capture_packets"] = False
            
        if "write_test_output" not in configKeys:
            self.config["write_test_output"] = False

        if "copy_logs" not in configKeys:
            self.config["copy_logs"] = False

        if "user_ssh_key" not in configKeys:
            self.config["user_ssh_key"] = ""
        
        if "ansible_tags" not in configKeys:
            self.config["ansible_tags"] = ""

        self.config["hplmn"]["hostname"] = "HPLMNTEST"
        self.config["vplmn"]["hostname"] = "VPLMNTEST"

        return True


    def _addAnsibleSSHKey(self):
        sshConfig = Path(getenv("HOME")).joinpath(".ssh")
        privateSSHPath = sshConfig.joinpath("id_rsa")
        publicSSHPath = privateSSHPath.with_suffix(".pub")

        if not publicSSHPath.is_file():
            print("SSH Key not found. Generating new key... \n")
            run(["ssh-keygen", "-t", "ed25519", "-N", "", "-f", privateSSHPath])
            print("Created SSH key for Control Node!\n")
        else:
            print("SSH key for Control Node was found\n")

        ControlNodeSSHKey = "" 
        with open(publicSSHPath.expanduser(), "r") as f:
            ControlNodeSSHKey = f.read().strip()
        
        self.config["ansible_ssh_key"] = ControlNodeSSHKey


    def _raiseMissingConfig(self, par):
        errorMsg = f"Required paramater not provided: {par}"
        raise Exception(errorMsg)


    def _raiseWrongConfig(self, par):
        errorMsg = f"Required paramater was provided incorrectly: {par}"
        raise Exception(errorMsg)
