import jinja2

from json import loads

from .InfrastructureManager import InfrastructureManager
from .CommandLineManager import CommandLineManager


VARS_PATH = "vultr-opentofu/terraform.tfvars"

VARS = """vpc_v4_subnet_mask = "{{ vpc_v4_subnet_mask }}"
vpc_v4_subnet = "{{ vpc_v4_subnet }}"
vpc_region = "{{ vpc_v4_subnet_region }}"
vultr_api_key = "{{ vultr_api_key }}"
vultr_plan_id = "{{ vultr_plan_id }}"
user_ssh_key = "{{ user_ssh_key }}"
ansible_ssh_key = "{{ ansible_ssh_key }}"
boxes = {
{{ boxes }}
}
descriptions = { 
    {{ descriptions }} 
}
"""

BOX = """   {{ name }} = {
		"region": "{{ region }}",
		"hostname": "{{ hostname }}",
        "vpcs": [{{ vpcs }}]
	},
"""


class OpenTofu(InfrastructureManager, CommandLineManager):
    def __init__(self, config, cwd):
        super().__init__(config)

        self.cwd = cwd
        environment = jinja2.Environment()
        self.varsTemplate = environment.from_string(VARS)
        self.boxTemplate = environment.from_string(BOX)
    
    def callInfManager(self):
        self._populateVars()

        res = self.runCommand(["tofu", f"-chdir={self.cwd / 'vultr-opentofu'}", "init"]) 
        if res.returncode != 0:
            raise Exception("Error initiating OpenTofu")

        res = self.runCommand(["tofu", f"-chdir={self.cwd / 'vultr-opentofu'}", "apply", "-auto-approve", "-show-sensitive", "-json-into=tofu_out.json"]) 
        if res.returncode != 0:
            raise Exception("Error applying OpenTofu plan")

        print("\n\nSuccesfully created HPLMN and VPLMN machines!\n\n")

        self.readIPs()

        print("\n\n OpenTofu completed succesfully!")
    
    
    def destroy(self):
        res = self.runCommand(["tofu", f"-chdir={self.cwd / 'vultr-opentofu'}", "destroy"]) 
        if res.returncode != 0:
            raise Exception("Error initiating OpenTofu")


    def readIPs(self):
        with open(self.cwd / "vultr-opentofu" / "tofu_out.json") as f:
            outFile = f.read()
            
            print("Reading OpenTofu outputs...")
            # only parse last line where outputs are stores
            outJson = loads(outFile.split("\n")[-2])

            self.config["hplmn"]["public_ip"] = outJson["outputs"]["hplm_ip"]["value"]
            self.config["vplmn"]["public_ip"] = outJson["outputs"]["vplm_ip"]["value"]
        

    def _populateVars(self):
        print("Populating OpenTofu Vars...")

        with open(self.cwd / VARS_PATH, 'w') as f:
            try:
                vpcNum = len(self.config["peering"])
                boxNum = 2
                boxes = ["hplmn", "vplmn"]
                
                descriptions = "" 
                for i in range(vpcNum):
                    descriptions += f'vpc_link{i} = \"vpc for {self.config["peering"][i]}\",'
                
                instance = ""
                for i in range(boxNum):
                    box = boxes[i]

                    vpcs = ""
                    for j in range(vpcNum):
                        if box in self.config["peering"][j]:
                            vpcs += f'"vpc_link{j}",'
                    instance += self.boxTemplate.render(
                        name=box,
                        region=self.config["vultr"][f"{box}_region"],
                        hostname=self.config[box]["hostname"],
                        vpcs=vpcs
                    )

                    instance += "\n"
                
                content = self.varsTemplate.render(
                            descriptions=descriptions,
                            vpc_v4_subnet_mask=self.config["vultr"]["vpc"]["v4_subnet_mask"],
                            vpc_v4_subnet=self.config["vultr"]["vpc"]["v4_subnet"],
                            vpc_region=self.config["vultr"]["vpc"]["region"],
                            vultr_api_key=self.config["vultr"]["api_key"],
                            vultr_plan_id=self.config["vultr"]["plan_id"],
                            boxes=instance,
                            user_ssh_key=self.config["user_ssh_key"],
                            ansible_ssh_key=self.config["ansible_ssh_key"]
                )

                f.write(content)
            except AttributeError as e:
                print("Attribute Error while writing OpenTofu variables: " + e)

        print("Vars created successfully!")
            