from json import loads
from pathlib import Path
from subprocess import run
from os import getenv

import argparse 
import yaml
import requests

from providers.InfrastructureManager import InfrastructureManager
from providers.OpenTofu import OpenTofu
from providers.Vagrant import Vagrant
from providers.AnsibleManager import AnsibleManager


CLOUD_PROVIDERS = ["vultr"]
LOCAL_PROVIDERS = ["vb", "vbox", "virtual box", "virtualbox", "vmware", "vm ware"]

COMMON_REQUIRED_PARAMETERS = ["OGS_REPO", "H-IP", "V-IP", "USER_SSH_KEY"]
LOCAL_REQUIRED_PARAMETERS = ["RAM", "DISK", "CPU"]
CLOUD_REQUIRED_PARAMETERS = ["H-REGION", "V-REGION", "VULTR_API_KEY", "VULTR_PLAN_ID", "VPC-REGION"]
SEPARATOR = ' '+'='*5+' '

class setupTOPSSIM():

    def __init__(self):
        self.args = self._parseArgs()
        self._parseConfig(self.args.ConfigFile)
        self.ansibleManager = AnsibleManager(self.config)


    def setup(self):
        print("Adding Control Node's SSH key to config\n")
        self._addAnsibleSSHKey(self.config)

        print(SEPARATOR + f"Calling {self.strategy.__class__.__name__}" + SEPARATOR)
        self.strategy.callInfManager(self.config)

        # now the VMs have been created and the IPs to ssh into the machines are stored within config
        print("\n"+SEPARATOR+f"Start Ansible Configuration"+SEPARATOR+"\n\n")

        # ansible-playbook release.yml --extra-vars "@some_file.yaml"
        #self.ansibleManager.configure()


    def getVultrPlans(self, apiKey):
        availVultrPlans = requests.get("https://api.vultr.com/v2/plans", headers={"Authorization": f"Bearer {apiKey}"})

        if availVultrPlans.status_code != 200:
            raise Exception("Error retrieving Vultr plans. Check internet connection or API key.")
        
        jsonVultrPlans = loads(str(availVultrPlans.content)[2:-1])['plans']
        return jsonVultrPlans


    def getVultrRegions(self, apiKey):
        availVultrRegions = requests.get("https://api.vultr.com/v2/regions", headers={"Authorization": f"Bearer {apiKey}"})    
        
        if availVultrRegions.status_code != 200:
            raise Exception("Error retrieving Vultr regions. Check internet connection or API key.")
        
        jsonVultrRegions = loads(str(availVultrRegions.content)[2:-1])['regions']
        return jsonVultrRegions


    def _parseConfig(self, configFile):
        print(SEPARATOR + "Reading Config File" + SEPARATOR)
        self.config = {}
        try:
            f = open(configFile, 'r')
        except FileNotFoundError:
            print(f"Inputted config file was not found: {configFile}")
        else:
            with f:
                self.config = yaml.load(f, Loader=yaml.SafeLoader)
        print("\nFile read succesfully!")

        configKeys = self.config.keys()
        print(SEPARATOR + "Asserting necessary parameters" + SEPARATOR)
        if not self.args.provider:
            if self.config["PROVIDER"].lower() in CLOUD_PROVIDERS:
                print("\nCloud Provider Recognized!")

                if "VULTR_API_KEY" not in configKeys:
                    self._raiseMissingConfig("VULTR_API_KEY")

                if self.args.VultrRegions:
                    regions = getVultrRegions(self.config['VULTR_API_KEY'])
                    [print(f"City: {region['city']}, ID: {region['id']}\n") for region in regions]
                    return
                
                if self.args.VultrRegions:
                    plans = getVultrPlans(self.config['VULTR_API_KEY'])
                    [print(f"ID: {plan['id']}\n") for plan in plans]
                    return

                for p in CLOUD_REQUIRED_PARAMETERS:
                    if p not in configKeys:
                        self._raiseMissingConfig(p)
                
                availPlans = self.getVultrPlans(self.config['VULTR_API_KEY'])
                idAvailPlans = [plan['id'] for plan in availPlans]
                if self.config["VULTR_PLAN_ID"] not in idAvailPlans:
                    self._raiseWrongConfig("VULTR_PLAN_ID")

                availRegions = self.getVultrRegions(self.config['VULTR_API_KEY'])
                idAvailRegions = [region['id'] for region in availRegions]
                for region in [self.config["H-REGION"], self.config["V-REGION"]]:
                    if region not in idAvailRegions:
                        self._raiseWrongConfig(region)

                self.strategy = OpenTofu()

            elif self.config["PROVIDER"].lower() in LOCAL_PROVIDERS:
                print("\nLocal Provider Recognized!")

                for p in LOCAL_REQUIRED_PARAMETERS:
                    if p not in configKeys:
                        self._raiseMissingConfig(p)

                self.strategy = Vagrant()
            
            else:
                raise Exception("Provider not recognized. Available providers are: VirtualBox, VMWare and Vultr")

        for p in COMMON_REQUIRED_PARAMETERS:
            if p not in configKeys:
                self._raiseMissingConfig(p)

        for c in [["HPLMNConfigPath", "HPLMNConfigRepo"], ["VPLMNConfigPath", "VPLMNConfigRepo"], ["HPLMNHostsPath", "HPLMNHostsRepo"], ["VPLMNHostsPath", "VPLMNHostsRepo"]]:
            bool configPresent = False

            if c[0] in configKeys:
                configPresent = True
            else:
                self.config[c[0]] = None

            if c[1] in configKeys:
                configPresent = True
            else:
                self.config[c[1]] = None
            
            if not configPresent:
                self._raiseMissingConfig(f"Either {c[0]} or {c[1]} must be present")
                

    def _parseArgs(self):
        parser = argparse.ArgumentParser(description="Open5Gs testing environment \
                                                    setup for the TOPSSIM project")

        parser.add_argument("ConfigFile", help="Gives the path to the config file that outlines all of the information necessary to execute the program")
        parser.add_argument("--provider", help="The VM provider that is used (Vultr, VirtualBox, VMWare, QEMU)")
        parser.add_argument("-VultrRegions", action='store_true', help="Shows the available regions for Vultr")
        parser.add_argument("-VultrPlans", action='store_true', help="Shows the available plans for Vultr")

        return parser.parse_args()


    def _addAnsibleSSHKey(self, config):
        homeDirectory = Path(getenv("HOME"))
        publicSSHPath = homeDirectory.joinpath(".ssh/id_rsa.pub")

        if not publicSSHPath.is_file():
            print("SSH Key not found. Generating new key... \n")
            run(["ssh-keygen", "-t", "ed25519", "-N", "''", "-f", publicSSHPath])
            print("Created SSH key for Control Node!\n")
        else:
            print("SSH key for Control Node was found\n")

        ControlNodeSSHKey = "" 
        with open(publicSSHPath.expanduser(), "r") as f:
            ControlNodeSSHKey = f.read().strip()
        
        config["ANSIBLE_SSH_KEY"] = ControlNodeSSHKey


    def _raiseMissingConfig(self, par):
        errorMsg = f"Required paramater not provided: {par}"
        raise Exception(errorMsg)


    def _raiseWrongConfig(self, par):
        errorMsg = f"Required paramater was provided incorrectly: {par}"
        raise Exception(errorMsg)


if __name__ == "__main__":
    setup = setupTOPSSIM()

    setup.setup()