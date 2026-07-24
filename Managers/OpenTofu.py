import jinja2

from json import loads

from .InfrastructureManager import InfrastructureManager
from .CommandLineManager import CommandLineManager


VARS_PATH = "vultr-opentofu/terraform.tfvars"

VARS = """vultr_api_key = "{{ vultr_api_key }}"
user_ssh_key = "{{ user_ssh_key }}"
ansible_ssh_key = "{{ ansible_ssh_key }}"
boxes = {
{{ boxes }}
}
peerings = { 
{{ peerings }} 
}
"""

PEERING = """   {{ name }} = {
        "description": {{ description }}
		"region": "{{ region }}",
		"v4_subnet": "{{ v4_subnet }}",
        "v4_subnet_mask": "{{ v4_subnet_mask }}"
	},
"""

BOX = """   {{ name }} = {
		"region": "{{ region }}",
		"hostname": "{{ hostname }}",
        "plan_id": "{{ plan_id }}"
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
        self.peeringTemplate = environment.from_string(PEERING)
    
    def callInfManager(self):
        self._populateVars()

        res = self.runCommand(["tofu", f"-chdir={self.cwd / 'vultr-opentofu'}", "init"]) 
        if res.returncode != 0:
            raise Exception("Error initiating OpenTofu")

        res = self.runCommand(["tofu", f"-chdir={self.cwd / 'vultr-opentofu'}", "apply", "-auto-approve", "-show-sensitive", "-json-into=tofu_out.json"]) 
        if res.returncode != 0:
            raise Exception("Error applying OpenTofu plan")

        print("\n\nSuccesfully created the following machines:\n")
        for box in self.config["boxes"]: print(f"- {box.upper()}") 
        print("\n\n")

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

            for box in self.config["boxes"]:
                self.config["boxes"][box]["public_ip"] = outJson["outputs"]["instance_ips"]["value"][box]
        

    def _populateVars(self):
        print("Populating OpenTofu Vars...")

        with open(self.cwd / VARS_PATH, 'w') as f:
            try:
                vpcNum = len(self.config["peering"])
                boxes = list(self.config["boxes"].keys())
                boxNum = len(boxes)
                
                peerings = "" 
                for i in range(vpcNum):
                    if "description" not in self.config["peering"][i]:
                        self.config["peering"][i]["description"] = f'vpc for {self.config["peering"][i]["members"]}'
                    self.config["peering"][i]["description"] = f'\"{self.config["peering"][i]["description"]}\"'

                    peerings += self.peeringTemplate.render(
                        description=self.config["peering"][i]["description"],
                        name=self.config["peering"][i]["name"],
                        v4_subnet=self.config["peering"][i]["v4_subnet"],
                        v4_subnet_mask=self.config["peering"][i]["v4_subnet_mask"],
                        region=self.config["peering"][i]["region"]
                    )
                    peerings += '\n'

                instance = ""
                for box in boxes:
                    vpcs = ""
                    for j in range(vpcNum):
                        if box in self.config["peering"][j]["members"]:
                            vpcs += f'\"{self.config["peering"][j]["name"]}\",'
                    
                    instance += self.boxTemplate.render(
                        name=box,
                        region=self.config["boxes"][box]["vultr"]["region"],
                        hostname=self.config["boxes"][box]["hostname"],
                        plan_id=self.config["boxes"][box]["vultr"]["plan_id"],
                        vpcs=vpcs
                    )

                    instance += "\n"
                
                content = self.varsTemplate.render(
                            peerings=peerings,
                            vultr_api_key=self.config["vultr_api_key"],
                            boxes=instance,
                            user_ssh_key=self.config["user_ssh_key"],
                            ansible_ssh_key=self.config["ansible_ssh_key"]
                )

                f.write(content)
            except AttributeError as e:
                print("Attribute Error while writing OpenTofu variables: " + e)

        print("Vars created successfully!")
            
