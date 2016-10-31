#!/usr/bin/env python
#
# warp extension module
#


MKROLE_USAGE ='''
   Usage:
    mkrole <name>
    lsroles 
    lsvars [role]

'''

from docopt import docopt
from warp_common import ExtensionContext
import os


class PlaybookManager():
      def __init__(self, user_id, ssh_keyfile, working_directory):
          self.user_id = user_id
          self.ssh_keyfile = ssh_keyfile
          self.working_dir = working_directory
          self.warp_template_dir = os.path.join(self.working_dir, 'warpfiles')
          self.warp_template_mgr = get_template_mgr_for_location(self.warp_template_dir)
          
          _template_vars = []

          
      def _retrieve_template_variables(self, ansible_role):
          pass

    
      @property
      def template_variable_names(self):
            return self._template_vars


      @property
      def warpfiles(self):
          return None
          

      @property
      def templates(self):
          return None

          
          
class Role():
    def __init__(self, name):
        self._name = name


    @property
    def name(self):
        return self._name

    
    def add_task_config(self, yaml_config):
        pass

    
    def add_default_values(self, yaml_config):
        pass

    
    def add_dependencies(self):
        pass

    

class RoleRegistry():
    def __init__(self, working_directory):
        self.roles = {}
        role_dirs = os.listdir(os.path.join(os.getcwd(), 'roles'))
        for dirname in role_dirs:
            new_role = Role(dirname)
            self.roles[new_role.name] = (new_role, os.path.join(os.getcwd(), 'roles', dirname))

    
    
class Playbook():
    def __init__(self):
        self.roles = []

    def add_role(self, role_name):
        self.roles.append(role_name)


        
class AnsibleExtensionContext(ExtensionContext):
    def __init__(self, warp_home_dir, logger, **kwargs):
        ExtensionContext.__init__(self, warp_home_dir, __name__, 'Ansible extension', logger)

        self.playbook_path = os.path.join(warp_home_dir, 'playbooks')
        if not os.path.isdir(self.playbook_path):
              raise InvalidPlaybookDirError(self.playbook_path)


        
def __load__(warp_home_dir, logger, **kwargs):
    return AnsibleExtensionContext(warp_home_dir, logger, **kwargs)


        
def _mkrole(self, args):
    print 'stub mkrole extension function'


def _lsroles(self, args):
    '''List ansible roles'''
    
    print 'stub lsroles extension function'


def _lsvars(self, args):
    '''List ansible variables'''      
    print 'stub lsvars extension function'
