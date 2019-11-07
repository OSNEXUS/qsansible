#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, OSNEXUS Engineering (eng@osnexus.com), Steven Umbehocker (steve@osnexus.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: quantastor_volume
version_added: '4.6'
short_description: Manage Storage Volume (iSCSI/FC) block storage operations within QuantaStor storage grids
description:
- Create, delete or modify storage volumes within a QuantaStor storage grid.
author:
- Steven Umbehocker, Seth Cagampang
options:
  volume:
    description:
    - Name of the new storage volume to be created (of any type volume, snapshot, clone, etc).
  volumeType:
    description:
    - Specify the volume type to be created (*normal, snapshot, clone)
  size:
    description:
    - size of the volume to be created in MB
  state:
    description:
    - Creates (present) or deletes (absent) a storage volume
    default: present
    choices: [ absent, present ]

Volume-Delete options:
  deleteChildren:
    description:
    - Set to 'true' to recursively delete child snapshots.

volumeType = snapshot Options:
  volume:
    description:
    - Optional name for storage volume snapshot. If not specified, an auto-generated name will be assigned to the snapshot.
  parent:
    description:
    - Specify the parent volume for this snapshot.
  description:
    description:
    - Gives a description to the snapshot
  accessMode:
    description:
    - Sets the access mode for the storage volume snapshot. [none, readonly, *readwrite]
  count:
    description:
    - Sets the number of snapshots of the specified volume to create.
  
  flags:
    description:
    - Optional flags for the operation.
extends_documentation_fragment:
- quantastor
'''

EXAMPLES = r'''
- name: Create new Storage Volume of size 1GB called volumeA in pool DefaultPool
  quantastor_volume:
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password
    volume: volumeA
    pool: DefaultPool
    size: 1024

- name: Create a snapshot of volumeA called snapA
  quantastor_volume: 
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password 
    parent: volumeA
    volume: snapA
    description: desc-snapA
    accessMode: 0
    count: 1
    flags: 0

- name: Delete Storage Volume snapshot named snapA of volumeA
  quantastor_volume:
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password
    volume: snapA
    state: absent

- name: Delete Storage Volume named volumeA
  quantastor_volume:
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password
    volume: volumeA
    state: absent
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from os import environ
import requests
from requests.auth import HTTPBasicAuth
from ansible.module_utils.quantastor import quantastor_argument_spec
from ansible.module_utils.qs_client import quantastor_sdk_enabled
from ansible.module_utils.qs_client import QuantastorClient

def main():
    argument_spec = quantastor_argument_spec()
    argument_spec.update(dict(
        volume=dict(type='str'),
        parent=dict(type='str'),
        pool=dict(type='str'),
        size=dict(type='str'),
        description=dict(type='str'),
        accessMode=dict(type='str'),
        count=dict(type='str'),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        volumeType=dict(type='str', default='normal', choices=['normal','snapshot','clone']),
        #delete option
        deleteChildren=dict(type='bool', default=False),
        flags=dict(type='int', default=0),
    ))

    # System checks
    module = AnsibleModule(argument_spec, supports_check_mode=True)
    if not quantastor_sdk_enabled():
        module.fail_json(msg='QuantaStor python SDK is required for this module.')

    client = QuantastorClient.from_module(module)
    try:
        client.storage_system_get("")
    except:
        module.fail_json(msg='Unable to gather QuantaStor system information.')

    # Operational Variables
    state = module.params['state']
    volumeType = module.params['volumeType']

    # Bailout checks
    # all non-'snapshot' volume types require 'volume' parameter.
    if not module.params['volume'] and not volumeType == 'snapshot':
        module.fail_json(msg="To create/delete a '%s', the 'volume' parameter must be specified." % (module.params['volumeType']))
    
    if module.params['volume']:
        try:
            client.storage_volume_get(storageVolume=module.params['volume'])
            if state == 'present':
                # If you try to create (present), exit if a volume with that name already exists.
                module.exit_json(changed=False)
        except Exception as e:
            if state == 'absent':
                # If you try to delete (absent), exit if no volume with that name exists.
                module.exit_json(changed=False)
            else:
                # case: storage volume named: module.params['volume'] does not already exist and state = 'present'
                pass

    if not module.params['parent']:
        if not volumeType == 'normal':
            # all non-'normal' volume types require 'parent' parameter.
            module.fail_json(msg="To create a '%s', 'parent' parameter must be specified." % (module.params['volumeType']))

    if volumeType == 'normal':
        if not module.params['size'] and not state == 'absent':
            # all normal shares need to have a 'size' argument
            module.fail_json(msg="To create a normal share you must provide a 'size' parameter.")
    else:
        try:
            client.storage_volume_get(storageVolume=module.params['parent'])
        except Exception as e:
            # all non-'normal' volume types require a vaild parent object
            module.fail_json(msg="To create a '%s', 'parent' parameter must be a valid storage volume." % (module.params['volumeType']))

    
    # For create operations:
    if state == 'present':
        # normal volumes require the 'pool' parameter to be a valid storage pool.
        if not module.params['pool']:
            if volumeType == 'normal':
                module.fail_json(msg="To create a normal volume, 'pool' parameter must be specified.")
        else:
            try:
                client.storage_pool_get(module.params['pool'])
            except:
                module.fail_json(msg="To create a normal volume, 'parent' parameter must be a valid storage pool.")

    #Parameter interpretation
    deleteChildren = False
    if module.params['deleteChildren']:
        deleteChildren = module.params['deleteChildren']

    # Case: set recursive flag
    if deleteChildren:
        flags = 262144
    else:
        flags = module.params['flags']
    
    #CREATE
    if state == 'present':
        #NORMAL VOLUME
        if volumeType == 'normal':
            try:
                client.storage_volume_create_ex(
                            name=module.params['volume'],
                            size=module.params['size'], 
                            description=module.params['description'], 
                            provisionableId=module.params['pool']
                            )
            except Exception as e: 
                module.fail_json(msg="Failed to create storage volume '%s', error was '%s'." % (module.params['volume'], str(e)))

        #SNAPSHOT
        elif volumeType == 'snapshot':
            try:
                client.storage_volume_snapshot(
                    storageVolume=module.params['parent'],
                    snapshotName=module.params['volume'],
                    description=module.params['description'],
                    accessMode=module.params['accessMode'],
                    count=module.params['count'],
                    flags=module.params['flags'],
                    )
            except Exception as e:
                module.fail_json(msg="Failed to create snapshot '%s' for Storage Volume  '%s', error was '%s'." % (module.params['snapName'],module.params['volume'], str(e)))

        #CLONE
        elif volumeType == 'clone':
            #unimplemented
            module.exit_json(changed=False)

        module.exit_json(changed=True)

    #DELETE
    elif state == 'absent':
        try:
            client.storage_volume_delete(storageVolumeList=module.params['volume'],flags=flags)
        except Exception as e: 
            module.fail_json(msg="Failed to delete storage volume '%s', error was '%s'." % (module.params['volume'], str(e)))
        
        # Verify Deletion
        module.exit_json(changed=True)
    
    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
