#!/usr/bin/env python

'''Usage: mkvgvars.py <project_home_directory> <link_name>

'''

import docopt
import os


VAGRANT_USER_ROOT = '/vagrant'
PROJECT_DIRECTORY_VAR_NAME = 'TDX_HOME'



def main(args):

    home_dir = os.path.expanduser('~')    
    project_path = os.path.expanduser(args['<project_home_directory>'])    
    relative_project_path = project_path[len(home_dir):].lstrip('/')
    vagrant_project_path = os.path.join(VAGRANT_USER_ROOT, relative_project_path)    
    link_name = args['<link_name>']

    properties = {}

    #properties[PROJECT_DIRECTORY_VAR_NAME] = '~/%s' % link_name
    
    properties['project_dir_link_src'] = vagrant_project_path.rstrip('/')
    properties['project_dir_link_dest'] = '~/%s' % link_name
    properties['couchbase_data_bucket'] = 'tdx_data'
    properties['couchbase_journal_bucket'] = 'tdx_oplogs'

    remote_username = raw_input('What is your username on the remote system? ')
    properties['remote_username'] = remote_username
    
    with open('playbooks/temp_vars/tdx.yml', 'w+') as f:
        f.write('---\n')        
        f.write('# Default values for tdx project setup\n')

        for key, value in properties.iteritems():
            f.write('%s: %s\n' % (key, value))

    print 'wrote properties to Ansible vars file ./%s' % 'playbooks/temp_vars/tdx.yml'
    
            

if __name__=='__main__':
    args = docopt.docopt(__doc__)
    main(args)
    
