from json import loads
from pathlib import Path
from subprocess import run
from os import getenv
from time import time

import argparse 
import yaml
import requests

from Managers.InfrastructureManager import InfrastructureManager
from Managers.OpenTofu import OpenTofu
from Managers.Vagrant import Vagrant
from Managers.AnsibleManager import AnsibleManager


CLOUD_PROVIDERS = ["vultr"]
LOCAL_PROVIDERS = ["vb", "vbox", "virtual box", "virtualbox", "vmware", "vm ware"]

COMMON_REQUIRED_PARAMETERS = ["ogs", "hplmn", "vplmn", "user_ssh_key", "provider"]
LOCAL_REQUIRED_PARAMETERS = ["vagrant"]
VAGRANT_REQUIRED_PARAMETERS = ["ram", "disk", "cpu"]
PLMN_CLOUD_REQUIRED_PARAMETERS = ["region"]
VULTR_CLOUD_REQUIRED_PARAMETERS = ["plan_id"]
VPC_CLOUD_REQUIRED_PARAMETERS = ["region"]

SEPARATOR = ' '+'='*10+' '
DEFAULT_BRANCH = "main"


class setupTOPSSIM():

    def __init__(self, config):
        self.config = config

        self.strategy = None
        self.ansibleManager = None
       # try:
        if not self._checkConfigurationValid():
            return
       # except AttributeError as e:
       #     print(f"Caught an error: {e}")
       #     print("Error present in configuration:(")
       #     return

        self.ansibleManager = AnsibleManager(self.config)


    def setup(self):
        if self.strategy == None or self.ansibleManager == None: return

        print("Adding Control Node's SSH key to config\n")
        self._addAnsibleSSHKey(self.config)

        print(SEPARATOR + f"Calling {self.strategy.__class__.__name__}" + SEPARATOR)
        self.strategy.callInfManager()

        # now the VMs have been created and the IPs to ssh into the machines are stored within config
        print("\n"+SEPARATOR+f"Start Ansible Configuration"+SEPARATOR+"\n\n")
        self.callAnsible()

        print(f'\n\nThe public IPs of the VMs are:\n - HPLMN: {self.config["hplmn"]["public_ip"]}\n - VPLMN: {self.config["vplmn"]["public_ip"]}')


    def destroy(self):
        if self.config["provider"].lower() in CLOUD_PROVIDERS:
            strategy = OpenTofu(self.config)
        elif self.config["provider"].lower() in LOCAL_PROVIDERS:
            strategy = Vagrant(self.config)
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
            raise Exception(f"Error retrieving Vultr plans. Check internet connection or API key. [Status Code: {availVultrPlans.status_code}]")
        
        jsonVultrPlans = loads(str(availVultrPlans.content)[2:-1])['plans']
        return jsonVultrPlans


    def getVultrRegions(self, apiKey):
        availVultrRegions = requests.get("https://api.vultr.com/v2/regions", headers={"Authorization": f"Bearer {apiKey}"})    
        
        if availVultrRegions.status_code != 200:
            raise Exception(f"Error retrieving Vultr plans. Check internet connection or API key. [Status Code: {availVultrPlans.status_code}]")
        
        jsonVultrRegions = loads(str(availVultrRegions.content)[2:-1])['regions']
        return jsonVultrRegions


    def _checkConfigurationValid(self):
        configKeys = self.config.keys()

        if "VultrRegions" in configKeys:
            regions = self.getVultrRegions(self.config['vultr_api_key'])
            [print(f"City: {region['city']}, ID: {region['id']}\n") for region in regions]
            return False
            
        if "VultrPlans" in configKeys:
            plans = self.getVultrPlans(self.config['vultr_api_key'])
            [print(f"ID: {plan['id']}\n") for plan in plans]
            return False
            
        if "readme" in configKeys:
            with open("README.md", "r") as f:
                print(f.read())
            return False
        
        print(SEPARATOR + "Asserting necessary parameters" + SEPARATOR)
        if self.config["provider"].lower() in CLOUD_PROVIDERS:
            print("\nCloud provider Recognized!")
            self.config["location"] = "cloud"

            for plmn in ["hplmn", "vplmn"]:
                for p in PLMN_CLOUD_REQUIRED_PARAMETERS:
                    if p not in self.config[plmn].keys():
                        self._raiseMissingConfig(p)
            
            print("Checking Vultr plan availability")
            availPlans = self.getVultrPlans(self.config["vultr"]['api_key'])
            idAvailPlans = [plan['id'] for plan in availPlans]
            if self.config["vultr"]["plan_id"] not in idAvailPlans:
                self._raiseWrongConfig("vultr_plan_id")

            print("Checking Vultr region availability")
            availRegions = self.getVultrRegions(self.config["vultr"]['api_key'])
            idAvailRegions = [region['id'] for region in availRegions]
            for region in [self.config["hplmn"]["region"], self.config["vplmn"]["region"]]:
                if region not in idAvailRegions:
                    self._raiseWrongConfig(region)
            
            if "vpc" not in self.config["vultr"].keys():
                config["vpc_v4_subnet_mask"] = "28"
                config["vpc_v4_subnet"] = "10.10.0.0"
            elif "v4_subnet_mask" not in self.config["vultr"]["vpc"].keys():
                config["vpc_v4_subnet_mask"] = "28"                
            elif "v4_subnet" not in self.config["vultr"]["vpc"].keys():
                config["vpc_v4_subnet"] = "10.10.0.0"
            
            for p in VULTR_CLOUD_REQUIRED_PARAMETERS:
                if p not in self.config["vultr"].keys():
                    self._raiseMissingConfig(p)
            
            for p in VPC_CLOUD_REQUIRED_PARAMETERS:
                if p not in self.config["vultr"]["vpc"].keys():
                    self._raiseMissingConfig(p)

            self.strategy = OpenTofu(self.config)

        elif self.config["provider"].lower() in LOCAL_PROVIDERS:
            print("\nLocal provider Recognized!")
            self.config["location"] = "local"

            for p in LOCAL_REQUIRED_PARAMETERS:
                if p not in configKeys:
                    self._raiseMissingConfig(p)
            
            for p in VAGRANT_REQUIRED_PARAMETERS:
                if p not in self.config["vagrant"].keys():
                    self._raiseMissingConfig(p)

            self.strategy = Vagrant(self.config)
        
        else:
            raise Exception("provider not recognized. Available providers are: VirtualBox, VMWare and Vultr")

        for p in COMMON_REQUIRED_PARAMETERS:
            if p not in configKeys:
                self._raiseMissingConfig(p)

        for plmn in ["hplmn", "vplmn"]:
            plmnKeys = self.config[plmn].keys()

            if ("test_command") not in plmnKeys:
                self.config[plmn]["test_command"] = ":"

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
            config["create_services"] = False

        if "ansible_tags" not in configKeys:
            self.config["ansible_tags"] = ""

        return True


    def _addAnsibleSSHKey(self, config):
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
        
        config["ansible_ssh_key"] = ControlNodeSSHKey


    def _raiseMissingConfig(self, par):
        errorMsg = f"Required paramater not provided: {par}"
        raise Exception(errorMsg)


    def _raiseWrongConfig(self, par):
        errorMsg = f"Required paramater was provided incorrectly: {par}"
        raise Exception(errorMsg)


def main():    
    '''
    This part of the code compiles and assimilates the command line arguments 
    and the configuration coming from the configuration file. The values given
    through the command line are mapped to the same structure than the ones in
    the config file, so that they can be used the same way everywhere.

    The command line arguments take precedence over the config file.
    '''

    start_time = time()

    parser = argparse.ArgumentParser(description="Open5Gs testing environment \
                                                setup for the TOPSSIM project", 
                                                argument_default=argparse.SUPPRESS)

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
    parser.add_argument("--create_services", action='store_true', help="Creates service files for OGS components in /etc/system/systemd")
    parser.add_argument('--ansible_tags', nargs='+', help="Tells ansible which stages to run. Options: install_stage, config_stage, testing_stage, services_stage, ogstun, install_ogs")

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
    parser.add_argument("--vpc_v4_subnet_mask", help="The mask for the VPC subnet")

    args = parser.parse_args()
    
    print(args)
    config = {}
    if hasattr(args, "config"):
        config = parseConfig(args.config, config)
    else:
        print("Config file was not passed!")

    config = apply_cli_overrides(config, args)

    for flag in ("destroy", "restart", "ansible", "VultrRegions", "VultrPlans", "readme"):
        if hasattr(args, flag):
            config[flag] = getattr(args, flag)

    setup = setupTOPSSIM(config)

    if "destroy" in config.keys():
        setup.destroy()
        return
    elif "restart" in config.keys():
        setup.destroy()
    elif "ansible" in config.keys():
        setup.callAnsible(writeInventory=False, tags=config["ansible_tags"])
        return
    setup.setup()

    print(f"\n\nExecution Complete!\nTime Elapsed: {(time()-start_time):.2f} seconds")


def parseConfig(configFile, config):
    print(SEPARATOR + "Reading Config File" + SEPARATOR)
    try:
        f = open(configFile, 'r')
    except FileNotFoundError:
        print(f"Inputted config file was not found: {configFile}")
    else:
        with f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
    print("\nFile read succesfully!")

    return config


def set_nested(d, path, value):
    cur = d
    for key in path[:-1]:
        cur = cur.setdefault(key, {})
    cur[path[-1]] = value


def apply_cli_overrides(config, args):
    # Map CLI argument names to nested config paths
    overrides = {
        "provider": ("provider",),
        "user_ssh_key": ("user_ssh_key",),
        "create_services": ("create_services",),
        "ogs_repo": ("ogs", "repo"),
        "ogs_version": ("ogs", "version"),
        "hplmn_ip": ("hplmn", "private_ip"),
        "vplmn_ip": ("vplmn", "private_ip"),
        "h_region": ("hplmn", "region"),
        "v_region": ("vplmn", "region"),
        "vultr_plan_id": ("vultr", "plan_id"),
        "vultr_api_key": ("vultr", "api_key"),
        "vpc_v4_subnet": ("vultr", "vpc", "v4_subnet"),
        "vpc_v4_subnet_mask": ("vultr", "vpc", "v4_subnet_mask"),
        "vpc_region": ("vultr", "vpc", "region"),
        "ansible_tags": ("ansible_tags",),
        "ram": ("Vagrant", "ram",),
        "disk": ("Vagrant", "disk",), 
        "cpu": ("Vagrant", "cpu",), 
    }

    for arg_name, path in overrides.items():
        value = getattr(args, arg_name, None)
        if value is not None:
            set_nested(config, path, value)

    return config


if __name__ == "__main__":
    main()
