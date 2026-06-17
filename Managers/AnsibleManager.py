import jinja2

from pathlib import Path
from .CommandLineManager import CommandLineManager


TEST_COMMAND_TIMEOUT = 120
TEST_COMMAND_POLL_TIME = 10
DEFAULT_MODULE = "ansible.builtin.shell"

INVENTORY = """
---
all:
  vars:
    ansible_user: {{ ansible_user }}
  children: 
    hplmn:  
      hosts:
        hplmn_node_1: 
          ansible_host: {{ hplmn_public_ip }}
        {% if provider == "local" %}
          ansible_port: {{ hplmn_port }}
        {% endif %}
    vplmn:  
      hosts:
        vplmn_node_1:
          ansible_host: {{ vplmn_public_ip }}
        {% if provider == "local" %}
          ansible_port: {{ vplmn_port }}
        {% endif %}
"""

VALID_FUNC = ["amf", "bsf", "mme", "nssf", "pcrf", "sepp1", "sepp2", "sgwu", "tls", "udr", "ausf", "hss", "nrf", "pcf", "scp", "sgwc", "smf", "udm", "upf"]

TESTS = {
    "registration": ["abts-main", "crash-test", "ecc-test", "guti-test", "idle-test", "multi-ue-test", "simple-test", "auth-test", "dereg-test", "gmm-status-test", "identity-test", "reset-test", "ue-context-test"],
    "310014": ["abts-main", "epc-test"],
    "app": ["5gc-init", "app-init", "epc-init"],
    "af": ["af-sm", "init", "nnrf-handler", "sbi-path", "event", "nbsf-handler", "npcf-handler", "context", "local", "nbsf-build", "npcf-build"],
    "attach": ["abts-main", "crash-test", "guti-test", "issues-test", "reset-test", "simple-test", "auth-test", "emm-status-test", "idle-test", "s1setup-test", "ue-context-test"],
    "common": ["application", "emm-handler", "gmm-build", "gsm-handler", "nas-path", "ngap-handler", "s1ap-handler", "sgsap-build", "context", "esm-build", "gmm-handler", "gtpu", "nas-security", "ngap-path", "s1ap-path", "emm-build", "esm-handler", "gsm-build", "nas-encoder", "ngap-build", "s1ap-build", "sctp"],
    "core": ["abts-main", "hash-test", "memory-test", "poll-test", "rbtree-test", "thread-test", "tlv-test", "conv-test", "list-test", "pool-test", "socket-test", "timer-test", "uuid-test", "fsm-test", "log-test", "pkbuf-test", "queue-test", "strings-test", "time-test"],
    "crypt": ["abts-main", "aes-test", "base64-test", "ecies-test", "sha-test"],
    "csfb": ["abts-main", "mo-idle-test", "mt-active-test", "mt-sms-test", "crash-test", "mo-active-test", "mo-sms-test", "mt-idle-test", "tau-test"],
    "fuzzing": ["nas-message-fuzz", "gtp-message-fuzz"],
    "handover": ["5gc-n2-test", "5gc-xn-test", "abts-main", "epc-s1-test", "epc-x2-test"],
    "sctp": ["sctp-test"],
    "slice": ["different-dnn-test", "paging-test", "same-dnn-test"],
    "transfer": ["abts-error-main", "abts-main", "ue-context-transfer-error-case-test", "ue-context-transfer-test"],
    "unit": ["abts-main", "gtp-message-test", "nas-message-test", "proto-message-test", "sbi-message-test", "crash-test", "ngap-message-test", "s1ap-message-test", "security-test"],
    "volte": ["abts-main", "cx-test", "diameter-rx-path", "rx-test", "simple-test", "bearer-test", "diameter-cx-path", "session-test", "test-fd-path", "video-test"],
    "vonr": ["abts-main", "af-test", "qos-flow-test", "session-test", "simple-test", "video-test"]
}

CONFIGS = {
    "configs": {
        "path": "",
        "configs": ["310014", "sample", "volte", "attach", "non3gpp", "slice", "transfer-error-case", "vonr", "csfb", "srsenb", "transfer"]
    },
    "examples": {
        "path": "examples/",
        "configs": ["5gc-no-scp-sepp1-999-70", "5gc-sepp3-315-010", "gnb-001-01-ue-315-010", "gnb-999-70-ue-001-01", "5gc-no-scp-sepp2-001-01", "5gc-tls-sepp1-999-70", "gnb-001-01-ue-999-70", "gnb-999-70-ue-315-010", "5gc-no-scp-sepp3-315-010", "5gc-tls-sepp2-001-01", "gnb-315-010-ue-001-01", "gnb-999-70-ue-999-70", "5gc-sepp1-999-70", "5gc-tls-sepp3-315-010", "gnb-315-010-ue-315-010", "5gc-sepp2-001-01", "gnb-001-01-ue-001-01", "gnb-315-010-ue-999-70"]
    },
    "open5gs": {
        "path": "open5gs/",
        "configs": ["amf", "bsf", "hss", "nrf", "pcf", "scp", "sepp2", "sgwu", "udr", "ausf", "mme", "nssf", "pcrf", "sepp1", "sgwc", "smf", "udm", "upf"]
    }
}


class AnsibleManager(CommandLineManager):

    def __init__(self, config, run, cwd):
        super().__init__()

        self.config = config
        self.run = run
        self.cwd = cwd

        environment = jinja2.Environment()
        self.template = environment.from_string(INVENTORY)


    def configure(self, writeInventory):
        if writeInventory:
            print("Writing Inventory!")
            with open(self.cwd / "ansible-setup" / "inventory" / "hosts.yaml", "w") as f:
                f.write(self._writeInventory())
            
        print("Writing Ansible variables!")
        self._writeVars()


    def setup(self, tags):
        try:
            command = ["ansible-playbook", "topssim_setup.yaml", "-vv"]
            if tags and len(tags) != 0:
                command.append("--tags")
                command.append(tags[0].replace(" ", ", "))
            res = self.runCommand(command, cwd=(self.cwd / "ansible-setup"))
        except Exception as e:
            import traceback
            traceback.print_exc()
        #if res.returncode != 0:
        #    raise Exception("Ansible Playbook presented an error!")


    def runFileCommands(self):
        for cmd in self.run:
            cmdKeys = cmd.keys()
            cmdTest = cmd["cmd"].split(".")

            if len(cmdTest) == 2 and cmdTest[0] in TESTS.keys() and cmdTest[1] in TESTS[cmdTest[0]]:
                if "config" not in cmdKeys:
                    self._raiseMissingConfig(f"Configuration for test ({cmdTest}) was not provided")
                else:
                    configTest = cmd["config"].split(".")
                    if len(configTest) == 2 and configTest[0] in CONFIGS.keys() and configTest[1] in CONFIGS[configTest[0]]["configs"]:
                        cmd["config"] = f'/root/open5gs/build/configs/{CONFIGS[configTest[0]]["path"]}/{configTest[1]}.yaml'

                cmd["cmd"] = f'/root/open5gs/build/tests/{cmdTest[0]}/{cmdTest[0]} -c {cmd["config"]} {cmdTest[1]}'

            if "timeout" not in cmdKeys:
                cmd["timeout"] = TEST_COMMAND_TIMEOUT
            if "module" not in cmdKeys:
                cmd["module"] = DEFAULT_MODULE
            if "poll" not in cmdKeys:
                cmd["poll"] = TEST_COMMAND_POLL_TIME

            name = f"\n[blue bold]{cmd['where'].upper()}:[/] executing [dark_orange italic]{cmd['cmd']}[/]\n"
            self.runAdHocCommand(cmd["where"], cmd["module"], cmd["cmd"], name, B=cmd['timeout'], P=cmd['poll'])
            
            if "logs" not in cmdKeys:
                continue 
                
            self.getLogs(cmd["where"], cmd["logs"])
        
        if self.config["copy_logs"]:
            for func in VALID_FUNC:
                name=f"\nCopying [dark_orange italic]{func}[/] logs\n"
                command=f"src=/root/open5gs/install/var/log/open5gs/{func}.log dest={{{{ playbook_dir }}}}/logs-{{{{ inventory_hostname }}}}/{func}.log"
                self.runAdHocCommand("all", "ansible.builtin.fetch", command, name)


    def getLogs(self, where, components, lines=10):
        for func in components:
            numLines = lines
            if type(func) is dict:
                numLines = func["lines"]
                f = func["func"]
            else:
                f = func
            if f in VALID_FUNC:
                name=f"\nLast [plum1]{numLines}[/] lines of [dark_orange]{f.upper()}[/] logs from [blue bold]{where.upper()}:[/]"
                command=f"tail -n {str(numLines)} /root/open5gs/install/var/log/open5gs/{f}.log"
                self.runAdHocCommand(where, "ansible.builtin.shell", command, name, titleJustify="left")
            else:
                self.__raiseWrongConfig(f"{f} is not a valid Open5GS function")


    def runAdHocCommand(self, where, module, cmd, name, B=None, P=None, cwd=None, titleJustify="center"):
        command = ["ansible", where, "-m", module, "-a", cmd]
        if B and B != -1:
            command.append("-B")
            command.append(str(B))
        if P and P != -1:
            command.append("-P")
            command.append(str(P))
        if not cwd:
            cwd = self.cwd / "ansible-setup"
        command.append("-v")
        self.runCommand(command, cwd=cwd, name=name, titleJustify=titleJustify)


    def _writeVars(self):
        res = self.runCommand(["git", "ls-remote", self.config["ogs"]["repo"]], noOutput=True) 
        if res.returncode != 0:
            self.__raiseWrongConfig("ogs_repo")
        else:
            print("Open5GS repo was found!")
        
        with open(self.cwd / "ansible-setup" / "roles" / "Open5GS Setup" / "vars" / "main.yml", "w") as f:
            f.write(f"ogs_repo: {self.config['ogs']['repo']}\n")
            f.write(f"ogs_version: {self.config['ogs']['version']}")
        
        for plmn in ["hplmn", "vplmn"]:
            with open(self.cwd / "ansible-setup" / "inventory" / "group_vars" / f"{plmn}.yaml", "w") as f:
                f.write(f"private_ip: {self.config[plmn]['private_ip']}\n")
                
                for c in [["config_path", "config_repo"], ["hosts_path", "hosts_repo"]]:
                    if self.config[plmn][c[0]] != None:
                        f.write(f"use_{c[0].split('_')[0]}_path: true\n")
                        f.write(f"{c[0]}: {self.config[plmn][c[0]]}\n")
                    else:
                        res = self.runCommand(["git", "ls-remote", self.config[plmn][c[1]]], noOutput=True) 
                        if res.returncode != 0:
                            self.__raiseWrongConfig(plmn + c[1])
                        else:
                            print(plmn + c[1] + " was found!")
                
                        f.write(f"use_{c[0].split('_')[0]}_path: false\n")
                        f.write(f"{c[1]}: {self.config[plmn][c[1]]}\n")

        '''
        When a Vultr machine is created its /etc/hosts file has this information:
        # Your system has configured 'manage_etc_hosts' as True.
        # As a result, if you wish for changes to this file to persist
        # then you will need to either
        # a.) make changes to the master file in /etc/cloud/templates/hosts.debian.tmpl
        This var makes it so that the hosts file is written at that address
        '''
        with open(self.cwd / "ansible-setup" / "roles" / "Open5GS Config" / "vars" / "main.yml", "w") as f:
            with open(self.cwd / "ansible-setup" / "roles" / "Netplan Config" / "vars" / "main.yml", "w") as g:
                if self.config["provider"].lower() == "vultr":
                    self.config["provider"] = "vultr"
                    self.config["dest_netplan_path"] = "/etc/netplan/50-cloud-init.yaml"
                    
                    g.write("vpc_v4_subnet_mask: "  + f'\"{self.config["vultr"]["vpc"]["v4_subnet_mask"]}\"' + "\n")
                else:
                    self.config["dest_netplan_path"] = "/etc/netplan/50-vagrant.yaml"
                
                f.write("provider: " + self.config["provider"])
                
                g.write("dest_netplan_path: "  + f'\"{self.config["dest_netplan_path"]}\"' + "\n")
                
        if "create_services" not in self.config.keys():
            self.config["create_services"] = "true"
        with open(self.cwd / "ansible-setup" / "vars" / "vars.yaml", "w") as f:
            f.write("---\n")
            f.write("vplmn_test_script: "  + f'{self.config["vplmn"]["test_script"]}' + "\n")
            f.write("hplmn_test_script: "  + f'{self.config["hplmn"]["test_script"]}' + "\n")
            f.write("test_command_timeout: "  + str(TEST_COMMAND_TIMEOUT) + "\n")
            f.write("create_services: "  + f'\"{self.config["create_services"]}\"' + "\n")


    def _writeInventory(self):
        if self.config["location"] == "cloud":
            self.config["hplmn"]["ip"] = 22
            self.config["hplmn"]["ip"] = 22
            user = "root"
        else:
            user = "vagrant"

        content = self.template.render(
                hplmn_public_ip=self.config["hplmn"]["public_ip"],
                hplmn_port=self.config["hplmn"]["port"],
                vplmn_public_ip=self.config["vplmn"]["public_ip"],
                vplmn_port=self.config["vplmn"]["port"],
                provider=self.config["location"],
                ansible_user=user
                )

        return content


    def __raiseWrongConfig(self, par):
        errorMsg = f"Required paramater was provided incorrectly: {par}"
        raise Exception(errorMsg)