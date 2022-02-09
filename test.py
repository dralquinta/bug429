import argparse
from common.helper.helper import *



def test_case():

    vpn_fc_connections_per_compartment = set()
    __topologies_with_cpe_connections_objects = []

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


    for com_region in vpn_fc_connections_per_compartment:
            region_needed = None
            for region in __regions:
                if com_region[1] == region.region_key.lower() or com_region[1] == region.region_name.lower() :
                    region_needed = config
                    region_needed['region'] = region.region_name
                    debug(region_needed,color = 'cyan')
                    n_client = get_virtual_network_client(region_needed, signer)
                    debug(region.region_name, "yellow")
                    n_client.base_client.endpoint = 'https://vnca-api.' + region.region_name + '.oci.oraclecloud.com'
                    __topologies_with_cpe_connections_objects.append(get_networking_topology_per_compartment(n_client,com_region[0]))


def __main__():
    test_case()


__main__()