import argparse
from common.helper.helper import *
import common.helper.ParallelExecutor as ParallelExecutor



def test_case():

    vpn_fc_connections_per_compartment = set()
    __topologies_with_cpe_connections_objects = []
    network_cleints = []

    

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', default="", dest='config_profile',
                        help='Config file section to use (tenancy profile)')
    parser.add_argument('-ip', action='store_true', default=False,
                        dest='is_instance_principals', help='Use Instance Principals for Authentication')           
    parser.add_argument('-dt', action='store_true', default=False,
                        dest='is_delegation_token', help='Use Delegation Token for Authentication')
    cmd = parser.parse_args() 

    config, signer = create_signer(cmd.config_profile, cmd.is_instance_principals, cmd.is_delegation_token)

    __identity = get_identity_client(config, signer)
    __regions = get_regions_data(__identity, config)
    __tenancy = get_tenancy_data(__identity, config)

    __compartments = get_compartments_data(__identity, __tenancy.id)

    for region in __regions:            
        region_config = config
        region_config['region'] = region.region_name     
        network_cleints.append(get_virtual_network_client(region_config, signer))




        __ip_sec_connections_objects = ParallelExecutor.executor(network_cleints, __compartments, ParallelExecutor.get_ip_sec_connections, len(__compartments), ParallelExecutor.ip_sec_connections)
        __cross_connections_objects = ParallelExecutor.executor(network_cleints, __compartments, ParallelExecutor.get_cross_connects, len(__compartments), ParallelExecutor.cross_connects)
        
        # find compartment and region with VPN or FastConnect
        for vpn_connections in __ip_sec_connections_objects:
            region = vpn_connections.id.split('.')[3]
            vpn_fc_connections_per_compartment.add((vpn_connections.compartment_id, region))

        for fc_connections in __cross_connections_objects:
            region = fc_connections.id.split('.')[3]
            vpn_fc_connections_per_compartment.add((fc_connections.compartment_id, region))

    for com_region in vpn_fc_connections_per_compartment:
            region_needed = None
            for region in __regions:
                if com_region[1] == region.region_key.lower() or com_region[1] == region.region_name.lower() :
                    region_needed = config
                    region_needed['region'] = region.region_name
                    debug(region_needed,color = 'cyan')
                    n_client = get_virtual_network_client(region_needed, signer)
                    debug(dir(signer), "blue")
                    debug(signer.region, "green")
                    debug(region.region_name, "yellow")
                    n_client.base_client.endpoint = 'https://vnca-api.' + region.region_name + '.oci.oraclecloud.com'
                    __topologies_with_cpe_connections_objects.append(get_networking_topology_per_compartment(n_client,com_region[0]))


def __main__():
    test_case()


__main__()