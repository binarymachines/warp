#!/usr/bin/env python
# warp: management tool for Ansible playbook config
# 
#
# Note: the docopt usage string must start on the first non-comment, non-whitespace line.
#

"""Usage: 
    warp [ -pge ] <command_target>  
    warp ls 
    warp ls <command_target> 
    warp --config
	

Arguments:
    command_target   a group with multiple commands, or a single command of the format '<group>.<command>'

    
Options:
    -l, --list       List contents of command target, or list all command groups
    -p, --preview    Preview mode: generate command line from command target but do not execute
    -g, --group      Specify command-group as a target
    -c, --config     Show current config information

"""


from docopt import docopt
import yaml
import jinja2
from cmd import Cmd
import os, sys
from sys import stdin
import re
import logging



logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class MissingEnvironmentVariableException(Exception):
    def __init__(self, varname):
        Exception.__init__(self, 'Environment variable %s is not set.' % varname)


        
class JinjaTemplateManager:
    def __init__(self, j2_environment):
        self.environment = j2_environment
        
    def get_template(self, filename):
        return self.environment.get_template(filename)
        


def get_template_mgr_for_location(directory):
      j2env = jinja2.Environment(loader = jinja2.FileSystemLoader(directory))
      return JinjaTemplateManager(j2env)



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
            #new_role.add_task_config()


    
    
class Playbook():
    def __init__(self):
        self.roles = []

    def add_role(self, role_name):
        self.roles.append(role_name)



class ComposeException(Exception):
    def __init__(self, parameter_string):
        Exception.__init__(self, 'No value provided for command parameter %s in the passed args or the defaults.'
                           % parameter_string)
        


class Composer(object):
    def __init__(self, command_template, **kwargs):
        self.raw_cmd = command_template.command_line
        self.default_parameter_values = command_template.defaults()
        self.settings = kwargs
        self.cmd_parameters = {}
        self.warp_var_rx = re.compile(r'<[\s\S]+?>')

        var_expressions = self.warp_var_rx.findall(self.raw_cmd)
        for exp in var_expressions:
            param_name = exp.lstrip('<').rstrip('>')
            self.cmd_parameters[param_name] = False        
            

    def has_default_value_for_param(self, param_name):
        return True if self.default_parameter_values.get(param_name) else False

    
    def default_value_for_param(self, param_name):
        return self.default_parameter_values.get(param_name)

    
    @property
    def parameters(self):
        return self.cmd_parameters.keys()


    @property
    def command_line(self):
        return self.raw_cmd


    def get_unpopulated_params(self, parameter_table):
        return [p for p in self.parameters if not parameter_table.get(p)]


    def build(self, parameter_tbl):
        cmd_params = self.warp_var_rx.findall(self.raw_cmd)
        target_command = self.command_line
        
        for source_param_string in cmd_params:            
            source_param_name = source_param_string.lstrip('<').rstrip('>')            
            target_param_value = parameter_tbl.get(source_param_name, self.default_value_for_param(source_param_name))            
            #if not target_param_value:
            #    raise ComposeException(source_param_string)
            if target_param_value:
                target_command = target_command.replace(source_param_string, target_param_value)
            
        return target_command


class CommandTemplate(object):
    def __init__(self, yaml_cfg, **kwargs):
        self.command_line = yaml_cfg['line'].strip()
        self._defaults = {}
        for tbl in yaml_cfg['defaults']:
            self._defaults[tbl['param']] = tbl['value']
        

    def defaults(self):
        return self._defaults


    
class CommandGroup(object):
    def __init__(self, name, **kwargs):
        self.templates = []
        self.name = name
        self.index = 0
        

    def append(self, command_template):            
        self.templates.append(command_template)

        
    def template_count(self):
        return len(self.templates)

    
    def current_template(self):
        if not self.template_count():
            raise Exception('Attempted to retrieve a command template from an empty command group.')
        return self.templates[self.index]

    
    def next_template(self):
        if self.index == len(self.templates) -1 :
            return self.templates[-1]
        self.index += 1
        return self.current_template()


    def previous_template(self):
        if self.index == 0:            
            return self.current_template
        self.index -= 1
        return self.current_template()

    
    
class CommandLoader(object):
    def __init__(self, warpfiles_dir, **kwargs):
        self.command_groups = {}      
        warpfiles = [os.path.join(warpfiles_dir, f) for f in os.listdir(warpfiles_dir) if f.endswith('yml') or f.endswith('yaml')]
        
        for filename in warpfiles:
            extension = filename.split('.')[-1]    
            groupname = os.path.basename(filename.rstrip('.%s' % extension))    
            with open(filename) as f:
                self.command_groups[groupname] = yaml.load(f)

    @property
    def group_names(self):
        return self.command_groups.keys()

                
    def load_command_group(self, group_name):        
        if not self.command_groups.get(group_name):
            raise NoSuchGroupException(group_name)

        cg = CommandGroup(group_name)
        for key, command_obj in self.command_groups[group_name]['commands'].iteritems():
            cg.append(CommandTemplate(command_obj))
            
        return cg


    def load_command(self, command_name, group_name):        
        command_obj = self.command_groups[group_name]['commands'].get(command_name)
        if not command_obj:            
            raise NoSuchCommandException(command_name, group_name)

        cg = CommandGroup(group_name)
        cg.append(CommandTemplate(command_obj))
        return cg
    

    
class UserEntry():
    def __init__(self, data):
        self.result = data.strip()
        self.is_empty = False
        if not self.result:
            self.is_empty = True


class InputPrompt():
    def __init__(self, prompt_string, default_value=''):
        self.prompt = prompt_string
        self.default = default_value

    def show(self):        
        result = raw_input(self.prompt).strip()
        if not result:
            result = self.default
        return result
    
    

class OptionPrompt(object):
    def __init__(self, prompt_string, options, default_value=''):
        self.prompt_string = prompt_string
        self.default_value = default_value
        self.options = options
        self.result = None

    def show(self):
        display_options = []
        for o in self.options:
            if o == self.default_value:
                display_options.append('[%s]' % o.upper())
            else:
                display_options.append(o)

        prompt_text = '%s %s  : ' % (self.prompt_string, ','.join(display_options))
        result = raw_input(prompt_text).strip()
        
        if not result: # user did not choose a value
            result = self.default_value

        return result

    
class Notifier():
    def __init__(self, prompt_string, info_string):
        self.prompt = prompt_string
        self.info = info_string

    def show(self):
        print '[%s]: %s' % (self.prompt, self.info)
        

        
            
class WarpCLI(Cmd):
    def __init__(self, command_group):
        # we always get a command group passed to the constructor, even if
        # it only has a single command
        Cmd.__init__(self)
        self.command_group = command_group
        self.process_command(self.command_group.current_template())
        self.prompt = '[warp-> ' # %
        

        
    def prompt_for_value(self, parameter_name, current_cmd):
        Notifier('command-template', current_cmd).show()

        parameter_value = InputPrompt('enter value for <%s>: ' % parameter_name).show()
        return parameter_value

        
    def do_hello(self, args):
        print 'Hello from the Warp CLI.'


    def do_quit(self, args):
        print 'Warp CLI exiting.'
        raise SystemExit

    
    def do_list(self, args):
        '''Lists the warp commands in the queue.'''
        for template in self.command_group.templates:
            self.show_template_info(Composer(template))
            print '\n'

        
    def do_shell(self, args):
        """Pass command to a system shell when line begins with '!'"""
        print 'executing shell command...'
        os.system(args)


    def show_template_info(self, composer):
        print '[command-template]: %s' % composer.raw_cmd
        defaults_list = []
        for name,value in composer.default_parameter_values.iteritems():
            defaults_list.append('    %s: %s' % (name, value))
        defaults_display = '\n'.join(defaults_list)
        print '[defaults]:\n%s' %  defaults_display


    def process_command(self, _command_template):
        composer = Composer(_command_template)
        print '[command-template]: %s' % composer.raw_cmd

        defaults_list = []
        for name,value in composer.default_parameter_values.iteritems():
            defaults_list.append('    %s: %s' % (name, value))
        defaults_display = '\n'.join(defaults_list)
        print '[defaults]:\n%s' %  defaults_display
        
        answer = OptionPrompt('populate with default values?', ['y', 'n'], 'y').show()

        user_params = {}
        
        if answer.lower() == 'y':
            user_params = dict(composer.default_parameter_values)
        #elif answer.lower() == 'n':            
        #    user_params = {}           
            
        empty_params = composer.get_unpopulated_params(user_params)
        for param_name in empty_params:
            new_param_value = self.prompt_for_value(param_name, composer.build(user_params))
            user_params[param_name] = new_param_value

        final_command = composer.build(user_params)
        
        
        
        print'[command]: %s' % final_command

        options = ['y', 'n']
        answer = OptionPrompt('execute command?', options, 'y').show()
        if answer.lower() == 'y':        
            self.do_shell(final_command)


    def do_next(self, args):
        '''Runs the next warp command in the queue.'''

        if not self.command_group.next_template():
            print 'no more commands in queue.'
        else:
            self.process_command(self.command_group.next_template())
            
        
        
    def do_go(self, args):
        '''Runs the current warp command in the queue.'''

        template =  self.command_group.current_template()
        logging.debug('params for current template: %s' % template.defaults())
        if not template:
            print 'end of command group.'
        else:
            self.process_command(template)

    do_q = do_quit
    do_ls = do_list

        
def read_env_var(var_name, mandatory=True):
    value = os.environ.get(var_name)
    if mandatory and not value:
        raise MissingEnvironmentVariableException(var_name)

    return value


'''
def load_command_groups(warpfiles_dir):
    groups = {}
    warpfiles = [os.path.join(warpfiles_dir, f) for f in os.listdir(warpfiles_dir) if f.endswith('yml') or f.endswith('yaml')]
    for filename in warpfiles:
        extension = filename.split('.')[-1]    
        groupname = os.path.basename(filename.rstrip('.%s' % extension))    
        with open(filename) as f:
            groups[groupname] = yaml.load(f)
        
    return groups
'''     


def show_commands_in_group(name, group_dict):
    return group_dict[name].keys()



def load_command(group_name, cmd_name, group_dict):    
    command_obj = group_dict[group_name]['commands'][cmd_name]
    return CommandTemplate(command_obj, group=group_name)
    

    
def load_command_group(group_name, group_dict):
    print 'command group data: %s' % group_dict
    print 'executing warp commands in group %s: %s' % (group_name, group_dict[group_name]['commands'].keys())

    templates = []
    for key, command_obj in group_dict[group_name]['commands'].iteritems():
        templates.append(CommandTemplate(command_obj, group=group_name))

    return templates
        


def is_command_designator(cmd_target_string):
    return cmd_target_string.find('.') != -1



def main():
    args = docopt(__doc__)

    cmd_options = {}
    cmd_options['preview_mode'] = True if args.get('--preview') else False
    cmd_options['group_target'] = True if args.get('--group') else False
    cmd_options['config'] = True if args.get('--config') else False
    cmd_options['list'] = True if args.get('ls') or args.get('<command_target>') == 'ls' else False
    
    warpfiles_dir = os.path.join(os.getcwd(), 'warpfiles')  

    loader = CommandLoader(warpfiles_dir)
    
    if cmd_options['list']:        
        target = args.get('<command_target>')

        if target == 'ls': # show everything
            for name in loader.group_names:
                print '%s' % (name)

        elif is_command_designator(target):
            print '### show contents of command %s.' % target
        else:            
            print '### show contents of command group %s.' % target
            print command_groups.keys()
                
    elif cmd_options['config']:
        print '### show warp config settings.'

    elif args.get('<command_target>'):
        target = args['<command_target>']

        # a target containing a '.' character is a command designator;
        # the format is <group_name>.<command_name>
        #
        if is_command_designator(target):
            cmd_tokens = target.split('.')            
            target_group_name = cmd_tokens[0]
            target_cmd = cmd_tokens[1]

            # load_command() will give us back a command  group,
            # but it will only have one command
            cmd_group = loader.load_command(target_cmd, target_group)
            WarpCLI(cmd_template).cmdloop()
            
        # anything else is a group designator            
        else:            
            cmd_group = loader.load_command_group(target)
            WarpCLI(cmd_group).cmdloop()

        

if __name__ == '__main__':
    main()
