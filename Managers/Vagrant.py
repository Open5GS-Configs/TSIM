import yaml
import jinja2

from .InfrastructureManager import InfrastructureManager
from .CommandLineManager import CommandLineManager


VARS_PATH = "vagrant-config/vars.yaml"

VARS = """box:
    memory: {{ memory }}
    disk: {{ disk }}
    cpu: {{ cpu }}
    ansible_tags: {{ ansible_tags }}
    ansible_ssh_key: {{ ansible_ssh_key }}
    user_ssh_key: {{ user_ssh_key }}

hplmn:
    private_ip: {{ h_ip }}
    hostname: "{{ h_hostname }}"
    use_config_path: {{ h_use_config_path }}
  {% if h_use_config_path %}
    config_path: {{ h_config_path }}
  {% else %}
    config_repo: {{ h_config_repo }}
  {% endif %}
    use_hosts_path: {{ h_use_hosts_path }}
  {% if h_use_hosts_path %}
    hosts_path: {{ h_hosts_path }}
  {% else %}
    hosts_repo: {{ h_hosts_repo }}
  {% endif %}
  

vplmn:
    private_ip: {{ v_ip }}
    hostname: "{{ v_hostname }}"
    use_config_path: {{ v_use_config_path }}
  {% if v_use_config_path %}
    config_path: {{ v_config_path }}
  {% else %}
    config_repo: {{ v_config_repo }}
  {% endif %}
    use_hosts_path: {{ v_use_hosts_path }}
  {% if v_use_hosts_path %}
    hosts_path: {{ v_hosts_path }}
  {% else %}
    hosts_repo: {{ v_hosts_repo }}
  {% endif %}
"""


class Vagrant(InfrastructureManager, CommandLineManager):
    def __init__(self, config):
        super().__init__(config)
        environment = jinja2.Environment()
        self.template = environment.from_string(VARS)


    def callInfManager(self):
        self.populateVars()
        
        if self.runCommand(["vagrant", "up"], cwd="vagrant-config").returncode != 0:
            raise Exception("Error applying Vagrant plan") 

        print("\n\nSuccesfully created HPLMN and VPLMN machines!\n\n")
        
        res = self.runCommand(["vagrant", "ssh-config", "--machine-readable"], noOutput=True, cwd="vagrant-config")
        if res.returncode != 0:
            raise Exception("Error collecting VM IPs")
        
        self.extractIPs(res)

        print("\n\n Vagrant completed succesfully!")


    def populateVars(self):
        print("Populating Vagrant Vars...")

        content = self.template.render(
            memory=self.config["vagrant"]["ram"],
            disk=self.config["vagrant"]["disk"],
            cpu=self.config["vagrant"]["cpu"],
            ansible_tags=self.config["ansible_tags"],
            ansible_ssh_key=self.config["ansible_ssh_key"],
            user_ssh_key=self.config["user_ssh_key"],
            h_ip=self.config["hplmn"]["private_ip"],
            h_hostname="HPLMNTEST",
            h_use_config_path=(self.config["hplmn"]["config_path"] != None),
            h_config_path=self.config["hplmn"]["config_path"],
            h_config_repo=self.config["hplmn"]["config_repo"],
            h_use_hosts_path=(self.config["hplmn"]["hosts_path"] != None),
            h_hosts_path=self.config["hplmn"]["hosts_path"],
            h_hosts_repo=self.config["hplmn"]["hosts_repo"],
            v_ip=self.config["vplmn"]["private_ip"],
            v_hostname="VPLMNTEST",
            v_use_config_path=(self.config["vplmn"]["config_path"] != None),
            v_config_path=self.config["vplmn"]["config_path"],
            v_config_repo=self.config["vplmn"]["config_repo"],
            v_use_hosts_path=(self.config["vplmn"]["hosts_path"] != None),
            v_hosts_path=self.config["vplmn"]["hosts_path"],
            v_hosts_repo=self.config["vplmn"]["hosts_repo"]
        )

        with open(VARS_PATH, 'w') as f:
            f.write(content)
        
        print("Vars created successfully!")


    def provision(self):
        res = self.runCommand(["vagrant", "provision"], cwd="vagrant-config") 
        if res.returncode != 0:
            raise Exception("Error in provisioning with Vagrant: " + res.stderr)


    def destroy(self):
        res = self.runCommand(["vagrant", "destroy"], cwd="vagrant-config") 
        if res.returncode != 0:
            raise Exception("Error destroying Vagrant VMs: " + res.stderr)


    def extractIPs(self, res):
        plmn = ""
        ip = ""
        port = ""

        for t in res.stdout.split("\n"):
            data = t.split(",")
            if "ssh-config" in data:
                for c in data[3].split("\\n"):
                    sshConfig = c.split()
                    if "Host" in sshConfig:
                        plmn = sshConfig[1]
                    if "HostName" in sshConfig:
                        ip = sshConfig[1]
                    if "Port" in sshConfig:
                        port = sshConfig[1]
                self.config[plmn]["public_ip"] = ip
                self.config[plmn]["port"] = port
                print(f"SSH Config: {plmn} {ip} {port}")

