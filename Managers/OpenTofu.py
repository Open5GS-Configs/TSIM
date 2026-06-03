from json import loads

from .InfrastructureManager import InfrastructureManager
from .CommandLineManager import CommandLineManager

VARS_PATH = "vultr-opentofu/terraform.tfvars"
REQ_VARS = ["vpc_v4_subnet_mask", "vpc_v4_subnet", "ansible_ssh_key", "vultr_api_key", "vultr_plan_id", "h_region", "vpc_region", "v_region", "user_ssh_key"]
SEPARATOR = ' '+'='*5+' '


class OpenTofu(InfrastructureManager, CommandLineManager):
    def callInfManager(self, config):
        self.populateVars(config)

        
        if self.runCommand(["tofu", "-chdir=vultr-opentofu", "init"]) != 0:
            raise Exception("Error initiating OpenTofu")

            
        if self.runCommand(["tofu", "-chdir=vultr-opentofu", "apply", "-auto-approve", "-show-sensitive", "-json-into=tofu_out.json"]) != 0:
            raise Exception("Error applying OpenTofu plan") 
        
        # self.runCommand(["tofu", "-chdir=vultr-opentofu", "show", "-show-sensitive", "-json-into=tofu-apply.json"])

        print("\n\nSuccesfully create HPLMN and VPLMN machines!\n\n")

        with open("vultr-opentofu/tofu_out.json") as f:
            outFile = f.read()
            
            print("Reading OpenTofu outputs...")
            # only parse last line where outputs are stores
            outJson = loads(outFile.split("\n")[-2])

            config["hplmn_public_ip"] = outJson["outputs"]["hplm_ip"]["value"]
            config["vplmn_public_ip"] = outJson["outputs"]["vplm_ip"]["value"]

            print("\n\n OpenTofu completed succesfully!")
            
            
    def populateVars(self, config):
        print("Populating OpenTofu Vars...")

        with open(VARS_PATH, 'w') as f:
            for var in REQ_VARS:
                f.write(f'{var} = "{config[var]}"\n')
            f.write('H_HOSTNAME = "HPLMNTEST"\n')
            f.write('V_HOSTNAME = "VPLMNTEST"\n')

        print("Vars created successfully!")
            
