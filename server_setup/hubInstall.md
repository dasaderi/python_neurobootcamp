## Setup/maintenance instructions for JupyterHub

### Installation

On a single linux machine (user "svd" can be replaced by some other name of course):

1. Install jupyterhub as root, configure more or less vanilla installation, as described in their docs
[https://github.com/jupyterhub/jupyterhub#installation]

2. create user svd with sudo privileges, install python (miniconda in this example) and clone the python_neurobootcamp repo from github into /svd/home/

3. create accounts user01 ... user30. for each userXX (See also create_bootcamp_users script):
   
   Create users and clone svd’s repo their home directory
   
```for i in $(seq -f "%02g" 1 30)
  do
   user="user$i"
   echo "Creating $user"
   sudo useradd -s /bin/bash -p $user -m -d /home/$user $user
   sudo su -l $user -c "git clone /home/svd/python_neurobootcamp"
  done
```

   Set password for each user with "sudo passwd userXX"
   
   If you want users to be able to log directly (not with jupyterhub): create .bash_login, set PATH to include to svd’s python install

4. Things to think about for testing:

   Are all the python packages installed that are required by each notebook?
   
   Can the server handle the load of X students all logged in and running the notebooks at the same time?


### Starting the server

After reboot, log in as svd and run ```sudo su -l -c /home/svd/miniconda3/bin/jupyterhub``` (You need to be running as root in order to be able to launch all the different users' notebooks.)

### Maintenance:

If the likely case that the repo changes after the intial installation, here's a script to pull down latest repo to svd, and then have each userXX pull the repo from svd (update_bootcamp)

```#!/bin/bash

echo "pulling latest to svd install"
sudo su -l svd -c"cd python_neurobootcamp; git pull"

echo "propogating to userXX accounts"
for i in $(seq -f "%02g" 1 40)
   do
      user="user$i"
      echo $user
      sudo su -l $user -c "cd ~/python_neurobootcamp; git checkout -- *; git pull
   done
```

### Instructions for users to download their modified notebooks:

1. Log in to your account (userXX). In the root directory, you should see a single folder, `python_neurobootcamp`.

2. In the upper right corner, click New -> Python 3 notebook

3. A new window should appear with a single empty cell. Paste in this text: ```!tar cvfz python_neurobootcamp.tar.gz python_neurobootcamp``` and run that cell.

4. Close the current notebook. You should then see a new file `python_neurobootcamp.tar.gz` in your notebook home folder.

5. Click the checkbox next to that entry (python_neurobootcamp.tar.gz). You should see a "Download" button appear at the top of the screen. Click and save to your local computer. Most unzipping software should be able to uncompress this once downloaded.
