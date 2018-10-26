#!/usr/bin/env python
# This script will be used to help setup a customized Arista ESXI lab envrionment
# This script will try to configure and catch any configuration options that could arise.
#
#
# Revision 1.0
# Written by Rob Martin, Arista Networks 2018
#
__author__ = 'robmartin@arista.com'
__version__ = 1.0

from ruamel.yaml import YAML
from getpass import getpass
from os import listdir

#Output YAML file paths
esxi_yaml = 'esxi.yml'
lab_yaml = 'lab'
group_all = 'group_vars/all'
roles_veos_switches = 'roles/veos-switches/tasks/main.yml'
roles_esxi = 'roles/vmware-esxi/tasks/main.yml'
ryaml = YAML()

#Output of supplemental files
vcenter_vswitch = 'roles/vmware-esxi/files/esxi_vswitch_list.txt'

def check_integer(user_value,query):
    while type(user_value) != int:
        try:
            user_value = int(user_value)
        except ValueError:
            user_value = raw_input("\n***Please Enter a number***\n%s"%query)
    return(user_value)

def check_yes_no(user_value,query):
    user_value = user_value.lower()
    u_status = False
    if 'y' == user_value or 'yes' == user_value:
        u_status = True
        return True
    elif 'n' == user_value or 'no' == user_value:
        u_status = True
        return False
    while not u_status:
        user_value = raw_input("\n***Please Enter Yes or No***\n%s"%query).lower()
        if 'y' == user_value or 'yes' == user_value:
            u_status = True
            return True
        elif 'n' == user_value or 'no' == user_value:
            u_status = True
            return False

def get_dir(item,s_path):
    for r1 in listdir(s_path):
        if item in r1:
            return(r1)

def build_topo(spine,leaf,n_topo):
    "Used to build a topology for spine and leaf nics"
    topo = []
    spine_topo = {}
    leaf_topo = {}
    racks = leaf//2
    for r1 in range(1,spine+1):
        cur_int = 2
        s_vnic = {}
        l_vnic = {}
        for r2 in range(1,racks+1):
            for r3 in range(1,3):
                topo.append(['spine%s'%r1,'rack%s'%r2,'leaf%s'%r3])
                s_vnic['vmnic'+str(cur_int)] = '%s-spine%s_rack%s-leaf%s'%(n_topo,r1,r2,r3)
                cur_int += 1
        if leaf%2:
            topo.append(['spine%s'%r1,'rack%s'%str(racks+1),'leaf1'])
            s_vnic['vmnic'+str(cur_int)] = '%s-spine%s_rack%s-leaf1'%(n_topo,r1,racks+1)
        spine_topo['%s-spine%s'%(n_topo,r1)] = s_vnic
    for r1 in range(1,leaf+1):
        for r2 in range(1,racks+1):
            for r3 in range(1,3):
                l_vnic = {}
                cur_int = 2
                l_vnic['vmnic'+str(cur_int)] = '%s-rack%s-leaf1_rack%s-leaf2'%(n_topo,r2,r2)
                cur_int += 1
                for r4 in range(1,spine+1):
                    l_vnic['vmnic'+str(cur_int)] = '%s-spine%s_rack%s-leaf%s'%(n_topo,r4,r2,r3)
                    cur_int += 1
                l_vnic['vmnic'+str(cur_int)] = '%s-rack%s-leaf%s_rack%s-linux-01'%(n_topo,r2,r3,r2)
                leaf_topo['%s-rack%s-leaf%s'%(n_topo,r2,r3)] = l_vnic
    return(spine_topo,leaf_topo)

def build_veos_device(device,spine,leaf,power_on,n_topo):
    "Used to build the veos-switches main.yml file"
    dict_veos = []
    #Section to start building Spine section
    #Used to create base vmnics for spines
    spine_vnic = {'nic1':{'type':"{{esxi_veos_adapter_type}}",'network':"{{esxi_vmnic}}",'network_type':'standard'}}
    if device == 'switch':
        for r1 in range(2,leaf+2):
            spine_vnic['nic%s'%r1] = {'type':"{{esxi_veos_adapter_type}}",'network':"{{item.value.vmnic%s}}"%r1,'network_type':'standard'}
        tmpSpine = """\
        name: Create Spine Switches
        tags: deploy_vEOS_Spine
        delegate_to: localhost
        command: >
            "{{playbook_dir}}/files/{{ovftool}}"
            --sourceType=OVA
            --acceptAllEulas
            --allowExtraConfig
            --noSSLVerify
            --diskMode=thin
            --skipManifestCheck
            --name='{{item.key}}'
            --datastore='{{ esxi_datastore }}'
            --network='{{ esxi_vmnic }}'
            --X:injectOvfEnv
            --X:logToConsole
            '{{ veos_ova }}'
            'vi://{{ esxi_username }}:{{ esxi_password }}@{{ esxi_ip }}'
        ignore_errors: true
        with_dict: '{{vm_config_spines}}'"""
        dict_veos.append(ryaml.load(tmpSpine))

        #Section to start building Leaf section
        leaf_vnic = {'nic1':{'type':"{{esxi_veos_adapter_type}}",'network':"{{ esxi_vmnic }}",'network_type':'standard'}}
        for r1 in range(2,spine+4):
            leaf_vnic['nic%s'%r1] = {'type':"{{esxi_veos_adapter_type}}",'network':"{{item.value.vmnic%s}}"%r1,'network_type':'standard'}
        tmpLeaf = """\
        name: Create Leaf Switches
        tags: deploy_vEOS_Leaf
        delegate_to: localhost
        command: >
            "{{playbook_dir}}/files/{{ovftool}}"
            --sourceType=OVA
            --acceptAllEulas
            --allowExtraConfig
            --noSSLVerify
            --diskMode=thin
            --skipManifestCheck
            --name='{{item.key}}'
            --datastore='{{ esxi_datastore }}'
            --network='{{ esxi_vmnic }}'
            --X:injectOvfEnv
            --X:logToConsole
            '{{ veos_ova }}'
            'vi://{{ esxi_username }}:{{ esxi_password }}@{{ esxi_ip }}'
        ignore_errors: true
        with_dict: '{{vm_config_leafs}}'"""
        dict_veos.append(ryaml.load(tmpLeaf))

        # ============================================================
        # Need to change the ethernet0 network adapter type to match 
        # All other network adapters.  Otherwise interface mappings
        # Will be crossed.
        # ============================================================
        dict_veos.append({
            'name':'Change Adapter type to {{esxi_veos_adapter_type}}',
            'tags':'updating_ethernet0_adapter',
            'with_dict':"{{vm_config_leafs | combine(vm_config_spines)}}",
            'replace':{
                'path':'/vmfs/volumes/{{esxi_datastore}}/{{item.key}}/{{item.key}}.vmx',
                'regexp':'vmxnet3',
                'replace':'e1000',
                'backup':'yes'
            }
        })
        
        #Secttion to create modified NICS for Spines
        tmpNet = """\
        name: Modify Spine NICs
        tags: modify_spine_nics
        with_dict: '{{vm_config_spines}}'
        blockinfile:
            dest: /vmfs/volumes/{{esxi_datastore}}/{{item.key}}/{{item.key}}.vmx
            insertafter: EOF
            block: |"""
        for r1 in range(1,leaf+1):
            tmpNet += """
                ethernet%s.virtualDev = "{{esxi_veos_adapter_type}}"
                ethernet%s.networkName = "{{item.value.vmnic%s}}"
                ethernet%s.addressType = "generated"
                ethernet%s.uptCompatibility = "TRUE"
                ethernet%s.present = "TRUE"
                """%(r1,r1,r1+1,r1,r1,r1)
        dict_veos.append(ryaml.load(tmpNet))

        #Secttion to create modified NICS for Leafs
        tmpNet = """\
        name: Modify Leaf NICs
        tags: modify_leaf_nics
        with_dict: '{{vm_config_leafs}}'
        blockinfile:
            dest: /vmfs/volumes/{{esxi_datastore}}/{{item.key}}/{{item.key}}.vmx
            insertafter: EOF
            block: |"""
        for r1 in range(1,spine+3):
            tmpNet +=  """
                ethernet%s.virtualDev = "{{esxi_veos_adapter_type}}"
                ethernet%s.networkName = "{{item.value.vmnic%s}}"
                ethernet%s.addressType = "generated"
                ethernet%s.uptCompatibility = "TRUE"
                ethernet%s.present = "TRUE"
                """%(r1,r1,r1+1,r1,r1,r1)
        dict_veos.append(ryaml.load(tmpNet))

        #Modify CPU on all switches
        dict_veos.append({
            'name':'Modify CPU on Switches',
            'tags':'modify_cpu_switches',
            'with_dict':"{{vm_config_leafs | combine(vm_config_spines)}}",
            'lineinfile':{
                'dest':'/vmfs/volumes/{{esxi_datastore}}/{{item.key}}/{{item.key}}.vmx',
                'regex': 'numvcpus',
                'line': 'numvcpus= "{{vm_veos_vcpu}}"'
            }
        })
        #Modify RAM on all switches
        dict_veos.append({
            'name':'Modify RAM on Switches',
            'tags':'modify_ram_switches',
            'with_dict':"{{vm_config_leafs | combine(vm_config_spines)}}",
            'lineinfile':{
                'dest':'/vmfs/volumes/{{esxi_datastore}}/{{item.key}}/{{item.key}}.vmx',
                'regex':'memSize',
                'line': 'memSize= "{{vm_veos_memory}}"'
            }
        })

        #Section to reload all newly added VMS so modifications take into effect
        dict_veos.append({
            'name':'Reload New Switches',
            'tags':'reload_switches',
            'shell':"for a in $(vim-cmd vmsvc/getallvms | grep %s | awk '{print $1}');do vim-cmd vmsvc/reload $a;done"%n_topo
        })

        #Section to add powering on VM commands
        if power_on:
            dict_veos.append({
            'name':'Power-on New Switches',
            'tags':'power_on_switches',
            'shell':"for a in $(vim-cmd vmsvc/getallvms | grep %s | awk '{print $1}');do vim-cmd vmsvc/power.on $a;done"%n_topo
            })
    return(dict_veos)

def build_esxi():
    list_esxi = []
    list_esxi.append({'name':'Create vSwitches from file esxi_vswitch_list.txt',
                    'tags':'esxi_vswitch',
                    'command':"{{item}}",
                    'with_items':'{{lookup("file","esxi_vswitch_list.txt").splitlines()}}',
                    'ignore_errors':'yes'})
    return(list_esxi)

def build_vswitches(s_data,n_topo):
    dict_net = []
    dict_add = []
    vlan_id = 10
    base_c = 'esxcli network vswitch standard'
    l_net = s_data['vm_config_leafs']
    dict_add.append("%s add -v %s"%(base_c,n_topo))
    dict_add.append("%s policy security set -v %s -f yes -m yes -p yes"%(base_c,n_topo))
    for r1 in l_net:
        for r2 in l_net[r1]:
                net = l_net[r1][r2]
                if net not in dict_net:
                    dict_net.append(net)
    for new_net in dict_net:
        dict_add.append("%s portgroup add -v %s -p %s"%(base_c,n_topo,new_net))
        dict_add.append("%s portgroup set -p %s -v %s"%(base_c,new_net,vlan_id))
        vlan_id += 1
    return(dict_add)

def export_yaml(data,f_path):
    rYaml = YAML()
    rYaml.dump(data,f_path)

def main():
    #Dictionary objects to be used to create the yaml files
    dict_esxi = [{'hosts':'lab-esxi','vars_files':['group_vars/all'],'roles':[{'role':'vmware-esxi'},{'role':'veos-switches'}]}]
    base_def = {}
    esxi_def = {}
    vm_config_spines = {}
    vm_config_leafs = {}
    list_def = [base_def,esxi_def]

    #Set variables to work off of
    print('\n============================================================================')
    print('Please answer the following questions to help customize your lab deployment.')
    print('============================================================================\n')
    num_spines = check_integer(raw_input("How many spine switches will be used? "),'How many spine switches will be used? ')
    num_leafs = check_integer(raw_input("How many leaf switches will be used? "),'How many leaf switches will be used? ')
    topo_name = raw_input("What is the name for this topology? ")
    
    #Add wrong value input detection 
    esxi_ip = raw_input("What is the IP address or hostname for ESXI? ")
    esxi_username = raw_input("What is the username for %s? "%esxi_ip)
    esxi_password = getpass("What is the password for %s on %s? "%(esxi_username,esxi_ip))
    esxi_ds = raw_input("What is the name of the datastore to use on %s? "%(esxi_ip))
    eos_ova = 'files/' + raw_input("What is the name of the EOS OVA? ie EOS-4.21.0F.ova: ")
    esxi_vmnic = raw_input("What is the name of the Port-Group for the EOS ma1 interface? ")
    vm_state = raw_input("Power on the switches when done? (y/n) ")
    if 'y' in vm_state.lower():
        vm_state = True
    else:
        vm_state = False
    
    esxi_vnic = 'e1000'
    
    vm_veos_memory = '2048'
    vm_veos_vcpu = '1'
    ovftool = 'ovftool/ovftool'

    #Apply base data to dictionary object
    base_def['vm_veos_memory'] = vm_veos_memory
    base_def['vm_veos_vcpu'] = vm_veos_vcpu
    base_def['ovftool'] = ovftool
    base_def['veos_ova'] = eos_ova

    #Apply data for ESXI to dictionary object
    esxi_def['esxi_ip'] = esxi_ip
    esxi_def['esxi_username'] = esxi_username
    esxi_def['esxi_password'] = esxi_password
    esxi_def['esxi_datastore'] = esxi_ds
    esxi_def['esxi_veos_adapter_type'] = esxi_vnic
    esxi_def['esxi_vmnic'] = esxi_vmnic

    #Section to start building and configuring the vnics for the spine/leaf switches
    vm_config_spines, vm_config_leafs = build_topo(num_spines,num_leafs,topo_name)


# =================================================
# Start outputing data to YAML files
# =================================================

    #Section to start building the esxi.yml file
    with open(esxi_yaml,'w') as esxi:
        export_yaml(dict_esxi,esxi)

    #Section to build the lab file
    with open(lab_yaml,'w') as lab_f:
        lab_f.write('[all:vars]\n')
        lab_f.write('ansible_user=ansible\n')
        lab_f.write('ansible_ssh_pass=ansible\n\n')
        lab_f.write('[lab-esxi]\n')
        lab_f.write('%s'%esxi_ip)

    #Section for group vars all
    with open(group_all,'w') as g_all:
        c_dict = {}
        for r1 in list_def:
            if r1:
                if c_dict:
                    c_dict.update(r1)
                else:
                    c_dict = r1.copy()
        c_dict['vm_config_spines'] = vm_config_spines
        c_dict['vm_config_leafs'] = vm_config_leafs
        export_yaml(c_dict,g_all)

    # Writes data to veos-switches/tasks/main.yml
    with open(roles_veos_switches,'w') as v_switches:
        export_yaml(build_veos_device('switch',num_spines,num_leafs,vm_state,topo_name),v_switches)
    
    # Writes data vmware-esxi/tasks/main.yml
    with open(roles_esxi,'w') as v_esxi:
        export_yaml(build_esxi(),v_esxi)
    
    # Writes switch data to vmware/esxi/files/esxi_vswitch_list.txt
    with open(vcenter_vswitch,'w') as v_vswitch:
        s_data = build_vswitches(c_dict,topo_name)
        for r1 in s_data:
            if s_data.index(r1) == 0:
                v_vswitch.write(r1)
            else:
                v_vswitch.write('\n%s'%r1)
    


if __name__ == '__main__':
    main()