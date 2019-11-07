# Running QuantaStor Ansible playbooks

## Step 1: install ansible
NOTE: best to do this on a stock ubuntu 16.04 VM as your Ansible controller else you may run into package pinning issues

    sudo apt-get update
    sudo apt-get install ansible git python3-pip
    pip3 install requests
    sudo python3 -m pip install quantastor-qsclient

## Step 2: clone quantastor ansible module git repository

    cd /path/to/dir
    git clone https://github.com/cagamps/qsansible.git

## Step 3: tell ansible about one of your quantastor test boxes by editing /etc/ansible/hosts and adding a section like shown below:

    nano /etc/ansible/hosts

Modify this file with the following text (see playbooks/hosts.example):

    [qsservers]
    x.x.x.x qs_username='username' qs_password='password'


replace above IP with the IP of your QuantaStor appliance or one within a grid and the credantials with your own username and password.

## Step 3: copy the QuantaStor ansible module files into place, here I'm using a symbolic link to the source code in my git checkout rather than copying the content NOTE: installation location for 'qs_client.py' may differ on your system.

    cd /path/to/dir/qsansible
    ln -s /path/to/dir/qsansible/quantastor.py /usr/local/lib/python3.6/dist-packages/ansible/module_utils/.
    ln -s /usr/local/lib/python3.6/dist-packages/quantastor/qs_client.py /usr/local/lib/python3.6/dist-packages/ansible/module_utils/.
    ln -s /path/to/dir/qsansible/quantastor/ /usr/local/lib/python3.6/dist-packages/ansible/modules/storage/

## Step 4: run a playbook to test the module

You can find example playbooks in the `/path/to/dir/qsansible/playbooks/` location. If you are in the root of the git repo you can run the following commands:

    cd playbooks/
    ansible-playbook qstest_addhost.yml -vvv

## Step 5: verification.. make sure that the above commands ran successfully


## MISC NOTES: these things are not needed but can be used to get a newer copy of ansible from github and then puts it into your python path.  If you do this you don't need to apt-get install ansible
    sudo apt-add-repository ppa:ansible/ansible
    git clone https://github.com/ansible/ansible.git
    export PYTHONPATH="/root/ansible:/root/ansible/lib"
    python ./ansible/lib/ansible/modules/storage/quantastor/quantastor_host.py 

# Testing using ansible playbooks

This section will detail how to set up a test to run the 'qstest_addshare_test.yml' playbook. This playbook removes the share 'testShare'
if it exists, then creates a new share called 'testShare' with various parameters set/assigned. The purpose of these instructions are to insure that 
all of the prerequisits (groups, users, pools, etc...) to run this testing-playbook are set up such that the instructions are executed successfully.

Before running this playbook, you should at least follow steps 1 - 3 in the section above.

## Step 1: Create a user-group named 'testGroup' using the QuantaStor CLI, REST service, or UI.

## Step 2: Create a storage pool named 'DefaultPool' using the QuantaStor CLI, REST service, or UI.

## Step 3: Navigate to the playbook directory. 

Playbooks can be found in the qsansible git repository `./path/to/dir/qsansible/playbooks/`

## Step 4: Now you have all of the prerequisits neeeded. Run the playbook in verbose mode using the following command:

    ansible-playbook <playbook>.yml -vvv

eg.
    ansible-playbook qstest_addshare.yml -vvv

Result: If you look at your target QuantaStor_host UI you should see that a Network Share named 'testShare' 
has been created with the parameters listed in the playbook set. Alternatively you can run one of these commands to see that you new share exists:

### CLI command from a QuantaStor box on your system :
    qs share-list

### Using qstorapi :
    curl -u admin:password "https://[hostIP]:8153/qstorapi/networkShareGet?networkShare=testShare" -k

To setup your own playbook see documentation in ansible modules. (quantastor_host.py, quantastor_share.py, quantastor_volume.py)