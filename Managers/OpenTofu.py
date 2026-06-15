from json import loads

from .InfrastructureManager import InfrastructureManager
from .CommandLineManager import CommandLineManager


VARS_PATH = "vultr-opentofu/terraform.tfvars"


class OpenTofu(InfrastructureManager, CommandLineManager):
    def __init__(self, config):
        super().__init__(config)
    
    def callInfManager(self):
        self.populateVars()

        res = self.runCommand(["tofu", "-chdir=vultr-opentofu", "init"]) 
        if res.returncode != 0:
            raise Exception("Error initiating OpenTofu")

        res = self.runCommand(["tofu", "-chdir=vultr-opentofu", "apply", "-auto-approve", "-show-sensitive", "-json-into=tofu_out.json"]) 
        if res.returncode != 0:
            raise Exception("Error applying OpenTofu plan") 
        
        # self.runCommand(["tofu", "-chdir=vultr-opentofu", "show", "-show-sensitive", "-json-into=tofu-apply.json"])

        print("\n\nSuccesfully created HPLMN and VPLMN machines!\n\n")

        with open("vultr-opentofu/tofu_out.json") as f:
            outFile = f.read()
            
            print("Reading OpenTofu outputs...")
            # only parse last line where outputs are stores
            outJson = loads(outFile.split("\n")[-2])

            self.config["hplmn"]["public_ip"] = outJson["outputs"]["hplm_ip"]["value"]
            self.config["vplmn"]["public_ip"] = outJson["outputs"]["vplm_ip"]["value"]

            print("\n\n OpenTofu completed succesfully!")

    
    def destroy(self):
        res = self.runCommand(["tofu", "-chdir=vultr-opentofu", "destroy"]) 
        if res.returncode != 0:
            raise Exception("Error initiating OpenTofu")

            
    def populateVars(self):
        print("Populating OpenTofu Vars...")

        with open(VARS_PATH, 'w') as f:
            try:
                f.write(f'vpc_v4_subnet_mask = \"{self.config["vultr"]["vpc"]["v4_subnet_mask"]}\"\n')
                f.write(f'vpc_v4_subnet = \"{self.config["vultr"]["vpc"]["v4_subnet"]}\"\n') 
                f.write(f'vpc_region = \"{self.config["vultr"]["vpc"]["region"]}\"\n') 
            
                f.write(f'vultr_api_key = \"{self.config["vultr"]["api_key"]}\"\n')
                f.write(f'vultr_plan_id = \"{self.config["vultr"]["plan_id"]}\"\n')
            
                f.write(f'h_region = \"{self.config["vultr"]["hplmn_region"]}\"\n')
                f.write(f'v_region = \"{self.config["vultr"]["vplmn_region"]}\"\n')
                f.write(f'user_ssh_key = \"{self.config["user_ssh_key"]}\"\n')
                f.write(f'ansible_ssh_key = \"{self.config["ansible_ssh_key"]}\"\n')

                f.write('H_HOSTNAME = "HPLMNTEST"\n')
                f.write('V_HOSTNAME = "VPLMNTEST"\n')
            except AtributeError as e:
                print("Attribute Error while writing OpenTofu variables: " + e)

        print("Vars created successfully!")
            
