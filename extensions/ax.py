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


        
class ExtensionContext(object):
    def __init__(self, extension_name, description, logger):
        self.name = extension_name
        self.description = description
        self.logger = logger


        
class AnsibleExtensionContext(ExtensionContext):
    def __init__(self, logger, **kwargs):
        ExtensionContext.__init__(self, __name__, 'Ansible extension', logger)

        self.playbook_dir = kwargs.get('playbook_directory')
        if not os.path.isdir(self.playbook_dir):
              raise InvalidPlaybookDirError(self.playbook_dir)

        self.ansible_hosts = kwargs.get('ansible_hosts')


        
def __load__(description, logger, context_registry, **kwargs):
    extension_name = __name__
    print '### Loading extension %s...' % extension_name
    if not context_registry.get(extension_name):
        context = AnsibleExtensionContext(logger, kwargs)
        context_registry.register(context, extension_name)
        


def _mkrole(self, args):
    print 'stub mkrole extension function'


def _lsroles(self, args):
    '''List ansible roles'''
    
    print 'stub lsroles extension function'


def _lsvars(self, args):
    '''List ansible variables'''      
    print 'stub lsvars extension function'
