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
module: quantastor_share
version_added: '4.6'
short_description: Manage Network share operations within QuantaStor Storage Grid
description:
- Create, delete or modify Network shares within a QuantaStor storage grid.
author:
- Steven Umbehocker, Seth Cagampang

options:
  state:
    description:
    - Used to help inturpret what operation is being done on the Network share. 'present' (create) or 'absent' (delete).
    choices: [*'present','absent']
  share:
    description:
    - Name of the new Network Share to be created (of any type, subshare, alias, share, snapshot, etc).
  shareType:
    description
    - Specify what type of share is to be created, this field is not needed to delete any type of share (*normal, alias, subshare, snapshot).
  pool:
    description:
    - Specify the storage pool used for this share.
  ownerUser:
    description:
    - Assign a user as the owner of this share.
  ownerGroup:
    description:
    - Assign a user group to own this share (owner must be a part of chosen group).
  quota:
    description:
    - Set a quota size for the networkshare specified in Bytes (OK: KiB, KB, MiB, MB, GiB, GB, TiB, TB). Default value is 0.
  recordSizeKb:
    description:
    - Set a size for storage blocks. Argument must be a power of 2. Size will be set in KB. Default value is 0.
  publicNFS:
    description:
    - A boolean argument to set the 'isPublic' parameter. Default value is True.
  publicSMB:
    description:
    - A boolean argument to set the 'enableCifs' parameter. Default value is True.
  permissions:
    description:
    - A string argument in either the Unix/Linux permission format or octal format (eg. rwxr-x--- or 750).
  smbOptionList:
    description:
    - Sets various SMB/CIFS options from a ',' deleimited list in the form 'Key1=Value1,Key2=Value2,...,Keyn=Valuen'.
  userAccessList:
    description:
    - Specifies users and groups to be valid, invalid, or none in the form 'user1:value1,user2:value2,@group1:value3'. Prepend with tilde (~) to remove access assignment. Prepend with '@' to specify a user group.
  syncPolicy:
    description:
    - Used for handling writes to the storage pool with options 'always', 'disabled', or 'standard'. standard mode is a hybrid of write-through and write-back caching based on the O_SYNC flag, always mode is write-through to ZIL which could be SSD cache, and disabled indicates to always use async writes.
  compressionType:
    description:
    - Specify the type of compression to be used. (on \| off \| lzjb \| gzip \| gzip-[1-9] \| zle \| lz4).
  copies:
    description:
    - Indicates the number of copies of each block should be maintained in the Storage Pool.
  disableSnapBrowsing:
    description:
    - A boolean argument that when set to true prevents the ability to browse snpashot directories over CIFS.
  quotaExcludeSnapshots:
    description:
    - A boolean argument that when set to true offers unlimited space to be utilized by snapshots of the parent.
  reservedSpace:
    description:
    - Specifies the amount of thick-provisioned reserved space for a Storage volume.
  description:
    description:
    - Adds a description to the newly created network share.

Share-Delete options:
  deleteChildren:
    description:
    - Set to 'true' to recursively delete child snapshots.

shareType = subshare/alias options:
  share:
    description:
    - Name of the subshare/Alias.
  parent:
    description:
    - Name or ID of the parent share for this subshare/alias
  description:
    description:
    - Gives a description to the subshare/alias.
  subPath:
    description:
    - Designates a subPath to define the subShare.
    required: subshare
  inheritSettings:
    description:
    - Allows subshare to inherit access control settings from the parent share including NFS access entries and CIFS user/group access entries.
  publicNFS:
    description:
    - Indicates that the specified network subshare/alias should be made public.
  isActvie:
    description:
    - Indicates if the subshare/alias should be set to active upon initalization.

shareType = snapshot options:
  name:
    description:
    - Optional name to assign to snapshot. If name is not given a default time-stamped name will be auto-generated.
  parent:
    description:
    - Name or ID of the parent share for this snapshot.
  description:
    description:
    - Gives a description to the snapshot.
  isActive:
    description:
    - Indicates if the snapshot should be set to active upon initalization.

Flag options:
  flags:
    description:
    - allows user to set operational flags.


extends_documentation_fragment:
- quantastor
'''

EXAMPLES = r'''
- name: Create new Network share of size 10GB called shareA in pool DefaultPool
  quantastor_share:
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password
    share: shareA
    pool: DefaultPool
    ownerUser: admin
    ownerGroup: root
    quota: 5TB
    recordSizeKb: 32
    publicNFS: True
    publicSMB: True
    permissions: rwxr-x---
    smbOptionList: 'browseable=yes,public=no,writable=yes'
    userAccessList: 'user1:valid,foo:invalid,@admGroup:valid'
    syncPolicy: 0
    compressionType: gzip
    copies: 2
    disableSnapBrowsing: True
    quotaExcludeSnapshots: false
    reservedSpace: 10GB
    pool: DefaultPool140
    description: desc-4-shareA

- name:  create a subshare called subA
  quantastor_share:
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password
    alias: subA
    subDesc: sub-desc-subA
    subPath: /division/
    inheritSettings: true
    subPublic: true
    subActive: true
    operation: share-create-alias

- name: create a snapshot called snapA
  quantastor_share:
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password
    snapshot: snapA
    snapDesc: snapA-desc
    snapActive: true
    operation: share-snapshot

- name: Delete a subShare named subA of Network share shareA
  quantastor_share:
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password
    share: shareA
    name: subA
    operation: share-delete

- name: Delete a snapshot named snapA of Network share shareA
  quantastor_share:
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password
    share: shareA
    name: snapA
    operation: share-delete

- name: Delete Network share named shareA
  quantastor_share:
    quantastor_hostname: 10.10.10.2
    quantastor_username: admin
    quantastor_password: password
    share: shareA
    operation: share-delete
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.quantastor import quantastor_argument_spec
from ansible.module_utils.qs_client import quantastor_sdk_enabled
from ansible.module_utils.qs_client import QuantastorClient

def main():
    argument_spec = quantastor_argument_spec()
    argument_spec.update(dict(
        #network share parameters
        share=dict(type='str'),
        shareType=dict(type='str', default='normal', choices=['normal','subshare','alias','snapshot']),
        pool=dict(type='str'),
        ownerUser=dict(type='str'),
        ownerGroup=dict(type='str'),
        description=dict(type='str'),
        quota=dict(type='str', default='0'),
        recordSizeKb=dict(type='str', default='0'),
        isActive=dict(type='bool', default=True),
        publicNFS=dict(type='bool', default=True),
        publicSMB=dict(type='bool', default=True),
        permissions=dict(type='str'),
        smbOptionList=dict(type='str'),
        userAccessList=dict(type='str'),
        syncPolicy=dict(type='str', default='standard', choices=['standard','always','disabled']),
        compressionType=dict(type='str'),
        copies=dict(type='str', default='1'),
        disableSnapBrowsing=dict(bool='bool'),
        quotaExcludeSnapshots=dict(type='bool', default=True),
        reservedSpace=dict(type='str', default='0'),
        state=dict(type='str', default='present', choices=['present','absent']),
        #share-delete option
        deleteChildren=dict(type='bool', default=False),
        #alias options
        subPath=dict(type='str'),
        inheritSettings=dict(type='str'),
        #alias & snapshot required
        parent=dict(type='str'),
        #operations and flags
        flags=dict(type='int', default=0),
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
    shareType = module.params['shareType']

    # Bailout checks
    # all non-'snapshot' require 'share' parameter.
    if not module.params['share'] and not shareType == 'snapshot':
        module.fail_json(msg="To create/delete a '%s', the 'share' parameter must be specified." % (module.params['shareType']))
    
    if module.params['share']:
        try:
            client.network_share_get(networkShare=module.params['share'])
            if state == 'present':
                # If you try to create (present), exit if a share with that name already exists.
                module.exit_json(changed=False)
        except Exception as e:
            if state == 'absent':
                # If you try to delete (absent), exit if no share with that name exists.
                module.exit_json(changed=False)
            else:
                # case: network share named: module.params['share'] does not already exist and state = 'present'
                pass

    if not module.params['parent']:
        if not shareType == 'normal':
            # all non-'normal' share types require 'parent' parameter.
            module.fail_json(msg="To create a '%s', 'parent' parameter must be specified." % (module.params['shareType']))
    else:
        try:
            client.network_share_get(networkShare=module.params['parent'])
        except Exception as e:
            # all non-'normal' share types require a vaild parent object
            module.fail_json(msg="To create a(n) '%s', 'parent' parameter must be a valid network share." % (module.params['shareType']))


    # For create operations:
    if state == 'present':
        # normal shares require the 'pool' parameter to be a valid storage pool.
        if not module.params['pool']:
            if shareType == 'normal':
                module.fail_json(msg="To create a normal share, 'pool' parameter must be specified.")
        else:
            try:
                client.storage_pool_get(module.params['pool'])
            except:
                module.fail_json(msg="To create a normal share, 'parent' parameter must be a valid storage pool.")
        # all subshares require the 'subPath' parameter
        if shareType == 'subshare' and not module.params['subPath']:
            module.fail_json(msg="To create a subshare, 'subPath' parameter must be specified.")

    # Parameter interpretation 
    syncPolicy = 0
    if module.params['syncPolicy']:
      syncPolicy = module.params['syncPolicy']

    if syncPolicy == 'standard':
      syncPolicy = '0'
    elif syncPolicy == 'always':
      syncPolicy = '1'
    elif syncPolicy == 'disabled':
      syncPolicy = '2'
    else:
      syncPolicy = '0'

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
        #NORMAL SHARE
        if shareType == 'normal':
            try:
                client.network_share_create_ex(
                    name=module.params['share'],
                    description=module.params['description'],
                    provisionableId=module.params['pool'],
                    shareOwner=module.params['ownerUser'],
                    shareOwnerGroup=module.params['ownerGroup'],
                    permissions=module.params['permissions'],
                    isActive=module.params['isActive'],
                    isPublic=module.params['publicNFS'],
                    enableCifs=module.params['publicSMB'],
                    cifsOptions=module.params['smbOptionList'],
                    userAccessList=module.params['userAccessList'],
                    spaceQuota=module.params['quota'],
                    blockSizeKb=module.params['recordSizeKb'],
                    syncPolicy=syncPolicy,
                    compressionType=module.params['compressionType'],
                    copies=module.params['copies'],
                    disableSnapBrowsing=module.params['disableSnapBrowsing'],
                    spaceQuotaExcludeSnapshots=module.params['quotaExcludeSnapshots'],
                    spaceReserved=module.params['reservedSpace'],
                    flags=module.params['flags']
                    )
            except Exception as e:
                module.fail_json(msg="Failed to create Network share '%s', error was '%s'." % (module.params['share'], str(e)))

        #SUBSHARE/ALIAS
        elif shareType == 'subshare' or shareType == 'alias':
            try:
                client.network_share_create_alias(
                    name=module.params['share'],
                    description=module.params['description'],
                    parentShareId=module.params['parent'],
                    subSharePath=module.params['subPath'],
                    inheritParentSettings=module.params['inheritSettings'],
                    isPublic=module.params['publicNFS'],
                    isActive=module.params['isActive'],
                    flags=module.params['flags']
                    )
            except Exception as e:
                module.fail_json(msg="Failed to create alias/sub-share '%s' for Network share  '%s', error was '%s'." % (module.params['share'],module.params['parent'], str(e)))

        #SNAPSHOT
        elif shareType == 'snapshot':
            try:
                client.network_share_snapshot(
                    networkShare=module.params['parent'],
                    snapshotName=module.params['share'],
                    description=module.params['description'],
                    isActive=module.params['isActive'],
                    flags=module.params['flags'],
                    )
            except Exception as e:
                module.fail_json(msg="Failed to create snapshot '%s' for Network share  '%s', error was '%s'." % (module.params['share'],module.params['parent'], str(e)))

        module.exit_json(changed=True)

    #DELETE
    elif state == 'absent':
        try:
            client.network_share_delete_ex(networkShareList=module.params['share'],flags=flags)
        except Exception as e:
            module.fail_json(msg="Failed to delete Network share '%s', error was '%s'." % (module.params['share'], str(e)))

        module.exit_json(changed=True)

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
