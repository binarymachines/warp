#!/usr/bin/env python
# warp: management tool for Ansible playbook config
# 
#
# Note: the docopt usage string must start on the first non-comment, non-whitespace line.
#

"""Usage: 
    warp
    warp <command_target>  
    warp ls 
    warp ls <command_target> 
    warp --config
	

Arguments:
    command_target   a group with multiple commands, or a single command of the format '<group>.<command>'

    
Options:
    -l, --list       List contents of command target, or list all command groups
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
from fnmatch import fnmatch
from types import MethodType
import logging
from inspect import getmembers, isfunction

from warp_common import Stack


EXTENSION_INIT_FILENAME = 'init.yml'
CMD_METHOD_PREFIX = 'do'
BORDER = '_________________________________________________________\n'
MARQUEE_BORDER = '==========================================================\n'

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



    
def load_config_var(value):
      var = None
      if not value:
          pass
      elif value.__class__.__name__ == 'list':
          var = value
      elif value.startswith('$'):
          var = os.environ.get(value[1:])            
          if not var:
              raise MissingEnvironmentVariableException(value[1:])
      elif value.startswith('~%s' % os.path.sep):
          home_dir = expanduser(value[0])
          path_stub = value[2:]
          var = os.path.join(home_dir, path_stub)
      else:
          var = value
      return var   
    

    

        
        
class JinjaTemplateManager:
    def __init__(self, j2_environment):
        self.environment = j2_environment
        
    def get_template(self, filename):
        return self.environment.get_template(filename)
        


def get_template_mgr_for_location(directory):
      j2env = jinja2.Environment(loader = jinja2.FileSystemLoader(directory))
      return JinjaTemplateManager(j2env)




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

            if target_param_value:
                target_command = target_command.replace(source_param_string, target_param_value)
            
        return target_command


class CommandTemplate(object):
    def __init__(self, name, yaml_cfg, **kwargs):
        self.name = name
        self.command_line = yaml_cfg['line'].strip()
        self._defaults = {}
        for tbl in yaml_cfg['defaults']:
            self._defaults[tbl['param']] = tbl['value']
        

    def defaults(self):
        return self._defaults


    
class CommandTemplateGroup(object):
    def __init__(self, name, **kwargs):
        self.templates = []
        self.name = name
        

    def add_template(self, command_template):            
        self.templates.append(command_template)

        
    def template_count(self):
        return len(self.templates)

           
    
class CommandLoader(object):
    def __init__(self, warpfiles_dir, **kwargs):
        self.command_template_groups = {}      
        warpfiles = [os.path.join(warpfiles_dir, f) for f in os.listdir(warpfiles_dir) if f.endswith('.yml') or f.endswith('.yaml')]
        
        for filename in warpfiles:
            extension = filename.split('.')[-1]    
            groupname = os.path.basename(filename.rstrip('.%s' % extension))    
            with open(filename) as f:
                self.command_template_groups[groupname] = yaml.load(f)


    def group(self, group_name):
        return self.command_template_groups.get(group_name)

                
    @property
    def group_names(self):
        return self.command_template_groups.keys()

                
    def load_command_templates_by_group(self, group_name):        
        if not self.command_template_groups.get(group_name):
            raise NoSuchGroupException(group_name)

        templates = []
        for key, command_obj in self.command_template_groups[group_name]['commands'].iteritems():
            templates.append(CommandTemplate(key, command_obj))
            
        return templates

    
    def load_command_templates_by_name_match(self, command_name_expr, group_name):
        #ctg = CommandTemplateGroup(group_name)
        
        candidates = self.command_template_groups[group_name]['commands'].keys()
        target_command_names = [name for name in candidates if fnmatch(name, command_name_expr)]

        templates = []
        for cmd_name in target_command_names:
            command_obj = self.command_template_groups[group_name]['commands'][cmd_name]            
            templates.append(CommandTemplate(cmd_name, command_obj))

        return templates        


    def load_command_template_by_name(self, command_name, group_name):        
        command_obj = self.command_template_groups[group_name]['commands'].get(command_name)
        if not command_obj:            
            raise NoSuchCommandException(command_name, group_name)

        return CommandTemplate(command_name, command_obj)


class MethodExtension(object):
    def __init__(self, name, bound_method_name, function, **kwargs):
        self.name = name
        self.bound_method_name = bound_method_name
        self.function = function        


    
    def load(self, target_class):
        setattr(target_class, self.bound_method_name, MethodType(self.function, None, target_class))

        
    @property
    def docstring(self):
        return self.function.__doc__
        

def is_valid_extension_name(fname):
    rx = re.compile(r'_{1}[^_]{1,}')
    if rx.match(fname):
        return True
    return False


    
class ExtensionManager(object):
    def __init__(self, warp_yaml_cfg, **kwargs):
        self.registry = {}
        print warp_yaml_cfg
        warp_home_dir = load_config_var(warp_yaml_cfg['globals']['warp_home'])
        extensions_dir = os.path.join(warp_home_dir, 'extensions')
        sys.path.append(extensions_dir)

        module_names = []
        should_load_all = False
        
        #  load context from the specified modules        
        module_names = warp_yaml_cfg.get('extensions') or []
            
        # otherwise load all modules
        '''
        else:
            should_load_all = True
            module_names = [f[0:-3] for f in os.listdir(extensions_dir) if f.endswith('.py')]
        '''                            
        for module_name in module_names:
            extensions = {}
            dirmod = __import__('extensions.%s' % module_name)
            extmod = getattr(dirmod, module_name)
            context_loader_function = getattr(extmod, '__load__')

            extension_args = {}
            for param in warp_yaml_cfg['extensions'][module_name]['init_params']:
                extension_args[param['name']] = param['value']

            print '### Extension params: %s' % extension_args
            extension_context = context_loader_function(warp_home_dir,
                                                        logger,
                                                        **extension_args)
           
            function_names = [f[0] for f in getmembers(extmod) if isfunction(f[1]) and is_valid_extension_name(f[0])]
                
            for raw_function_name in function_names:
                function_name = raw_function_name.lstrip('_')
                bound_method_name = '_'.join([CMD_METHOD_PREFIX, module_name, function_name])
                function_obj = getattr(extmod, raw_function_name)
                mx = MethodExtension(function_name, bound_method_name, function_obj)
                extensions[function_name] = mx
                
            self.registry[module_name] = extensions
            
                
    def bind_methods_to_class(self, target_class):
        for extension_dict in self.registry.values():
            for name, ext in extension_dict.iteritems():
                ext.load(target_class)

                
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
        


def is_command_designator(cmd_target_string):
    return cmd_target_string.find('.') != -1


def border():
    return BORDER

def marquee_border():
    return MARQUEE_BORDER


def header(title):
    return '\n%s\n%s' % (title, marquee_border())
                    
class WarpCLI(Cmd):
    def __init__(self, command_loader, extension_mgr):
        Cmd.__init__(self)
        self.command_loader = command_loader
        self.extension_manager = extension_mgr
        self.replay_stack = Stack()
        self.prompt = '[warp-> ' 
        
        
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
        detail_mode = False
        if args == '-d':
            detail_mode = True
        for name in self.command_loader.group_names:
            if detail_mode:
                print '%s:' % name
                for template in self.command_loader.load_command_templates_by_group(name):
                    print '    %s: %s' % (template.name, template.command_line)
            else:
                print name

                
    def do_lsx(self, args):
        '''List installed command extensions'''

        print header('Command extensions:')
        for module_name, extension_dict in self.extension_manager.registry.iteritems():
            print 'module: %s' % module_name
            print 'functions:'
            for key in extension_dict.keys():
                print '    %s : %s' % (key, extension_dict[key].docstring or '')
            print BORDER

            
    def do_shell(self, args):
        """Pass command to a system shell when line begins with '!'"""
        print 'executing shell command...'
        os.system(args)


    def completedefault(self, text, line, begidx, endidx):
        print 'completion stub'
        

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
            replay_context = {}
            replay_context['template'] = _command_template
            replay_context['params'] = user_params
            self.replay_stack.push(replay_context)

            

    def infer_target_command_groups(self, group_selector_string):
        return [name for name in self.command_loader.group_names if fnmatch(name, group_selector_string)]
        

            
    def parse_command_selector(self, selector):
        cmd_groups = []
        targets = {}        
        if is_command_designator(selector):
            cmd_tokens = selector.split('.')            
            group_string = cmd_tokens[0]
            cmd_string = cmd_tokens[1]
            return [group_string, cmd_string]

        return [selector]
    
           
    def do_go(self, args):
        '''Runs one or more selected warp commands.'''

        if args:
            target_tuple = self.parse_command_selector(args)
            command_templates = []
            group_selector = target_tuple[0]
            target_group_names = self.infer_target_command_groups(group_selector)
            if len(target_tuple) == 2:                
                command_selector = target_tuple[1]                
                for group_name in target_group_names:
                    command_templates.extend(self.command_loader.load_command_templates_by_name_match(command_selector, group_name))
            else:
                for group_name in target_group_names:
                    command_templates.extend(self.command_loader.load_command_templates_by_group(group_name))
                    
            for t in command_templates:                
                self.process_command(t)



    def do_replay(self, args):
        ''' Repopulates and re-runs the last command template.'''

        if self.replay_stack.size():
            replay_context  = self.replay_stack.pop()
            composer = Composer(replay_context['template'])
            params = replay_context['params']
            
            command_line = composer.build(params)
            self.do_shell(command_line)

        
                
    do_q = do_quit


    
def read_env_var(var_name, mandatory=True):
    value = os.environ.get(var_name)
    if mandatory and not value:
        raise MissingEnvironmentVariableException(var_name)

    return value



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
        

def do_xt(self, *args):
    print 'running an extension command!'
    



def main():
    args = docopt(__doc__)

    cmd_options = {}
    cmd_options['preview_mode'] = True if args.get('--preview') else False
    cmd_options['group_target'] = True if args.get('--group') else False
    cmd_options['config'] = True if args.get('--config') else False
    cmd_options['list'] = True if args.get('ls') or args.get('<command_target>') == 'ls' else False
    
    warp_home_dir = os.getcwd() # default is current directory
    warp_initfile = 'warp.ini' # TODO: use a default constant instead of magic string
    warp_config = None
    with open(warp_initfile) as f:
        warp_config = yaml.load(f)


    if not warp_config:
        raise Exception('missing warp.ini config file.')
        
    warp_home_dir = load_config_var(warp_config['globals']['warp_home'])        
    warpfiles_dir = os.path.join(warp_home_dir, 'warpfiles')
    extensions_dir = os.path.join(warp_home_dir, 'extensions')
    
    loader = CommandLoader(warpfiles_dir)
    extension_mgr = ExtensionManager(warp_config)
    extension_mgr.bind_methods_to_class(WarpCLI)
    
    cli = WarpCLI(loader, extension_mgr)
    cli.cmdloop()

        

if __name__ == '__main__':
    main()
