import jinja2
import csv 
import sys

from datetime import datetime, timedelta
from yaml import dump
from json import loads
from pathlib import Path
from .CommandLineManager import CommandLineManager


DATE_FORMAT = "%H:%M:%S.%f"

TEST_COMMAND_TIMEOUT = 120
TEST_COMMAND_POLL_TIME = 10
DEFAULT_MODULE = "ansible.builtin.shell"

INVENTORY = """
---
all:
  vars:
    ansible_user: {{ ansible_user }}
  children: 
{{ hosts }}
"""

HOST = """    {{ name }}:  
      hosts:
        {{ name }}_node_1: 
          ansible_host: {{ public_ip }}
        {% if location == "local" %}
          ansible_port: {{ port }}
        {% endif %}

"""

GROUP_VARS = """interface_num: {{ interface_num }}
private_ip: 
{{ private_ip }}
mongodb: {{ mongodb }}
ogs: {{ ogs }}
{% if ogs %}
ogs_repo: {{ ogs_repo }}
ogs_version: {{ ogs_version }}
use_config_path: {{ use_config_path }}
{% if use_config_path %}
config_path: {{ config_path }}
{% else %}
config_repo: {{ config_repo }}
{% endif %}
use_hosts_path: {{ use_hosts_path }}
{% if use_hosts_path %}
hosts_path: {{ hosts_path }}
{% else %}
hosts_repo: {{ hosts_repo }}
{% endif %}
{% else %}
provisioning_script: {{ provisioning_script }}
{% endif %}
{% if location == "local" %}
use_netem: {{ use_netem }}
{% if use_netem %}
netem: {{  netem  }}
{% endif %}
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
        "path": "examples",
        "configs": ["5gc-no-scp-sepp1-999-70", "5gc-sepp3-315-010", "gnb-001-01-ue-315-010", "gnb-999-70-ue-001-01", "5gc-no-scp-sepp2-001-01", "5gc-tls-sepp1-999-70", "gnb-001-01-ue-999-70", "gnb-999-70-ue-315-010", "5gc-no-scp-sepp3-315-010", "5gc-tls-sepp2-001-01", "gnb-315-010-ue-001-01", "gnb-999-70-ue-999-70", "5gc-sepp1-999-70", "5gc-tls-sepp3-315-010", "gnb-315-010-ue-315-010", "5gc-sepp2-001-01", "gnb-001-01-ue-001-01", "gnb-315-010-ue-999-70"]
    },
    "open5gs": {
        "path": "open5gs",
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
        self.inventoryTemplate = environment.from_string(INVENTORY)
        self.hostTemplate = environment.from_string(HOST)
        self.groupvarsTemplate = environment.from_string(GROUP_VARS)


    def configure(self, writeInventory):
        if writeInventory:
            print("Writing Inventory!")
            with open(self.cwd / "ansible-setup" / "inventory" / "hosts.yaml", "w") as f:
                f.write(self._writeInventory())
            
        print("Writing Ansible variables!")
        self._writeVars()


    def setup(self, tags):
        try:
            command = ["ansible-playbook", "topssim_setup.yaml"]

            #if self.config["verbose"]: command.append("-v")
            if tags and len(tags) != 0:
                command.append("--tags")
                command.append(tags[0].replace(" ", ", "))
            res = self.runCommand(command, cwd=(self.cwd / "ansible-setup"))
            if res.returncode != 0:
                raise Exception("Ansible execution exited incorrectly!")
        except Exception as e:
            import traceback
            traceback.print_exc()


    def runFileCommands(self):
        """
        Results: 
        - logs
        - output
        - pcap
        - timings
        """
        now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        if len(self.run) > 0: 
            resultsPath = self.cwd / "results" / f"results-{now}" 
            timingPath = resultsPath / "timing"
            resultsPath.mkdir()
            timingPath.mkdir()
        else:
            return

        if self.config["capture_packets"]: 
            pcapWhere = ""
            if "pcap" not in self.run:
                pcapWhere = "all"
            else:
                for box in self.run["pcap"]:
                    pcapWhere += box + ", "
                pcapWhere = pcapWhere[:-2]
            
            self.runAdHocCommand(pcapWhere,
                                             "ansible.builtin.shell", 
                                            r"rm -f /tmp/capture.pcap & \
                                            setsid tcpdump -i any -w /tmp/capture.pcap -U >/dev/null 2>&1 & \
                                            echo $! >/tmp/tcpdump.pid", 
                                            "Start testing packet capture", capture_output=True, text=True, become=True)
        
        timing = []
        maxRepeats = 1
        for cmd in self.run:
            if "repeats" in cmd.keys():
                if int(cmd["repeats"]) > maxRepeats:
                    maxRepeats = int(cmd["repeats"])

        for cmd in self.run:
            cmdKeys = cmd.keys()
            script = False
            if "where" not in cmdKeys:
                continue

            if "cmd" in cmd:
                cmdTest = cmd["cmd"].split(".")
                if len(cmdTest) == 2 and cmdTest[0] in TESTS.keys() and cmdTest[1] in TESTS[cmdTest[0]]:
                    if "config" not in cmdKeys:
                        self._raiseMissingConfig(f"Configuration for test ({cmdTest}) was not provided")
                    else:
                        configTest = cmd["config"].split(".")
                        if len(configTest) == 2 and configTest[0] in CONFIGS.keys() and configTest[1] in CONFIGS[configTest[0]]["configs"]:
                            cmd["config"] = f'/root/open5gs/build/configs/{CONFIGS[configTest[0]]["path"]}/{configTest[1]}.yaml'

                    cmd["cmd"] = f'/root/open5gs/build/tests/{cmdTest[0]}/{cmdTest[0]} -c {cmd["config"]} {cmdTest[1]}'
                
                if "module" not in cmdKeys:
                    cmd["module"] = DEFAULT_MODULE
                
            
            if "script" in cmd:
                script = True
                cmd["module"] = "script"
                cmd["cmd"] = cmd["script"]

            if "timeout" not in cmdKeys:
                cmd["timeout"] = TEST_COMMAND_TIMEOUT
            if "poll" not in cmdKeys:
                cmd["poll"] = TEST_COMMAND_POLL_TIME

            repeatRun = ("repeats" in cmdKeys)
            if repeatRun: 
                repeats = cmd["repeats"]
                output_dir = resultsPath / "output"
                if self.config["write_test_output"]: output_dir.mkdir(parents=True, exist_ok=True)
            else: 
                repeats = 1
            
            name = f"\n[blue bold]{cmd['where'].upper()}:[/] executing [dark_orange italic]{cmd['cmd']}[/]\n"
            
            agg = {}
            timestamps = {}
            finished = True
            try:
                execScript = Path()
                if repeatRun and script:
                    scriptPath = Path(cmd["cmd"])
                    with open(scriptPath, "r") as f:
                        script = f.readlines()
                        # empty script
                        if len(script) == 0: continue

                        if script[0][0] != "#" and scriptPath.suffix == ".sh":
                            script.insert(0, "#!/bin/bash\n")

                        script.insert(1, "start=$(date +%s.%N)\n")
                        script.append("end=$(date +%s.%N)\n")
                        script.append('echo "__TIME__=$(echo "$end - $start" | bc)"')

                        execScript = self.cwd / Path("Managers/tmp") / scriptPath.name
                        with open(execScript, "w") as modifiedScript:
                            modifiedScript.writelines(script)
                else:
                    execScript = cmd["cmd"]

                for r in range(repeats):
                    if not script:
                        res = self.runAdHocCommand(cmd["where"], cmd["module"], cmd["cmd"], name, B=cmd['timeout'], P=cmd['poll'], capture_output=repeatRun, text=repeatRun)
                    else:
                        res = self.runAdHocCommand(cmd["where"], cmd["module"], str(execScript), name, capture_output=repeatRun, text=repeatRun)
                    
                    if res.returncode != 0: 
                        self.consolePrint("[red bold] Error [/] presented by command: " + cmd["cmd"])
                        finished = False
                        break

                    clIdx = 0
                    if repeatRun:
                        stdout = res.stdout.split(" => ")
                        for i in range(1, len(stdout)):
                            vm = stdout[i-1][clIdx:].split(" | ")[0].split("\n")[-1]
                            clIdx = stdout[i].rfind("}")

                            if not script: 
                                delta = loads(stdout[i][:clIdx+1])["delta"]
                                h, m, s = delta.split(":")
                            else: 
                                time = loads(stdout[i][:clIdx+1])['stdout_lines'][-1]
                                if "__TIME__" not in time: raise Exception("__TIME__ indicator was not found in script execution")
                                h, m, s = 0,0,float(time.split('=')[-1])

                            timeSec = timedelta(
                                hours=int(h),
                                minutes=int(m),
                                seconds=float(s)
                            ).total_seconds()
                            agg[vm] = timeSec if (vm not in agg.keys()) else (agg[vm] + timeSec)

                            cmdID = vm + "_" + cmd["cmd"]
                            if vm not in timestamps.keys(): timestamps[vm] = {} 
                            timestamps[vm]["command"] = cmdID
                            timestamps[vm]["rep" + str(r)] = timeSec
                        
                        if self.config["write_test_output"]:
                            with open(output_dir / "output.txt", "a") as f:
                                f.write(res.stdout)
            except Exception as e:
                print(e)
                sys.exit(1)
            finally:
                if script: Path(execScript).unlink(missing_ok=True)

            if repeatRun and finished:
                self.consoleRule(f"\n[bold]Executed [/]: [dark_orange italic]{cmd['cmd']}[/]")
                self.consolePrint(f"[spring_green4]Repetitions [/]: {repeats}\nAverage execution times were:")
                for vm in agg:
                    self.consolePrint(f"[spring_green4] {vm} [/]: {(agg[vm]/repeats):.4f} seconds")

                    for i in range(maxRepeats-repeats):
                        timestamps[vm]["rep" + str(repeats+i)] = "NA"
            
            for time in timestamps:
                timing.append(timestamps[time])

            if "logs" not in cmdKeys:
                continue 
            elif finished:
                self.getLogs(cmd["where"], cmd["logs"])
        
        with open(timingPath / "timing.csv", "a", newline='') as timingCSV:
            fieldnames = []
            fieldnames.append("command")

            for i in range(maxRepeats):
                fieldnames.append("rep" + str(i))
                
            writer = csv.DictWriter(timingCSV, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(timing)

        if self.config["capture_packets"]: 
            pcap_dir = resultsPath / "pcap" 
            pcap_dir.mkdir(parents=True, exist_ok=True)
            
            self.runAdHocCommand("all", 
                            "ansible.builtin.shell", 
                            r"kill -2 $(cat /tmp/tcpdump.pid) && sleep 2 && rm -f /tmp/tcpdump.pid", 
                            "Kill tcpdump process", capture_output=True, text=True)

            self.runAdHocCommand("all", 
                            "ansible.builtin.fetch", 
                            str(f"src=/tmp/capture.pcap dest={pcap_dir}/{{{{ inventory_hostname }}}}_capture.pcap flat=yes"), 
                            "Fetch captured packets (.pcap)", capture_output=True, text=True)

        if self.config["copy_logs"]:
            logs_dir = resultsPath / "logs" 
            logs_dir.mkdir(parents=True, exist_ok=True)

            logsWhere = ""
            for box in self.config["ogs_boxes"]:
                logsWhere += box + ", "
            logsWhere = logsWhere[:-2]

            res = self.runAdHocCommand(logsWhere, 
                                "ansible.builtin.shell", 
                                "find /root/open5gs/install/var/log/open5gs -maxdepth 1 -type f", 
                                "", 
                                capture_output=True, 
                                text=True)

            stdout = res.stdout.split("\n")
            if "Using" in stdout[0]:
                stdout = stdout[1:]
            
            self.consoleRule("Copying Open5GS Logs after testing")
            box = ""
            for i in range(len(stdout)):
                if ">>" in stdout[i]:
                    box = stdout[i].split(" | ")[0]
                    self.consolePrint(f"Copying the logs from {box.upper()}")
                # ignore non-log files
                elif "log" not in stdout[i]:
                    continue
                else:
                    func = stdout[i].split("/")[-1].split(".")[0]
                    self.consolePrint(f"Copying {func} logs...")
                    self.fetchLogs(func, logs_dir, box)
            

    def fetchLogs(self, func, logs_dir, where="all"):
        name=f"\nCopying [dark_orange italic]{func.upper()}[/] logs\n"
        dest = logs_dir / f"{{{{ inventory_hostname }}}}/{func}.log"
        command=f"src=/root/open5gs/install/var/log/open5gs/{func}.log dest={dest} flat=yes"
        self.runAdHocCommand(where, "ansible.builtin.fetch", command, name, capture_output=True, text=True, ruleAndResult=False)


    def getLogs(self, where, components, lines=10):
        for func in components:
            numLines = lines
            if type(func) is dict:
                numLines = func["lines"]
                f = func["func"]
            else:
                f = func

            name=f"\nLast [plum1]{numLines}[/] lines of [dark_orange]{f.upper()}[/] logs from [blue bold]{where.upper()}:[/]"
            command=f"tail -n {str(numLines)} /root/open5gs/install/var/log/open5gs/{f}.log"
            self.runAdHocCommand(where, "ansible.builtin.shell", command, name, titleJustify="left")


    def runAdHocCommand(self, where, module, cmd, name, B=None, P=None, cwd=None, titleJustify="center", capture_output=False, text=False, become=False, ruleAndResult=True):
        command = ["ansible", where, "-m", module, "-a", cmd]
        if B and B != -1:
            command.append("-B")
            command.append(str(B))
        if P and P != -1:
            command.append("-P")
            command.append(str(P))
        if not cwd:
            cwd = self.cwd / "ansible-setup"
        if become:
            command.append("-b")
        #if self.config["verbose"]: command.append("-v")
        return self.runCommand(command, cwd=cwd, name=name, titleJustify=titleJustify, capture_output=capture_output, text=text, ruleAndResult=ruleAndResult)


    def _writeVars(self):
        use_path = {"use_config_path": True, "use_hosts_path": True}
        netemConfig = ""
        for box in self.config["boxes"]:
            with open(self.cwd / "ansible-setup" / "inventory" / "group_vars" / f"{box}.yaml", "w") as f:
                for network in self.config["boxes"][box]["private_ip"]:
                    for i in range(len(self.config["peering"])):
                        if network == self.config["peering"][i]["name"]:
                            self.config["boxes"][box]["private_ip"][network]["subnet_mask"] = self.config["peering"][i]["v4_subnet_mask"]
                            break
                privateIP = dump(self.config["boxes"][box]["private_ip"])

                privateIP = "  " + privateIP
                for i in range(len(privateIP)):
                    if privateIP[i] == "\n":
                        privateIP = privateIP[:i+1] + "  " + privateIP[i+1:]

                ogs = True
                if box not in self.config["ogs_boxes"]: 
                    ogs = False
                else:
                    res = self.runCommand(["git", "ls-remote", self.config["boxes"][box]["ogs"]["repo"]], capture_output=True, text=True) 
                    if res.returncode != 0:
                        self.__raiseWrongConfig("ogs_repo")
                    else:
                        print("Open5GS repo was found!")
                    
                    for c in [["config_path", "config_repo"], ["hosts_path", "hosts_repo"]]:
                        if self.config["boxes"][box][c[0]] == "":
                            res = self.runCommand(["git", "ls-remote", self.config["boxes"][box][c[1]]], capture_output=True, text=True) 
                            if res.returncode != 0:
                                self.__raiseWrongConfig(box + c[1])
                            else:
                                print(box + c[1] + " was found!")
                            
                            use_path[f"use_{c[0].split('_')[0]}_path"] = False
                
                if self.config["location"].lower() == "local" and \
                "use_netem" in self.config["boxes"][box]["vagrant"].keys() and \
                self.config["boxes"][box]["vagrant"]["use_netem"]:
                    netemConfig = dump(self.config["boxes"][box]["vagrant"]["netem"])
                
                groupvars = self.groupvarsTemplate.render(
                    interface_num=len(self.config["boxes"][box]['private_ip']),
                    private_ip=privateIP,
                    mongodb=self.config["boxes"][box]["mongodb"],
                    ogs=ogs,
                    ogs_repo=self.config["boxes"][box]["ogs"]["repo"],
                    ogs_version=self.config["boxes"][box]["ogs"]["version"],
                    use_config_path=use_path["use_config_path"],
                    config_repo=self.config["boxes"][box]["config_repo"],
                    config_path=self.config["boxes"][box]["config_path"],
                    use_hosts_path=use_path["use_hosts_path"],
                    hosts_repo=self.config["boxes"][box]["hosts_repo"],
                    hosts_path=self.config["boxes"][box]["hosts_path"],
                    provisioning_script=self.config["boxes"][box]["provisioning_script"],
                    use_netem=self.config["boxes"][box]["vagrant"]["use_netem"],
                    netem=netemConfig,
                    location=self.config["location"]
                )

                f.write(groupvars)

        with open(self.cwd / "ansible-setup" / "roles" / "Open5GS Config" / "vars" / "main.yml", "w") as f:
            f.write("provider: " + self.config["provider"] + "\n")

        '''
        When a Vultr machine is created its /etc/hosts file has this information:
        # Your system has configured 'manage_etc_hosts' as True.
        # As a result, if you wish for changes to this file to persist
        # then you will need to either
        # a.) make changes to the master file in /etc/cloud/templates/hosts.debian.tmpl
        This var makes it so that the hosts file is written at that address
        '''
                
        if "create_services" not in self.config.keys():
            self.config["create_services"] = "true"
        with open(self.cwd / "ansible-setup" / "vars" / "vars.yaml", "w") as f:
            f.write("---\n")
            f.write("test_command_timeout: "  + str(TEST_COMMAND_TIMEOUT) + "\n")
            f.write("create_services: "  + f'\"{self.config["create_services"]}\"' + "\n")


    def _writeInventory(self):
        if self.config["location"] == "cloud":
            user = "root"
        else:
            user = "vagrant"
        
        hosts = ""
        for box in self.config["boxes"]:
            host = self.hostTemplate.render(
                name=box,
                public_ip=self.config["boxes"][box]["public_ip"],
                location=self.config["location"],
                port=self.config["boxes"][box]["port"]
            )
            hosts += host

        content = self.inventoryTemplate.render(
                hosts=hosts,
                ansible_user=user
                )

        return content


    def __raiseWrongConfig(self, par):
        errorMsg = f"Required paramater was provided incorrectly: {par}"
        raise Exception(errorMsg)
