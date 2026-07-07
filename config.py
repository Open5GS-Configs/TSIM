import yaml
import argparse 

from Managers.CommandLineManager import CommandLineManager


class Config(CommandLineManager):
    def __init__(self):    
        '''
        This part of the code compiles and assimilates the command line arguments 
        and the configuration coming from the configuration file. The values given
        through the command line are mapped to the same structure than the ones in
        the config file, so that they can be used the same way everywhere.

        The command line arguments take precedence over the config file.
        '''
        super().__init__()

        self.parser = argparse.ArgumentParser(description="Open5Gs testing environment \
                                                    setup for the TOPSSIM project", 
                                                    argument_default=argparse.SUPPRESS)

        self.addArguments()

        self.args = self.parser.parse_args()
    

    def createConfig(self):
        config = {}
        if hasattr(self.args, "config"):
            config = self.parseConfig(self.args.config, config)
        else:
            print("Config file was not passed!")
        run = {}
        if hasattr(self.args, "run"):
            run = self.parseRun(self.args.run, run)
        else:
            print("Run file was not passed!")

        config = self.apply_cli_overrides(config, self.args)

        for flag in ("destroy", "restart", "ansible", "vultr_regions", "vultr_plans", "readme", "test", "up", "ssh", "ad_hoc", "log", "tui"):
            if hasattr(self.args, flag):
                config[flag] = getattr(self.args, flag)

        return config, run


    def parseRun(self, runFile, run):
        self.consoleRule("Reading Run File")
        try:
            f = open(runFile, 'r')
        except FileNotFoundError:
            print(f"Inputted config file was not found: {runFile}")
        else:
            with f:
                run = yaml.load(f, Loader=yaml.SafeLoader)
        print("\nFile read succesfully!")

        return run


    def parseConfig(self, configFile, config):
        self.consoleRule("Reading Config File")
        try:
            f = open(configFile, 'r')
        except FileNotFoundError:
            print(f"Inputted config file was not found: {configFile}")
        else:
            with f:
                config = yaml.load(f, Loader=yaml.SafeLoader)
        print("\nFile read succesfully!")

        return config


    def set_nested(self, d, path, value):
        cur = d
        for key in path[:-1]:
            cur = cur.setdefault(key, {})
        cur[path[-1]] = value


    def apply_cli_overrides(self, config, args):
        # Map CLI argument names to nested config paths
        overrides = {
            "tui": ("tui",),
            "provider": ("provider",),
            "user_ssh_key": ("user_ssh_key",),
            "create_services": ("create_services",),
            "copy_logs": ("copy_logs",),
            "capture_packets": ("capture_packets",),
            "write_test_output": ("write_test_output",),
            "w": ("where",),
            "m": ("module",),
            "a": ("arguments",),
            "B": ("B",),
            "P": ("P",),
            "verbose": ("verbose",),
            "func": ("func",),
            "lines": ("lines",),
            "ogs_repo": ("ogs", "repo"),
            "ogs_version": ("ogs", "version"),
            "vultr_plan_id": ("vultr", "plan_id"),
            "vultr_api_key": ("vultr", "api_key"),
            "vpc_v4_subnet": ("vultr", "vpc", "v4_subnet"),
            "vpc_v4_subnet_mask": ("vultr", "vpc", "v4_subnet_mask"),
            "vpc_region": ("vultr", "vpc", "region"),
            "ansible_tags": ("ansible_tags",),
            "ram": ("vagrant", "ram",),
            "disk": ("vagrant", "disk",), 
            "cpu": ("vagrant", "cpu",), 
        }

        for arg_name, path in overrides.items():
            value = getattr(args, arg_name, None)
            if value is not None:
                self.set_nested(config, path, value)

        return config


    def addArguments(self):
        # Actions
        self.parser.add_argument("-destroy", action='store_true', help="Destroys all of the current VMs")
        self.parser.add_argument("-restart", action='store_true', help="Destroys and restarts all of the current VMs")
        self.parser.add_argument("-up", action='store_true', help="Just creates VMs and runs very basic setup with Infrastructure Manager (OpenTofu or Vagrant)")
        self.parser.add_argument("-ansible", action='store_true', help="Calls Ansible to setup the VMs")
        self.parser.add_argument("-test", action='store_true', help="Executes the commands from the run file")
        self.parser.add_argument("-ssh", action='store_true', help="Outputs the public IPs and ports used to SSH into the machines.")
        self.parser.add_argument("-ad_hoc", action='store_true', help="Uses Ansible ad-hoc commands to execute an action in the VMs")
        self.parser.add_argument("-log", action='store_true', help="Uses Ansible ad-hoc commands to tail the logs of a OGS component")

        # Printing (these stop execution)
        self.parser.add_argument("-vultr_regions", action='store_true', help="Shows the available regions for Vultr")
        self.parser.add_argument("-vultr_plans", action='store_true', help="Shows the available plans for Vultr")
        self.parser.add_argument("-readme", action='store_true', help="Prints the README")
        
        # General Arguments
        self.parser.add_argument("-c", "--config", help="Gives the path to the config file that outlines all of the information necessary to configure the VMs")
        self.parser.add_argument("-r", "--run", help="Gives the path to the a file that describes a sequence of commands to be run in the VMs")
        self.parser.add_argument("-v", "--verbose", action='store_true', help="Gives the option to run a TUI that displays some logs alongside test execution")
        self.parser.add_argument("--tui", action='store_true', help="Gives the option to run a TUI that displays some logs alongside test execution")
        self.parser.add_argument("--provider", help="The VM provider that is used (Vultr, VirtualBox, VMWare, QEMU)")
        self.parser.add_argument("--ogs_repo", help="The Open5GS repo that is installed to the VMs")
        self.parser.add_argument("--ogs_version", help="The version (branch) of the Open5GS repo that is cloned")
        self.parser.add_argument("--user_ssh_key", help="An ssh key automatically added to the authorized keys in the VMs")
        self.parser.add_argument("--create_services", action='store_true', help="Creates service files for OGS components in /etc/system/systemd")
        self.parser.add_argument("--copy_logs", action='store_true', help="Copies logs from VMs into local machine")
        self.parser.add_argument("--capture_packets", action='store_true', help="Captures network packets from the VMs during testing and copies them over to the host machine")
        self.parser.add_argument('--ansible_tags', nargs='+', help="Tells ansible which stages to run. Options: install_stage, config_stage, testing_stage, services_stage, ogstun, install_ogs")

        # Local Arguments
        self.parser.add_argument("--ram", help="The RAM used for the VMs (LOCAL ONLY)")
        self.parser.add_argument("--disk", help="The disk size allocated to the VMs (LOCAL ONLY)")
        self.parser.add_argument("--cpu", help="The amount of CPU allocated to the VMs (LOCAL ONLY)")

        # Vultr Arguments
        self.parser.add_argument("--vpc_region", help="The region where the virutal private network is created")
        self.parser.add_argument("--vultr_api_key", help="Personal Vultr API key")
        self.parser.add_argument("--vultr_plan_id", help="The plan used to create the VMs")
        self.parser.add_argument("--vpc_v4_subnet", help="The subnet used to create the VPC betwene the VMs")
        self.parser.add_argument("--vpc_v4_subnet_mask", help="The mask for the VPC subnet")

        # Ad Hoc Arguments
        self.parser.add_argument("--w", default="all", help="Which VMs to run ad-hoc commands on (all, hplmn, or vplmn), with a default value of all")
        self.parser.add_argument("--m", default="ansible.builtin.shell", help="Ansible module to run ad-hoc command (default is ansible.builtin.shell)")
        self.parser.add_argument("--a", help='A string of arguments for the ad-hoc command (e.g. "ip a")')
        self.parser.add_argument("--B", default=-1, help='Timeout (in seconds) for ad-hoc command')
        self.parser.add_argument("--P", default=-1, help='Poll time for ad-hoc commands')

        # Logs
        self.parser.add_argument("--func", nargs='+', help="Which function logs are going to be printed for (can be a list separated by spaces)")
        self.parser.add_argument("--lines", default="10", help="The number of lines to be returned from logs")
