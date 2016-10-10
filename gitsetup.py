#/usr/bin/env python
#
# setup script for github credential variables
# used to feed Ansible scripts
#
# Dexter Taylor 
# binarymachineshop@gmail.com
#


import os, sys
from os import listdir
from os.path import isfile, join
import getpass
import fnmatch


USERNAME_PROMPT = "Please enter your github user ID: "
PASSWORD_PROMPT = "Please enter your github password: "
REPO_LOCATION_PROMPT = "Please enter the location for the repository: "
REPO_LOCATION_DEFAULT = "github.com/binarymachines/blocpower.git"
REPO_LOCAL_OWNER_PROMPT = "Please enter the user that will own repository:"
REPO_LOCAL_OWNER_DEFAULT = "vagrant"




def captureInput(inputPrompt, default=None, showResponse=True):
    """
    Receive a user input string. 
    if showResponse is False, do not echo typed chars
    to terminal.
    Default value for response.
    """
    response = None
    if default is not None:
        if showResponse:
            response = raw_input("%s :(Default: %s)" % (inputPrompt, default))
            if response == "" :
                response = default
        else:
            response = getpass.getpass("%s" % inputPrompt)
    else:
        if showResponse:
            response = raw_input("%s" % inputPrompt)
        else:
            response = getpass.getpass("%s" % inputPrompt)

    return response



def writeAnsibleVarsFile(varDictionary, roleName, fileName):
    """
    Generate a YAML-style Ansible variables file.
    write the name-value pairs in the passed dictionary 
    to the specified file, and create a symlink
    """
    

    currentPath = os.getcwd()
    targetPath = os.path.join(currentPath, 'playbooks', 'roles', roleName, 'vars', fileName)
    linkPath = os.path.join(currentPath, 'playbooks', 'roles', roleName, 'vars', 'main.yml')

    if os.path.exists(linkPath):
        print 'File or symlink %s already exists.' % linkPath
        return 


    print 'Writing vars file to: %s...' % targetPath

    writeSuccess = False

    with open(targetPath, 'w+') as varsFile:
        for key in varDictionary:
            varsFile.write('%s: %s\n' % (key, varDictionary[key]))
        writeSuccess = True

        
    print 'Creating symbolic link %s...' % linkPath

    if writeSuccess:
        # create symbolic link
        os.symlink(targetPath, linkPath)
        

    

def main():    
    os.system('cls' if os.name == 'nt' else 'clear')
    
    gitUsername = captureInput(USERNAME_PROMPT)
    
    gitPassword = captureInput(PASSWORD_PROMPT, None, False)
    
    gitRepo = captureInput(REPO_LOCATION_PROMPT, REPO_LOCATION_DEFAULT)
    
    repoLocalOwner = captureInput(REPO_LOCAL_OWNER_PROMPT, REPO_LOCAL_OWNER_DEFAULT)
    
    repoDestination = os.path.join('/home/',repoLocalOwner, 'blocpower')
    
    configurationFiles = []
    for file in os.listdir(os.path.join('..','web')):
        if fnmatch.fnmatch(file, '*.conf'):
            configurationFiles.append(file)
    CONFIGURATION_PROMPT = "Select Configuration File:\n"
    for configIndex in range(len(configurationFiles)):
        CONFIGURATION_PROMPT += "[" + str(configIndex+1)+ "]" +configurationFiles[configIndex] + "\n"
    configurationResponseIndex = captureInput(CONFIGURATION_PROMPT,str(1))
    configurationFile = configurationFiles[int(configurationResponseIndex)-1]
    
    credentials = {'github_username': gitUsername, 'github_password': gitPassword, 'github_repo_address' : gitRepo, 'repo_destination': repoDestination, 'repo_owner': repoLocalOwner, 'configuration_file': os.path.join(repoDestination,'web',configurationFile)}
    variableFilename = 'main_%s.yml' % gitUsername
    writeAnsibleVarsFile(credentials, 'UMAP', variableFilename)


    print 'gitsetup exiting.'





if __name__ == '__main__':
    main()


