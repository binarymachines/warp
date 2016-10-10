#!/usr/bin/env python
#
# python script for reassigning elastic IP addresses
#
# Dexter Taylor
# binarymachineshop@gmail.com
#
#

'''Usage:
	ip_reassign.py <soma_initfile> --address=<elastic_ip_address> --cluster=<cluster_name> [-p | --preview]


Arguments:
    <initfile>              soma YAML initialization file
    <elastic_ip_address>    address to be reassigned
    <cluster_name>          named cluster section in the soma init file    

Options:
    -p --preview            show (but do not execute) the specified reassignment
    
'''

import os, sys
import atexit
import syslog
from docopt import docopt
import yaml
import time
import logging
import datetime as dt
import boto
import re
from boto.ec2 import EC2Connection
import soma



class StateTransition():
    def __init__(self, state_tuple):
        if len(state_tuple) != 2:
            raise BadStateTupleException(state_tuple)

        self.initial_state = state_tuple[0]
        self.final_state = state_tuple[1]
        
 


def reassign_ipaddr(ip_address, cluster_host, ec2_conn):
    ec2_conn.disassociate_address(ip_address)
    ec2_conn.associate_address(cluster_host.instance_id, ip_address, None, None, None, True)
    


def get_eligible_transition_host(transition, cluster, statefile_data={}):
    transition_host = None

    if transition.initial_state == 'primary' and transition.final_state == 'failover':
        candidate_hosts = cluster.get_failover_hosts()
        if not len(candidate_hosts):
            raise NoAvailableFailoverHostException()

        # use the first failover host that's available
        for host in candidate_hosts:
            if check_host(host):
                transition_host = host
                break
    if transition.initial_state == 'failover' and transition.final_state == 'failover':
        candidate_hosts = cluster.get_failover_hosts()
        if not len(candidate_hosts):
            raise NoAvailableFailoverHostException()

        # use the next available failover host
        
        
            
    elif transition.initial_state == 'failover' and transition.final_state == 'failover':
        candidate_hosts = cluster.get_failover_hosts()
        

        

def load_addresses(ec2_conn):
    addr_table = {}
    addresses = ec2_conn.get_all_addresses()
    for addr in addresses:
        addr_table[addr.public_ip] = addr.allocation_id
    return addr_table



def load_running_instances(ec2_conn):
    instance_table = {}
    reservations = ec2_conn.get_all_reservations()
    for r in reservations:
        for inst in r.instances:
            if 'Name' in inst.tags and inst.state == 'running':
                instance_table[inst.tags['Name']] = inst
    return instance_table






def main(argv):
    args = docopt(__doc__)
    print args

    target_address = args['--address']
    cluster_name = args['--cluster']
    preview_mode = args['--preview']
    
    yaml_config = soma.load_yaml_config(args['<soma_initfile>'])    
    cfg_reader = soma.ConfigReader(yaml_config)

    logfile_path = soma.get_full_path(yaml_config['globals']['failover_logfile'])
    logging.basicConfig(filename=logfile_path, level=logging.INFO)    
    
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        
    conn = EC2Connection(access_key_id, secret_key)
    reservations = load_running_instances(conn)
    addresses = load_addresses(conn)

    ip_allocation_id = addresses.get(target_address)

    print 'address %s with ID %s' % (target_address, allocation_id)

    cluster = cfg_reader.load_cluster(cluster_name)
    primary_host = cluster.get_primary_host()
    failover_hosts = cluster.get_failover_hosts()

    print 'using cluster: %s' % cluster_name
    print 'primary host: %s' % primary_host
    print 'failover host(s): \n%s' % '\n'.join(str(fh) for fh in failover_hosts)

    transition_type = None
    
    # look for the statefile to figure out what state are we in. If the statefile doesn't exist,
    # we have failed during normal operation and are going from primary -> failover state.
    # If the statefile does exist, we have failed during a failover state (failover -> failover).
    #
    # In the first case we have to switch from the primary cluster host to the failover instance;
    # in the second we either have to switch from the failover host back to the primary,
    # or (if the primary is still down) to another failover host if we have more than one,
    # or else fail outright.
    #
    statefile_name = cfg_reader.read_statefile_name()
    statefile_path = soma.get_full_path(statefile_name)

    if not os.path.isfile(statefile_path):
        transition = StateTransition(('primary', 'failover'))
    else:
        transition = StateTransition(('failover', 'failover'))
    
    # the host returned from this routine must be a *running* instance
    target_cluster_host = get_eligible_transition_host(transition_type, cluster)


    if preview_mode:
        print 'preview mode: transition type is %s' % transition_type
        print 'ip address %s would be reassigned to cluster host %s.' % target_cluster_host
        print 'exiting without executing reassignment.'
        exit(0)


    if not target_cluster_host:
        # couldn't find a host to reassign to; we're going down
        
    else:        
        reassign_ipaddr(target_address, target_cluster_host)
        if target_cluster_host.role == 'primary':
            # we are changing from failover state to primary; delete the statefile
            os.remove(statefile_path)
        
    exit(0) 
     
        
    

if __name__ == '__main__':
    main(sys.argv[1:])



    
