#!/usr/bin/env python3

from time import time
from pathlib import Path

from config import Config
from topssim_setup import setupTOPSSIM
from tui.tui import TSim


def main():
    start_time = time()
    cwd = Path(__file__).resolve().parent

    configManager = Config()
    config, run = configManager.createConfig()
    
    setup = setupTOPSSIM(config, run, cwd)

    configKeys = config.keys()
    if "destroy" in configKeys:
        setup.destroy()

    elif "up" in configKeys:
        setup.strategy.callInfManager()
        setup.printVMIPs()

    elif "tui" in configKeys:
        app = TSim(config, run, cwd, setup)
        app.run()

    elif "restart" in configKeys:
        setup.destroy()
        setup.setup()
        setup.ansibleManager.runFileCommands()
        setup.printVMIPs()

    elif "ansible" in configKeys:
        runTest = False
        if "testing_stage" in config["ansible_tags"]:
            runTest = True
            config["ansible_tags"].remove("testing_stage")
            config["ansible_tags"].append("ssh_stage")
        setup.callAnsible(writeInventory=False, tags=config["ansible_tags"])
        if runTest or config["ansible_tags"] == "":
            setup.ansibleManager.runFileCommands()
        setup.printVMIPs()    

    elif "test" in configKeys:
        setup.ansibleManager.runFileCommands()
        setup.printVMIPs()

    elif "ad_hoc" in configKeys:
        if "arguments" not in configKeys:
            raise Exception("Arguments missing in ad-hoc command")

        name = f"\n[blue bold]{config['where'].upper()}:[/] executing ad-hoc command: [dark_orange italic]{config['arguments']}[/]\n"
        setup.ansibleManager.runAdHocCommand(config["where"], config["module"], config["arguments"], name, config["B"], config["P"])
    
    elif "log" in configKeys:
        if "func" not in configKeys:
            raise Exception("A function has to be provided")
        setup.ansibleManager.getLogs(config["where"], config["func"], config["lines"])
    
    elif "ssh" in configKeys:
        setup.printVMIPs()
    
    elif "vultr_regions" in configKeys:
        setup.printVultrRegions()

    elif "vultr_plans" in configKeys:
        setup.printVultrPlans()

    elif "readme" in configKeys:
        setup.printReadme()
    
    else:
        runTest = False
        
        if "testing_stage" in config["ansible_tags"]:
            runTest = True
            config["ansible_tags"].remove("testing_stage")
            config["ansible_tags"].append("ssh_stage")
        
        setup.setup(runTest)

    print(f"\n\nExecution Complete!\nTime Elapsed: {(time()-start_time):.2f} seconds")


if __name__ == "__main__":
    main()
