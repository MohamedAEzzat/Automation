# Description: A python script that automates DNS zone transfer and subdomain enumeration.

import argparse
import dns.query
import dns.resolver
import dns.zone
import json

def get_ns(tlz: str, soa=False):

    servers = []
    if not soa:
        ns = dns.resolver.resolve(tlz, 'NS')
        sn = [x.to_text() for x in ns]
    else:
        ns = dns.resolver.resolve(tlz, 'SOA')
        sn = [x.mname.to_text() for x in ns]
    for name in sn:
        ips = dns.resolver.resolve(name, 'A')
        for rdata in ips:
            servers.append(rdata.address)
    return servers



def do_xfr(tlz: str, server: str):
    try:
        z = dns.zone.from_xfr(dns.query.xfr(server, tlz, timeout=3.0))
        return z
    except:
        return None


def do_enum(tlz: str, subdomains_file: str, resolver=dns.resolver):
    domains = {}
    with open(subdomains_file, 'r') as f:
        for sub in f:
            sub = sub.strip()
            qname = '{}.{}'.format(sub, tlz)
            try:
                q = dns.resolver.resolve(qname)
                a = [a.address for a in q]
                domains[qname] = a
            except Exception as e:
                print(e)
                continue
    return domains


def main():
    parser = argparse.ArgumentParser(description='A DNS enumeration tool.')
    parser.add_argument('-x', '--skip-xfr',
                        help='Skip zone transfer attempt (default is to attempt before enumerating)',
                        action='store_true')
    parser.add_argument('-s', '--server', help='Specify DNS server to query (default is to use system resolver)')
    parser.add_argument('-o', '--output', help='Output file to write to')
    parser.add_argument('-f', '--format', help='Output format (default is json)', default='json',
                        choices=['json', 'plain'])
    parser.add_argument('-n', '--no-address', help='Print only the valid subdomains (do not print the rdata)',
                        action='store_true')
    parser.add_argument('tlz', help='Top-level zone to enumerate (i.e. google.com)')
    parser.add_argument('subdomains_file', help='File containing a list of subdomains to enumerate')
    args = parser.parse_args()

    server = args.server
    skip_xfr = args.skip_xfr
    output = args.output
    output_format = args.format
    no_address = args.no_address
    tlz = args.tlz
    subdomains_file = args.subdomains_file


    soa_server = get_ns(tlz, soa=True)[0]
    resolver = dns.resolver
    if server:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [server]
    
    if not skip_xfr:
        print('Trying zone transfer.')
        results = do_xfr(tlz, soa_server)
    
    print('Enumerating subdomains.')
    domains = do_enum(tlz, subdomains_file, resolver)

    if output:
        print('Writing output to {}.'.format(output))
        with open(output, 'w') as of:
            if output_format == 'json':
                if no_address:
                    json.dump(list(domains.keys()), of, indent=2)
                else:
                    json.dump(domains, of, indent=2)
            else:
                for k, v in domains.items():
                    if no_address:
                        of.write('{}\n'.format(k))
                    else:
                        of.write('{} : {}\n'.format(k, v))
    else:
        print('Writing output to STDOUT.')
        if output_format == 'json':
            if no_address:
                print(json.dumps(list(domains.keys()), indent=2))
            else:
                print(json.dumps(domains, indent=2))
        else:
            for k, v in domains.items():
                if no_address:
                    print(k)
                else:
                    print('{} : {}'.format(k, v))




if __name__ == '__main__':
    main()
