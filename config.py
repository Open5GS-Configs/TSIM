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

        self.parser = argparse.ArgumentParser(description="TSIM aims to create a reproducible environment for testing 5G \
                                            core performance within the TOPSSIM project. It uses a number of tools to automate \
                                            the creation and configuration of virtual machines used for testing.", 
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
            "vultr_api_key": ("vultr", "api_key"),
            "ansible_tags": ("ansible_tags",),
        }

        for arg_name, path in overrides.items():
            value = getattr(args, arg_name, None)
            if value is not None:
                self.set_nested(config, path, value)

        return config


    def addArguments(self):
        # Actions
        actions_group = self.parser.add_mutually_exclusive_group()
        actions_group.add_argument("-destroy", action='store_true', help="Destroys all of the current VMs")
        actions_group.add_argument("-restart", action='store_true', help="Destroys and restarts all of the current VMs")
        actions_group.add_argument("-up", action='store_true', help="Just creates VMs and runs very basic setup with Infrastructure Manager (OpenTofu or Vagrant)")
        actions_group.add_argument("-ansible", action='store_true', help="Calls Ansible to setup the VMs")
        actions_group.add_argument("-test", action='store_true', help="Executes the commands from the run file")
        actions_group.add_argument("-ssh", action='store_true', help="Outputs the public IPs and ports used to SSH into the machines.")
        actions_group.add_argument("-ad_hoc", action='store_true', help="Uses Ansible ad-hoc commands to execute an action in the VMs")
        actions_group.add_argument("-log", action='store_true', help="Uses Ansible ad-hoc commands to tail the logs of a OGS component")

        # Printing (these stop execution)
        print_group = self.parser.add_mutually_exclusive_group()
        print_group.add_argument("-vultr_regions", action='store_true', help="Shows the available regions for Vultr")
        print_group.add_argument("-vultr_plans", action='store_true', help="Shows the available plans for Vultr")
        print_group.add_argument("-readme", action='store_true', help="Prints the README")
        
        # General Arguments
        general_group = self.parser.add_argument_group("General Arguments (override config file)")
        general_group.add_argument("-c", "--config", help="Gives the path to the config file that outlines all of the information necessary to configure the VMs")
        general_group.add_argument("-r", "--run", help="Gives the path to the a file that describes a sequence of commands to be run in the VMs")
        general_group.add_argument("--tui", action='store_true', help="Gives the option to run a TUI that displays some logs alongside test execution")
        general_group.add_argument("--provider", help="The VM provider that is used (Vultr, VirtualBox, VMWare, QEMU)")
        general_group.add_argument("--user_ssh_key", help="An ssh key automatically added to the authorized keys in the VMs")
        general_group.add_argument('--ansible_tags', nargs='+', help="Tells ansible which stages to run. Options: install_stage, config_stage, testing_stage, services_stage, ogstun, install_ogs")
        general_group.add_argument("--create_services", action='store_true', help="Creates service files for OGS components in /etc/system/systemd")
        general_group.add_argument("--copy_logs", action='store_true', help="Copies logs from VMs into local machine")
        general_group.add_argument("--capture_packets", action='store_true', help="Captures network packets from the VMs during testing and copies them over to the host machine")

        # Vultr Arguments
        vultr_group = self.parser.add_argument_group("Vultr Arguments (override config file)")
        vultr_group.add_argument("--vultr_api_key", help="Personal Vultr API key")

        # Ad Hoc Arguments
        adhoc_group = self.parser.add_argument_group("Arguments for Ad Hoc commands")
        adhoc_group.add_argument("--w", default="all", help="Which VMs to run ad-hoc commands on (all, hplmn, or vplmn), with a default value of all")
        adhoc_group.add_argument("--m", default="ansible.builtin.shell", help="Ansible module to run ad-hoc command (default is ansible.builtin.shell)")
        adhoc_group.add_argument("--a", help='A string of arguments for the ad-hoc command (e.g. "ip a")')
        adhoc_group.add_argument("--B", default=-1, help='Timeout (in seconds) for ad-hoc command')
        adhoc_group.add_argument("--P", default=-1, help='Poll time for ad-hoc commands')

        # Logs
        logs_group = self.parser.add_argument_group("Arguments for capturing logs (with -log flag)")
        logs_group.add_argument("--func", nargs='+', help="Which function logs are going to be printed for (can be a list separated by spaces)")
        logs_group.add_argument("--lines", default="10", help="The number of lines to be returned from logs")
