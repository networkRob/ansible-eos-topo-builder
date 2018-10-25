# Ansible ESXI Topology Builder
* Currently working through an issue where the EOS devices are only deployed with a single NIC

This script will help create the necessary files to run an Ansible-Playbook.  `setup.py` will be used to create a customized Layer3 Leaf-Spine (L3LS) topology.  

This may take serveral minutes for the topology to be built, depending on the size.

The script will build an isoloated vSwitch based on the name for the topology.  All port-groups created are contained within this single vSwitch.

## Requirements
You will need the following to make this project work:
* This project uses Ansible to build. This has been tested on 2.7 but should work in previous versions.
* You will need SSH enabled on your ESXi server
* You will need a copy of VMware's `ovftool` in `/files`
* A working ESXi host. All you really need for this is a management IP address and a single datastore.
* You will need the Arista EOS OVA file. Put it in `files/`


## Python Package Dependencies
Here is a list of packages that are required to run `setup.py` and the ansible-playbook
- ruamel.yaml
- ansible
- pyvmomi

## Example
```
$ ./build
============================================================================

Please answer the following questions to help customize your lab deployment.
============================================================================

How many spine switches will be used? 1
How many leaf switches will be used? 2
What is the name for this topology? rob-01
What is the IP address for ESXI? 192.168.20.8
What is the username for 192.168.20.8? ansible
What is the password for ansible on 192.168.20.8?
What is the name of the datastore to use on 192.168.20.8? datastore1
What is the name of the EOS OVA? ie EOS-4.21.0F.ova: EOS-4.21.0F.ova
What is the name of the Port-Group for the EOS ma1 interface? LAB-MGMT
Power on the switches when done? (y/n) y
...
{Output of Ansible-Playbook removed}
...
```