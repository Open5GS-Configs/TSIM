# TOPSSIM Environment Setup

The purpose of this project is to create a reproducible environment for testing 5G core performance within the TOPSSIM project. It uses a number of tools to automate the creation and configuration of virtual machines used for testing. Currently, it creates two VMs, one per PLMN. This could be extended to create a VM per component, connecting each VM through a private network and running only its particular function in the future. 

This project uses:
    <br>- A Python script for parsing arguments and connecting different tools together
    <br>- [Ansible](https://docs.ansible.com/projects/ansible/latest/installation_guide/intro_installation.html#installing-and-upgrading-ansible-with-pip) to install dependencies, bring Open5GS configurations, and run tests
    <br>- [OpenTofu](https://opentofu.org/docs/intro/install/deb/#step-by-step-instructions) to create and initially configure cloud VMs (provided by Vultr)
    <br>- [Vagrant](https://developer.hashicorp.com/vagrant/install#linux) to create and configure local VMs (provided by VirtualBox and VMWare). To control the disk size of the VMs, it is also necessary to install a plugin with the following command: `vagrant plugin install vagrant-disksize`


Notes for VMWare:
    <br>- For use with VMWare, a plugin needs to be installed [here](https://developer.hashicorp.com/vagrant/install/vmware).
    <br>- Before creating the VMs, in the control panel for VMware a Host-only network needs to be created with DHCP disabled with the adapter name "vmnet5" to create the private connection between VMs


It clones and builds an Open5GS repo into /root/open5gs/ and copies the specified config files into /root/open5gs/install/etc/open5gs/ (the config files need to take this into account for pathing).

<img src="/img/diagram.png" width="75%">

### Config 
It requires a .yaml config file to store the required parameters for execution. Options differ between providers. This is a sample of a config file:

```
---
ogs:
  repo: "<Open5GS repo>"
  version: <the git version used when cloning the repo>

hplmn:
  config_repo: <HPLMN Config repo> 
  hosts_path: <Path to Hosts used in HPLMN>
  test_script: <Path to your test script>
  private_ip: "<IP for private network>"
  region: "<region for HPLMN>"


vplmn:
  config_repo: <VPLMN Config repo> 
  hosts_path: <Path to Hosts used in VPLMN>
  test_script: <Path to your test script>
  private_ip: "<IP for private network>"
  region: "<region for VPLMN>"

################# If using Cloud VM Provider #################
vultr:
  vpc:
    v4_subnet: "<subnet for private network>"
    v4_subnet_mask: "<subnet mask for private network>"
    region: "<region for private network>"
  hplmn_region: "<region for HPLMN>"
  vplmn_region: "<region for VPLMN>"
  plan_id: "<plan used for machines>"
##############################################################

################# If using Local VM Provider #################
vagrant:
  ram: <RAM to be allocated to each VM (in MB)>
  cpu: <CPU cores to be allocated to each VM>
  disk: <Disk size of each VM (in GB)>

  use_netem: <adds network emulation for local testing>
  netem: <the following are example values>
    delay: 
      time: 100ms 
      jitter: 10ms
      correlation: 25%
    distribution: normal
    loss: 2% # % assumes random model
    corrupt: 1%
    duplicate: 1%
    gap: 5
    rate:
      rate: 5kbit
      packetoverheard: 20
      cellsize: 100
      celloverhead: 5
##############################################################

###################### General Settings ######################
create_services: <(true or false) creates service files in /etc/systemd/system and enables all components to run at boot>
user_ssh_key: "<SSH key of the user>"
provider: "<your VM provider (can either be Vultr, VB or VMWare)>"
```

For **Local** VMs, it is important to note that the ram is meant to be in MB and the disk in GB. Also, Vagrant automatically forwards localhost ports for ssh connections to the VMs. The default user in the VMs will be called "vagrant" and the default password is also "vagrant".

### Run File

A yaml file that gives commands to be executed in each machine. It is executed sequentially using Ansible ad-hoc commands. A sample file could be:
```
---
- where: hplmn
  function: udm
  cmd: <a command>
  logs: 
      - func: udm
        lines: 5
      - func: sepp
        lines: 100
      
- where: vplmn
  function: amf
  cmd: <another command>
  logs: 
      - amf
      - udm
      - sepp

- where: vplmn
  function: amf
  cmd: registration.simple-test
  config: examples.gnb-001-01-ue-999-70
```

The first task executes a command in the HPLMN and collects the last 5 logs from the UDM and the last 100 from the SEPP.
The second task executes a command in the VPLMN and collects the default 10 last logs from the AMF, UDM, and SEPP.
Lastly, the last task runs the simple registration test with one of the example configurations. 

A timeout and polling time can also be specified with each command. The default timeout is 120 seconds and polling is 10 seconds. 

The -test command line argument just runs the commands from the run file.

### Running the program
You can call it using:
`python3 topssim_setup.py  -c /directory/your_config_file.yaml -r /directory/your_run_file.yaml`

You can check other command-line options with `python3 topssim_setup.py -h`.

Some examples are:
To run just the configuration and testing stages of Ansible on already existing machines:
`python3 topssim_setup.py  -c /directory/your_config_file.yaml -r /directory/your_run_file.yaml -ansible --ansible_tags "config_stage testing_stage"`

It is also useful to know that OpenTofu, Vagrant, and Ansible provide CLI tools. These can be used to isolate a part of the process. Some notable commands are:

1. Ansible:    

`ansible all -m ping ` to test connectivity    
`ansible-playbook topssim_setup.yaml` to run the playbook   
`ansible-inventory --list-hosts` to see the hosts    
`ansible-galaxy role list` to see the installed roles  

- To add a SSH key passphrase to be recognized by Ansible when creating the SSH connection to the hosts:    
Start SSH Agent:     
`eval "$(ssh-agent -s)"`     
And add private key:     
`ssh-add ~/.ssh/id_rsa` 


2. OpenTofu:   
`tofu show`    
`tofu state list`    
`tofu state show vultr_vpc.sepp-link` (the address of the instances lives in _vultr-opentofu/vultr_resources.tf_)   


3. Vagrant:
`vagrant up`
`vagrant ssh-config`
`vagramt destroy`

### Troubleshooting

1.  OpenTofu:     

- If a resource has been deleted manually, OpenTofu will not recognize the change. It must be manually deleted from its instances.     
This shows the states that are being tracked: `tofu state list`      
If the instance deleted is still there, you can remove it with: `tofu state rm vultr_vpc.sepp-link` (instead of `vultr_vpc.sepp-link` insert your instance's address).     

2. Vagrant
If a machine times out during boot, especially when being created, it can signify a problem in the communication to that machine. Sometimes the box has been created but it does not connect. The best way to deal with this is to run the -restart command, which destroys and recreates the machines. 
