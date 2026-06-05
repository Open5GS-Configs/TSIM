from json import loads
from pathlib import Path
from subprocess import run
from os import getenv

import argparse 
import yaml
import requests

from Managers.InfrastructureManager import InfrastructureManager
from Managers.OpenTofu import OpenTofu
from Managers.Vagrant import Vagrant
from Managers.AnsibleManager import AnsibleManager


CLOUD_PROVIDERS = ["vultr"]
LOCAL_PROVIDERS = ["vb", "vbox", "virtual box", "virtualbox", "vmware", "vm ware"]

COMMON_REQUIRED_PARAMETERS = ["ogs_repo", "hplmn_ip", "vplmn_ip", "user_ssh_key"]
LOCAL_REQUIRED_PARAMETERS = ["ram", "disk", "cpu"]
CLOUD_REQUIRED_PARAMETERS = ["h_region", "v_region", "vultr_api_key", "vultr_plan_id", "vpc_region"]

SEPARATOR = ' '+'='*10+' '
DEFAULT_BRANCH = "main"


class setupTOPSSIM():

    def __init__(self, config):
        self.config = config

        self.strategy = None
        self.ansibleManager = None
        try:
            if not self._checkConfigurationValid():
                return
        except AttributeError:
            print("Error present in configuration:(")
            return

        self.ansibleManager = AnsibleManager(self.config)


    def setup(self):
        if self.strategy == None or self.ansibleManager == None: return

        print("Adding Control Node's SSH key to config\n")
        self._addAnsibleSSHKey(self.config)

        print(SEPARATOR + f"Calling {self.strategy.__class__.__name__}" + SEPARATOR)
        self.strategy.callInfManager(self.config)

        # now the VMs have been created and the IPs to ssh into the machines are stored within config
        print("\n"+SEPARATOR+f"Start Ansible Configuration"+SEPARATOR+"\n\n")

        self.callAnsible()



    def destroy(self):
        if self.config["provider"].lower() in CLOUD_PROVIDERS:
            strategy = OpenTofu()
        elif self.config["provider"].lower() in LOCAL_PROVIDERS:
            strategy = Vagrant()
        else:
            raise Exception("provider not recognized. Available providers are: VirtualBox, VMWare and Vultr")

        strategy.destroy()

        return False


    def callAnsible(self, writeInventory=True, tags=None):
        self.ansibleManager.configure(writeInventory)
        print("\n"+SEPARATOR+f"Start Ansible Setup in VMs"+SEPARATOR+"\n\n")
        self.ansibleManager.setup(tags)


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


    def _checkConfigurationValid(self):
        configKeys = self.config.keys()

        if self.config["VultrRegions"]:
            regions = self.getVultrRegions(self.config['vultr_api_key'])
            [print(f"City: {region['city']}, ID: {region['id']}\n") for region in regions]
            return False
            
        if self.config["VultrPlans"]:
            plans = self.getVultrPlans(self.config['vultr_api_key'])
            [print(f"ID: {plan['id']}\n") for plan in plans]
            return False
            
        if self.config["readme"]:
            with open("README.md", "r") as f:
                print(f.read())
            return False
        
        print(SEPARATOR + "Asserting necessary parameters" + SEPARATOR)
        if self.config["provider"].lower() in CLOUD_PROVIDERS:
            print("\nCloud provider Recognized!")

            if "vultr_api_key" not in configKeys:
                self._raiseMissingConfig("vultr_api_key")

            for p in CLOUD_REQUIRED_PARAMETERS:
                if p not in configKeys:
                    self._raiseMissingConfig(p)
            
            availPlans = self.getVultrPlans(self.config['vultr_api_key'])
            idAvailPlans = [plan['id'] for plan in availPlans]
            if self.config["vultr_plan_id"] not in idAvailPlans:
                self._raiseWrongConfig("vultr_plan_id")

            availRegions = self.getVultrRegions(self.config['vultr_api_key'])
            idAvailRegions = [region['id'] for region in availRegions]
            for region in [self.config["h_region"], self.config["v_region"]]:
                if region not in idAvailRegions:
                    self._raiseWrongConfig(region)
            
            if "vpc_v4_subnet_mask" not in configKeys:
                config["vpc_v4_subnet_mask"] = "28"
                
            if "vpc_v4_subnet" not in configKeys:
                config["vpc_v4_subnet"] = "10.10.0.0"

            self.strategy = OpenTofu()

        elif self.config["provider"].lower() in LOCAL_PROVIDERS:
            print("\nLocal provider Recognized!")

            for p in LOCAL_REQUIRED_PARAMETERS:
                if p not in configKeys:
                    self._raiseMissingConfig(p)

            self.strategy = Vagrant()
        
        else:
            raise Exception("provider not recognized. Available providers are: VirtualBox, VMWare and Vultr")

        for p in COMMON_REQUIRED_PARAMETERS:
            if p not in configKeys:
                self._raiseMissingConfig(p)

        for c in [["hplmn_config_path", "hplmn_config_repo"], ["vplmn_config_path", "vplmn_config_repo"], ["hplmn_hosts_path", "hplmn_hosts_repo"], ["vplmn_hosts_path", "vplmn_hosts_repo"]]:
            configPresent = False

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
        
        if "ogs_version" not in configKeys:
            self.config["ogs_version"] = DEFAULT_BRANCH
        elif self.config["ogs_version"] == None:
            self.config["ogs_version"] = DEFAULT_BRANCH

        if "services" not in configKeys:
            config["services"] = False
        
        for plmn in ["hplmn", "vplmn"]:
            if (plmn + "_test_command") not in configKeys:
                self.config[plmn + "_test_command"] = ":"
        
        return True


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
        
        config["ansible_ssh_key"] = ControlNodeSSHKey


    def _raiseMissingConfig(self, par):
        errorMsg = f"Required paramater not provided: {par}"
        raise Exception(errorMsg)


    def _raiseWrongConfig(self, par):
        errorMsg = f"Required paramater was provided incorrectly: {par}"
        raise Exception(errorMsg)


def main():    
    parser = argparse.ArgumentParser(description="Open5Gs testing environment \
                                                setup for the TOPSSIM project")

    # Actions
    parser.add_argument("-destroy", action='store_true', help="Destroys all of the current VMs")
    parser.add_argument("-restart", action='store_true', help="Destroys and restarts all of the current VMs")
    parser.add_argument("-ansible", action='store_true', help="Calls Ansible to setup the VMs")
    
    # These stop execution
    parser.add_argument("-VultrRegions", action='store_true', help="Shows the available regions for Vultr")
    parser.add_argument("-VultrPlans", action='store_true', help="Shows the available plans for Vultr")
    parser.add_argument("-readme", action='store_true', help="Prints the README")
    
    # General Arguments
    parser.add_argument("-c", "--config", help="Gives the path to the config file that outlines all of the information necessary to execute the program")
    parser.add_argument("--provider", help="The VM provider that is used (Vultr, VirtualBox, VMWare, QEMU)")
    parser.add_argument("--ogs_repo", help="The Open5GS repo that is installed to the VMs")
    parser.add_argument("--ogs_version", help="The version (branch) of the Open5GS repo that is cloned")
    parser.add_argument("--user_ssh_key", help="An ssh key automatically added to the authorized keys in the VMs")
    parser.add_argument("--hplmn_ip", help="The VPC ip of the home network")
    parser.add_argument("--vplmn_ip", help="The VPC ip of the visited network")
    parser.add_argument("--services", help="Creates service files for OGS components in /etc/system/systemd")
    parser.add_argument('--ansible_tags', nargs='+', help="Tells ansible which stages to run. Options: install_stage, config_stage, testing_stage, services_stage, ogstun, ")

    # Local Arguments
    parser.add_argument("--ram", help="The RAM used for the VMs (LOCAL ONLY)")
    parser.add_argument("--disk", help="The disk size allocated to the VMs (LOCAL ONLY)")
    parser.add_argument("--cpu", help="The amount of CPU allocated to the VMs (LOCAL ONLY)")


    # Vultr Arguments
    parser.add_argument("--h_region", help="The region where the home VM is created")
    parser.add_argument("--v_region", help="The region where the visited VM is created")
    parser.add_argument("--vpc_region", help="The region where the virutal private network is created")
    parser.add_argument("--vultr_api_key", help="Personal Vultr API key")
    parser.add_argument("--vultr_plan_id", help="The plan used to create the VMs")
    parser.add_argument("--vpc_v4_subnet", help="The subnet used to create the VPC betwene the VMs")
    parser.add_argument("--vpc_v4_subnet_mask:", help="The mask for the VPC subnet")

    clArgs, remaining_argv = parser.parse_known_args()
    
    if clArgs.config:
        fileConfig = parseConfig(clArgs.config)

        parser.set_defaults(**fileConfig)

    config = vars(parser.parse_args())
    
    
    setup = setupTOPSSIM(config)

    if config["destroy"]:
        setup.destroy()
        return
    elif config["restart"]:
        setup.destroy()
    elif config["ansible"]:
        setup.callAnsible(writeInventory=False, tags=config["ansible_tags"])
        return
    setup.setup()


def parseConfig(configFile):
        print(SEPARATOR + "Reading Config File" + SEPARATOR)
        config = {}
        try:
            f = open(configFile, 'r')
        except FileNotFoundError:
            print(f"Inputted config file was not found: {configFile}")
        else:
            with f:
                config = yaml.load(f, Loader=yaml.SafeLoader)
        print("\nFile read succesfully!")

        return config


if __name__ == "__main__":
    main()