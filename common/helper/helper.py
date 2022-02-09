import oci
import os
from termcolor import colored
from inspect import getframeinfo, stack
from datetime import datetime

CUSTOM_RETRY_STRATEGY = oci.retry.RetryStrategyBuilder().add_max_attempts(max_attempts=8) \
                                                        .add_total_elapsed_time(total_elapsed_time_seconds=600) \
                                                        .add_service_error_check(service_error_retry_config=  {   
                                                                                                            -1: [],
                                                                                                            409: ['IncorrectState'],
                                                                                                            429: [],
                                                                                                            500: [404], 
                                                                                                            500: [429] 
                                                                                                        },
                                                                                service_error_retry_on_any_5xx=True) \
                                                        .get_retry_strategy()



def get_tenancy_data(identity_client, config):
    try:
        tenancy = identity_client.get_tenancy(config["tenancy"]).data
    except Exception as e:
        raise RuntimeError("Failed to get tenancy: " + e)
    return tenancy



def get_networking_topology_per_compartment(network_client, compartment_id):
    return network_client.get_networking_topology(
        compartment_id,query_compartment_subtree = True,
        retry_strategy= CUSTOM_RETRY_STRATEGY
    ).data

def get_regions_data(identity_client, config):
    try:
        regions = identity_client.list_region_subscriptions(config["tenancy"]).data
    except Exception as e:
        raise RuntimeError("Failed to get regions: " + e)
    return regions

def get_virtual_network_client(config, signer):
    try:
        virtual_network_client = oci.core.VirtualNetworkClient(config, signer=signer)
    except Exception as e:
        raise RuntimeError("Failed to create virtual network client: " + e)
    return virtual_network_client

def get_identity_client(config, signer):
    try:
        identity_client = oci.identity.IdentityClient(config, signer=signer)
    except Exception as e:
        raise RuntimeError("Failed to create identity client: " + e)
    return identity_client



def create_signer(config_profile, is_instance_principals, is_delegation_token):

    # if instance principals authentications
    if is_instance_principals:
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            config = {'region': signer.region, 'tenancy': signer.tenancy_id}
            return config, signer

        except Exception:
            print("Error obtaining instance principals certificate, aborting")
            raise SystemExit

    # -----------------------------
    # Delegation Token
    # -----------------------------
    elif is_delegation_token:

        try:
            # check if env variables OCI_CONFIG_FILE, OCI_CONFIG_PROFILE exist and use them
            env_config_file = os.environ.get('OCI_CONFIG_FILE')
            env_config_section = os.environ.get('OCI_CONFIG_PROFILE')

            # check if file exist
            if env_config_file is None or env_config_section is None:
                print(
                    "*** OCI_CONFIG_FILE and OCI_CONFIG_PROFILE env variables not found, abort. ***")
                print("")
                raise SystemExit

            config = oci.config.from_file(env_config_file, env_config_section)
            delegation_token_location = config["delegation_token_file"]

            with open(delegation_token_location, 'r') as delegation_token_file:
                delegation_token = delegation_token_file.read().strip()
                # get signer from delegation token
                signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(
                    delegation_token=delegation_token)

                return config, signer

        except KeyError:
            print("* Key Error obtaining delegation_token_file")
            raise SystemExit

        except Exception:
            raise

    # -----------------------------
    # config file authentication
    # -----------------------------
    else:
        try:
            config = oci.config.from_file(
                oci.config.DEFAULT_LOCATION,
                (config_profile if config_profile else oci.config.DEFAULT_PROFILE)
            )
            signer = oci.signer.Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=oci.config.get_config_value_or_default(
                    config, "pass_phrase"),
                private_key_content=config.get("key_content")
            )
            return config, signer
        except Exception:
            print(
                f'** OCI Config was not found here : {oci.config.DEFAULT_LOCATION} or env varibles missing, aborting **')
            raise SystemExit

def debug(msg, color=None):
    frame = getframeinfo(stack()[1][0])
    filename = os.path.splitext(os.path.basename(frame.filename))[0]
    lineno = str(frame.lineno)    

    debug_exp = get_current_date()+" DEBUG: "+filename+".py:"+lineno+" - "+str(msg)

    if (color == "red"):
        print(turn_red(debug_exp), flush=True)
    elif (color == "green"):
        print(turn_green(debug_exp), flush=True)
    elif (color == "yellow"):
        print(turn_yellow(debug_exp), flush=True)
    elif (color == "blue"):
        print(turn_blue(debug_exp), flush=True)
    elif (color == "magenta"):
        print(turn_magenta(debug_exp), flush=True)
    elif (color == "cyan"):
        print(turn_cyan(debug_exp), flush=True)
    elif (color == "grey"):
        print(turn_grey(debug_exp), flush=True)
    else:
        print(turn_white(debug_exp), flush=True)



def dye_return(msg):
    if(msg == "No"):
        return turn_red(msg)
    elif(msg == "Ok"):
        return turn_green(msg)


def turn_red(msg):
    return colored(msg, 'red')

def turn_green(msg):
    return colored(msg, 'green')

def turn_yellow(msg):
    return colored(msg, 'yellow')

def turn_blue(msg):
    return colored(msg, 'blue')

def turn_magenta(msg):
    return colored(msg, 'magenta')

def turn_cyan(msg):
    return colored(msg, 'cyan')

def turn_white(msg):
    return colored(msg, 'white')

def turn_grey(msg):
    return colored(msg, 'grey')


def get_compartments_data(identity_client, compartment_id):
    return oci.pagination.list_call_get_all_results(
        identity_client.list_compartments,
        compartment_id,
        compartment_id_in_subtree=True,
        lifecycle_state="ACTIVE",
        retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
    ).data

def get_ip_sec_connections_per_compartment(network_client, compartment_id):
    return oci.pagination.list_call_get_all_results(
        network_client.list_ip_sec_connections,
        compartment_id,
        retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
    ).data

def get_ip_sec_connections_tunnels_per_connection(network_client, ipsec_id):
    return oci.pagination.list_call_get_all_results(
        network_client.list_ip_sec_connection_tunnels,
        ipsec_id,
        retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
    ).data

def get_cross_connects_per_compartment(network_client, compartment_id):
    return oci.pagination.list_call_get_all_results(
        network_client.list_cross_connects,
        compartment_id,
        retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
    ).data