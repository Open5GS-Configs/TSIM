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

COMMON_REQUIRED_PARAMETERS = ["ogs", "hplmn", "vplmn", "provider"]
LOCAL_REQUIRED_PARAMETERS = ["vagrant"]
VAGRANT_REQUIRED_PARAMETERS = ["ram", "disk", "cpu"]
VULTR_CLOUD_REQUIRED_PARAMETERS = ["plan_id", "hplmn_region", "hplmn_region"]
VPC_CLOUD_REQUIRED_PARAMETERS = ["region"]

SEPARATOR = ' '+'='*10+' '
DEFAULT_BRANCH = "main"


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

        self.ansibleManager = AnsibleManager(self.config, self.run, self.cwd)


    def setup(self):
        if self.strategy == None or self.ansibleManager == None: return

        print("Adding Control Node's SSH key to config\n")
        self._addAnsibleSSHKey()

        self.consoleRule(f"Calling {self.strategy.__class__.__name__}")
        self.strategy.callInfManager()

        # now the VMs have been created and the IPs to ssh into the machines are stored within config
        self.consoleRule("Start Ansible Configuration")
        self.callAnsible(self.config["ansible_tags"])

        if "ansible_tags" not in self.config.keys() or "testing_stage" in self.config["ansible_tags"]:
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
        if self.config["location"] == "cloud":
            if "public_ip" not in self.config["hplmn"].keys():
                self.strategy.readIPs()
            print(f'\n\nThe public IPs of the VMs are:\n - HPLMN: {self.config["hplmn"]["public_ip"]}\n - VPLMN: {self.config["vplmn"]["public_ip"]}')
        else:
            if "port" not in self.config["hplmn"].keys():
                self.strategy.readIPs()
            print(f'\n\nYour VMs are available through localhost with ports:\n - HPLMN: {self.config["hplmn"]["port"]}\n - VPLMN: {self.config["vplmn"]["port"]}')


    def printVultrRegions(self):
        regions = self.getVultrRegions(self.config['vultr']['api_key'])
        [print(f"City: {region['city']}, ID: {region['id']}\n") for region in regions]


    def printVultrPlans(self):
        plans = self.getVultrPlans(self.config['vultr']['api_key'])
        [print(f"ID: {plan['id']}\n") for plan in plans]


    def printReadme(self):
        with open((self.cwd / "README.md"), "r") as f:
            print(f.read())


    def _checkConfigurationValid(self):
        configKeys = self.config.keys()
        
        if "vultr_regions" in configKeys or "vultr_plans" in configKeys:
            self.config["vultr"] = {}
            self.config["vultr"]["api_key"] = getenv("VULTR_API_KEY")
            return False
        elif "readme" in configKeys:
            return False

        for p in COMMON_REQUIRED_PARAMETERS:
            if p not in configKeys:
                self._raiseMissingConfig(p)

        self.consoleRule("Asserting necessary parameters")
        self.config["provider"] = self.config["provider"].lower()
        if self.config["provider"] in CLOUD_PROVIDERS:
            print("\nCloud provider Recognized!")
            self.config["location"] = "cloud"

            self.config["vultr"]["api_key"] = getenv("VULTR_API_KEY")
            if self.config["vultr"]["api_key"] == None or self.config["vultr"]["api_key"] == "":
                self._raiseMissingConfig("vultr_api_key")
            
            print("Checking Vultr plan availability")
            availPlans = self.getVultrPlans(self.config["vultr"]['api_key'])
            idAvailPlans = [plan['id'] for plan in availPlans]
            if self.config["vultr"]["plan_id"] not in idAvailPlans:
                self._raiseWrongConfig("vultr_plan_id")

            print("Checking Vultr region availability")
            availRegions = self.getVultrRegions(self.config["vultr"]['api_key'])
            idAvailRegions = [region['id'] for region in availRegions]
            for region in [self.config["vultr"]["hplmn_region"], self.config["vultr"]["vplmn_region"]]:
                if region not in idAvailRegions:
                    self._raiseWrongConfig(region)
            
            if "vpc" not in self.config["vultr"].keys():
                self.config["vultr"]["vpc"]["v4_subnet_mask"] = "28"
                self.config["vultr"]["vpc"]["v4_subnet"] = "10.10.0.0"
            elif "v4_subnet_mask" not in self.config["vultr"]["vpc"].keys():
                self.config["vultr"]["vpc"]["v4_subnet_mask"] = "28"                
            elif "v4_subnet" not in self.config["vultr"]["vpc"].keys():
                self.config["vultr"]["vpc"]["v4_subnet"] = "10.10.0.0"
            
            for p in VULTR_CLOUD_REQUIRED_PARAMETERS:
                if p not in self.config["vultr"].keys():
                    self._raiseMissingConfig(p)
            
            for p in VPC_CLOUD_REQUIRED_PARAMETERS:
                if p not in self.config["vultr"]["vpc"].keys():
                    self._raiseMissingConfig(p)

            self.config["hplmn"]["port"] = ""
            self.config["vplmn"]["port"] = ""
            
            self.strategy = OpenTofu(self.config, self.cwd)

        elif self.config["provider"] in LOCAL_PROVIDERS:
            print("\nLocal provider Recognized!")
            self.config["location"] = "local"
            self.config["provider"] = self.config["provider"].lower()

            for p in LOCAL_REQUIRED_PARAMETERS:
                if p not in configKeys:
                    self._raiseMissingConfig(p)
            
            for p in VAGRANT_REQUIRED_PARAMETERS:
                if p not in self.config["vagrant"].keys():
                    self._raiseMissingConfig(p)

            self.strategy = Vagrant(self.config, self.cwd)
        
        else:
            raise Exception("provider not recognized. Available providers are: VirtualBox, VMWare and Vultr")

        for plmn in ["hplmn", "vplmn"]:
            plmnKeys = self.config[plmn].keys()

            for c in [["config_path", "config_repo"], ["hosts_path", "hosts_repo"]]:
                configPresent = False

                if c[0] in plmnKeys:
                    configPresent = True
                else:
                    self.config[plmn][c[0]] = None

                if c[1] in plmnKeys:
                    configPresent = True
                else:
                    self.config[plmn][c[1]] = None
                
                if not configPresent:
                    self._raiseMissingConfig(f"Either {c[0]} or {c[1]} must be present")
        
        if "version" not in self.config["ogs"].keys():
            self.config["ogs"]["version"] = DEFAULT_BRANCH
        elif self.config["ogs"]["version"] == None:
            self.config["ogs"]["version"] = DEFAULT_BRANCH

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
