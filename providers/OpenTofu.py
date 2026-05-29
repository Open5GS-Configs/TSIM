from subprocess import run

from .InfrastructureManager import InfrastructureManager

VARS_PATH = "vultr-opentofu/terraform.tfvars"
REQ_VARS = ["ANSIBLE_SSH_KEY", "VULTR_API_KEY", "VULTR_PLAN_ID", "H-REGION", "VPC-REGION", "V-REGION", "USER_SSH_KEY"]
SEPARATOR = ' '+'='*5+' '


class OpenTofu(InfrastructureManager):
    def callInfManager(self, config):


        self.populateVars(config)

        self.runCommand(["tofu", "-chdir=vultr-opentofu", "init"])
        self.runCommand(["tofu", "-chdir=vultr-opentofu", "plan", "-show-sensitive"])
        self.runCommand(["tofu", "-chdir=vultr-opentofu", "apply", "-auto-approve", "-show-sensitive", "-json-into=tofu-apply.json"])

        print("Succesfully create HPLMN and VPLMN machines!")
            


    def populateVars(self, config):
        print("Populating OpenTofu Vars...")

        with open(VARS_PATH, 'w') as f:
            for var in REQ_VARS:
                val = config[var]
                var = var.replace('-', '_')
                f.write(f'{var} = "{val}"\n')
            f.write('H_HOSTNAME = "HPLMNTEST"\n')
            f.write('V_HOSTNAME = "VPLMNTEST"\n')

        print("Vars created successfully!")


    def runCommand(self, command):
        if len(command) > 1:
            commandName = f"{command[0]} {command[2]}"
        
        print(SEPARATOR+f"running: {commandName}"+SEPARATOR+"\n\n")
        res = run(command)

        if(res.returncode != 0):
            print(f"Command ({commandName}) presented an error [Status code: {res.returncode}]")
            return
        else:
            print(f"Command ({commandName}) was succesful")
