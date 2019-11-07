#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, OSNEXUS Engineering (eng@osnexus.com), Steven Umbehocker (steve@osnexus.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: quantastor_host
version_added: '4.6'
short_description: Manage iSCSI/FC host entries within QuantaStor storage grids
description:
- Create, delete or modify hosts within a QuantaStor storage grid.
author:
- Steven Umbehocker
options:
  host:
    description:
    - The hostname of the host.
    required: true
  state:
    description:
    - Host with an associated IQN(s) and/or WWPN(s) must be added before Storage Volume may be assigned to a given Host.
    - Removing a Host will disconnect all volumes assigned to it.  Hosts may be grouped into Host Groups.
    default: present
    choices: [ absent, present ]
  initiators:
    description:
    - List of iSCSI IQNs and/or FC WWPNs for the Host.
extends_documentation_fragment:
- quantastor
'''

EXAMPLES = r'''
- name: Create new Host entry called "foo" in the storage grid
  quantastor_host:
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password
    host: foo
    initiators: iqn.foo

- name: Delete Host entry called "foo" from the storage grid
  quantastor_host:
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password
    host: foo
    state: absent

- name: Create a Host called "bar" with WWPN and IQN entries in the storage grid
  quantastor_host:
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password
    host: bar
    initiators:
    - 00:00:00:00:00:00:00
    - 11:11:11:11:11:11:11
    - iqn.1994-05.com.redhat:12345678

- name: Map Host "foo" to Storage Volume "volume2"
  quantastor_host:
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password
    host: foo
    volume: volume2
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.quantastor import quantastor_argument_spec
from ansible.module_utils.qs_client import quantastor_sdk_enabled
from ansible.module_utils.qs_client import QuantastorClient
from ansible.module_utils.qs_client import Host

# Helper function forms 2 sets from given arguments and _initiatorPortList then returns 
# the Difference-set or the Intersection-set based on the given mode (true: intersection, false: difference).
def getIntersectionDifference(argset, hostset, mode):
    ret = set()
    tempArgs = set()
    tempHosts = set()

    for arg in argset:
        tempArgs.add(arg)
    for init in hostset:
        tempHosts.add(init['name'])

    if mode:
        ret = tempArgs.intersection(tempHosts)
    else:
        ret = tempArgs.difference(tempHosts)

    return ret


def main():
    argument_spec = quantastor_argument_spec()
    argument_spec.update(dict(
        host=dict(type='str'),
        hosts=dict(type='list'),
        hostgroup=dict(type='str'),
        description=dict(type='str'),
        initiators=dict(type='list'),
        volume=dict(type='str'),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        flags=dict(type='str',default='0'),
    ))

    # System checks
    module = AnsibleModule(argument_spec, supports_check_mode=True)
    if not quantastor_sdk_enabled():
        module.fail_json(msg='QuantaStor python SDK is required for this module.')

    client = QuantastorClient.from_module(module)
    try:
        client.storage_system_get()
    except:
        module.fail_json(msg='Unable to gather QuantaStor system information.')

    # Operation Variables
    state = module.params['state']    
    
    # Object Variables
    host = None
    hostgroup = None

    # Bailout checks
    if module.params['host'] and module.params['hostgroup']:
        module.fail_json(msg="Cannot perform operation that has both host and hostgroup as the target.")
    if not (module.params['host'] or module.params['hostgroup']):
        module.fail_json(msg="Cannot perform operation unless atleast one of, 'host' or 'hostgroup' are specified.")
    if module.params['volume'] and module.params['initiators']:
        module.fail_json(msg="Invalid argument specification. You cannot specify both 'volume' and  'initiators' arguments together.")

    if state == "present":
        # create host or add host initiators
        if module.params['host']:
            try:
                host = client.host_get(host=module.params['host'])
                hostId = module.params['host']
            except Exception as e:
                # case: Add new host entry
                if module.params['initiators']:
                    pass
                else:
                    module.fail_json(msg="Operation failed because target host '%s' does not exist. Error was '%s'." % (module.params['host'],str(e)))
        
        # create hostgroup
        if module.params['hostgroup']:
            try:
                task, hostgroup = client.host_group_get(hostGroup=module.params['hostgroup'])
                # case: Trying to create a hostgroup with name that already exists.
                if module.params['hosts']:
                    module.exit_json(changed=False)
                hostId = module.params['hostgroup']
            except Exception as e:
                # case: Create new hostgroup
                if module.params['hosts']:
                    pass
                else:
                    module.fail_json(msg="Operation failed because target hostgroup '%s' does not exist. Error was '%s'." % (module.params['hostgroup'],str(e)))

        # attach volume to host or hostgroup
        if module.params['volume']:   
            try:
                client.storage_volume_get(module.params['volume'])
            except Exception as e:
                module.fail_json(msg="To assign a storage volume to a host/hostgroup, the target volume '%s' must exist. Error was '%s'." % (module.params['volume'],str(e)))

            try:
                client.storage_volume_acl_get(storageVolume=module.params['volume'],host=hostId)
                module.exit_json(changed=False)
            except Exception as e:
                # case: ACL add between module.params['volume'] and a host/hostgroup
                if (host or hostgroup):
                    pass
                else:
                    module.fail_json(msg="Cannot attach storage volume '%s' to a host or host group that does not exist. Error was '%s'." % (module.params['volume'], str(e)))

    if state == "absent":
        # delete host or remove host initiators
        if module.params['host']:
            try:
                host = client.host_get(host=module.params['host'])
                hostId = module.params['host']
            except Exception as e:
                if not (module.params['initiators'] or module.params['volume']):
                    module.exit_json(changed=False)
                else:
                    module.fail_json(msg="Cannot remove host entry '%s' because it does not exist. Error was '%s'" % (module.params['host'],str(e)))
        
        # delete hostgroup
        if module.params['hostgroup']:
            try:
                task, hostgroup = client.host_group_get(hostGroup=module.params['hostgroup'])
                hostId = module.params['hostgroup']
            except Exception as e:
                if not (module.params['volume']):
                    module.exit_json(changed=False)
                else:
                    module.fail_json(msg="Cannot remove hostgroup '%s' because it does not exist. Error was '%s'" % (module.params['hostgroup'],str(e)))
        
        # detach storage volumes from host or hostgroup
        if module.params['volume']:
            try:
                client.storage_volume_get(storageVolume=module.params['volume'])
            except Exception as e:
                module.fail_json(msg="Failed to detatch storage volume ACL because storage volume '%s' does not exist. Error was '%s'." % (module.params['volume'],str(e)))

            try:
                client.storage_volume_acl_get(storageVolume=module.params['volume'],host=hostId)
            except Exception as e:
                module.exit_json(changed=False)



    # Create/Add Operations
    if state == 'present':
        #CREATE HOST GROUP
        if not hostgroup and module.params['hosts']:
            try:
                client.host_group_create(
                    name=module.params['hostgroup'],
                    description=module.params['description'],
                    hostList=module.params['hosts'],
                    flags=module.params['flags']
                    )
                module.exit_json(changed=True)
            except Exception as e: 
                module.fail_json(msg="Failed to create host group '%s' with hosts '%s', error was '%s'." % (module.params['hostgroup'], ','.join(module.params['hosts']), str(e)))
            
        #ASSIGN VOLUME TO HOST OR HOSTGROUP
        elif (module.params['hostgroup'] or module.params['host']) and module.params['volume']:
            try:
                client.storage_volume_acl_add_remove_ex(
                    storageVolumeList=module.params['volume'], 
                    host=hostId,
                    modType=0, #OSN_CMN_MOD_OP_ADD
                    flags=module.params['flags']
                    )
                module.exit_json(changed=True)
            except Exception as e: 
                module.fail_json(msg="Failed to create new volume assignment entry to host '%s/%s', error was '%s'." % (module.params['volume'], module.params['host'], str(e)))

        #ADD HOST ENTRY
        elif not host and module.params['initiators'] and module.params['host']:
            try:
                client.host_add(
                        hostname=module.params['host'], 
                        iqn=module.params['initiators'][0],
                        description=module.params['description'],
                        flags=module.params['flags']
                        )
                initiators = iter(module.params['initiators'])
                next(initiators)
                for port in initiators:
                    try:
                        client.host_initiator_add(
                            host=module.params['host'], 
                            iqn=port,
                            flags=module.params['flags']
                            )
                    except Exception as e: 
                        module.fail_json(msg="Failed to create new host initiator entry '%s', error was '%s'." % (port, str(e)))
                module.exit_json(changed=True)
            except Exception as e: 
                module.fail_json(msg="Failed to create new host entry '%s', error was '%s'." % (module.params['host'], str(e)))
            module.fail_json(msg="Failed to create new host entry '%s'." % (module.params['host']))

        #ADD HOST INITIATORS TO HOST ENTRY
        elif host and module.params['initiators']:
            missingInitiators = getIntersectionDifference(module.params['initiators'],host._initiatorPortList,False) #return difference
            if len(missingInitiators) > 0:
                for port in missingInitiators:
                    try:
                        client.host_initiator_add(host=module.params['host'], iqn=port)
                    except Exception as e: 
                        module.fail_json(msg="Failed to create new host initiator entry '%s', error was '%s'." % (port, str(e)))
                module.exit_json(changed=True)
            else:
                module.exit_json(changed=False)

    # Delete/Remove operations
    elif state == 'absent':
        #DELETE HOST GROUP
        if hostgroup and not module.params['volume']:
            try:
                client.host_group_delete(hostGroup=module.params['hostgroup'])
                module.exit_json(changed=True)
            except Exception as e: 
                module.fail_json(msg="Failed to delete host group '%s', error was '%s'." % (module.params['hostgroup'], str(e)))
            module.fail_json(msg="Failed to delete host group '%s'." % (module.params['hostgroup']))

        #UNASSIGN VOLUME FROM HOST or HOSTGROUP 
        elif module.params['volume']:
            try:
                client.storage_volume_acl_add_remove_ex(
                    storageVolumeList=module.params['volume'], 
                    host=hostId,
                    modType=1
                    )
                module.exit_json(changed=True)
            except Exception as e: 
                module.fail_json(msg="Failed to remove volume assignment entry for host (or hostgroup) '%s/%s', error was '%s'." % (module.params['volume'], hostId, str(e)))
            module.fail_json(msg="Failed to remove volume assignment entry for volume '%s'." % (module.params['volume']))

        #REMOVE HOST
        elif host and not module.params['volume'] and not module.params['initiators']:
            try:
                client.host_remove(module.params['host'])
                module.exit_json(changed=True)
            except Exception as e: 
                module.fail_json(msg="Failed to remove host entry '%s', error was '%s'." % (module.params['host'], str(e)))
            module.fail_json(msg="Failed to remove host entry '%s'." % (module.params['host']))

        #REMOVE HOST INITIATORS FROM HOST
        elif host and module.params['initiators']:
            removeInitiators = getIntersectionDifference(module.params['initiators'],host._initiatorPortList,True) # return intersection
            if len(removeInitiators) > 0:
                for port in removeInitiators:
                    try:
                        client.host_initiator_remove(module.params['host'], port)
                    except Exception as e: 
                        module.fail_json(msg="Failed to remove host initiator entry '%s', error was '%s'." % (port, str(e)))
                module.exit_json(changed=True)
            else:
                module.exit_json(changed=False)

    else:
        module.fail_json(msg="Invalid state '%s', must be either 'present' or 'absent'." % module.params['state'])

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
