# (c) 2019, OSNEXUS Corporation (eng@osnexus.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import time
from os import environ
import requests
from requests.auth import HTTPBasicAuth
from ansible.module_utils.basic import AnsibleModule

def quantastor_argument_spec():
    """Return standard base dictionary used for the argument_spec argument in AnsibleModule"""

    return dict(
        quantastor_hostname=dict(type = 'str'),
        quantastor_username=dict(type = 'str', default = 'admin'),
        quantastor_password=dict(type = 'str', default = 'password', no_log=True),
        quantastor_cert=dict(type = 'str' , default = '')
    )

