#!/usr/bin/env python
#
# database backup script for blocpower.nyc site
#
# Dexter Taylor
# binarymachineshop@gmail.com
#
#


'''Usage:
        db_backup.py <initfile>
        db_backup.py <initfile> [-p | --preview]
        db_backup.py (-h | --help)

Arguments:
        <initfile>      yaml initialization file
        
Options:
        -p --preview    show (but do not run) the database dump commands
        -h --help       show this screen. 

'''


import os, sys
import syslog
import sh
from docopt import docopt
import yaml
import time, datetime
import logging
import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key




class DatabaseBackupConfig():
    def __init__(self, host, schema, user, password, prefix, s3_bucket_name):        
        self.host = host
        self.schema = schema
        self.user = user
        self.password = password
        self.prefix = prefix
        self.s3_bucket_name = s3_bucket_name


    def run_post_backup(self, backup_file_path):
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        access_key_id = os.getenv('AWS_ACCESS_KEY_ID')

        if not secret_key:
            logging.error('missing environment variable AWS_SECRET_ACCESS_KEY; could not perform S3 upload.')
            return

        if not access_key_id:
            logging.error('missing environment variable AWS_ACCESS_KEY_ID; could not perform S3 upload.')
            return

        print 'backup file path: %s' % backup_file_path
        print 'target S3 bucket: %s' % self.s3_bucket_name
        
        print 'secret key: %s' % secret_key
        print 'access key id: %s' % access_key_id
        
        conn = S3Connection(access_key_id, secret_key)
        
        s3_bucket = conn.get_bucket(self.s3_bucket_name)
        k = Key(s3_bucket)
        k.key = os.path.basename(backup_file_path)
        k.set_contents_from_filename(backup_file_path)
        



    def generate_backup_command(self):        
        return "mysqldump --user=%s --password=%s --host=%s %s" % (self.user, self.password, self.host, self.schema)



    def run_backup(self, db_backup_dir):
        backup_filename = '%s_%s.sql' % (self.prefix, time.strftime('%m%d%Y-%H%M%S'))
        backup_file_path = os.path.join(db_backup_dir, backup_filename)

        cmd_string = self.generate_backup_command()

        tokens = cmd_string.split(' ')
        backup_command = sh.Command(tokens[0])
        args = tokens[1:]

        logging.debug('executing database backup command at %s' % current_datetime())
        output = backup_command(args, _out=backup_file_path)

        logging.info('backup command exited with code %s.' % output.exit_code)

        success = not output.exit_code
        if output.exit_code:
            logging.critical('backup command exited with error: %s' % output.exit_code)
        
        if success:
            self.run_post_backup(backup_file_path)
            



    def __repr__(self):
        return 'backup of schema "%s" in mysql instance on host: %s' % (self.schema, self.host)



def get_full_path(filename):
    if filename.startswith(os.path.sep):
        return filename

    if filename.startswith('~'):
        homedir = os.path.expanduser('~')
        return os.path.join(homedir, filename[1:])

    if filename.startswith('$'):
        return os.getenv(filename[1:])

    if filename == '.':
        return os.getcwd()

    return os.path.join(os.getcwd(), filename)



def load_yaml_config(filename):
    yaml_config = None
    with open(filename, 'r') as file:
        yaml_config = yaml.load(file)
        
    return yaml_config


def current_datetime():
    return datetime.datetime.now()



def execute_backup_command(cmd_string):
    
    tokens = cmd_string.split(' ')
    backup_command = sh.Command(tokens[0])
    args = tokens[1:]

    logging.debug('executing database backup command at %s' % current_datetime())

    output = backup_command(args)
    logging.debug('backup command exited with code %s.' % output.exit_code)
    if output.exit_code:
        logging.critical('backup command exited with error: %s' % output.exit_code)
    



def main(argv):
    args = docopt(__doc__)
    
    yaml_config = load_yaml_config(args['<initfile>'])
    preview_mode = args['--preview']

    logfile_path = get_full_path(yaml_config['globals']['logfile'])
    logging.basicConfig(filename=logfile_path, level=logging.ERROR)
    logging.debug('starting %s with initfile %s...' % (argv[0], args['<initfile>']))

    backup_file_path = get_full_path(yaml_config['globals']['backup_path'])

    db_configs = {}
    config_group = yaml_config['backups']
    for name in config_group:
        db_host = config_group[name]['host']
        db_schema = config_group[name]['schema']
        db_user = config_group[name]['user']
        db_password = config_group[name]['password']
        prefix = config_group[name]['filename_prefix']
        s3_bucket_name = config_group[name]['s3_bucket_name']
        
        db_configs[name] = DatabaseBackupConfig(db_host, db_schema, db_user, db_password, prefix, s3_bucket_name)

    
    if preview_mode:
        print '>>> generated database backup command(s):\n'

    for name in db_configs.keys():        
        backup_cmd = db_configs[name].generate_backup_command()
        
        if preview_mode:
            print '%s\n' % backup_cmd
        else:
            logging.debug(str(db_configs[name]))
            db_configs[name].run_backup(backup_file_path)



if __name__ == '__main__':
    main(sys.argv[1:])










