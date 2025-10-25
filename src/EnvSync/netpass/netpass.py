
import argparse
from EnvSync.netpass import network

if __name__=="__main__":

    parser = argparse.ArgumentParser(description="Network Passwords")

    filterGroup = parser.add_mutually_exclusive_group()
    filterGroup.add_argument("-name", type=str, help="case-insensitive network name filter")
    filterGroup.add_argument("-all", action="store_true", help="fetch all networks")
    filterGroup.required = True

    formatGroup = parser.add_mutually_exclusive_group()
    formatGroup.add_argument("-json", action="store_true", help="output as json format")
    formatGroup.add_argument("-csv", action="store_true", help="output as csv format")
    formatGroup.required = False

    parser.add_argument("-sep", default="|", type=str, help="network name | password separator")

    args = parser.parse_args()

    # SCRIPT START
    sep: str = args.sep
    
    networks = network.getNetworks(args.name)

    if args.json:

        [network.fetchPassword() for network in networks]
        print(network.toJson(networks), flush=True)
        exit(0)

    if args.csv:
        sep = ","

    for n in networks:
        print(f"{n.name}{sep}{n.fetchPassword()}", flush=True)