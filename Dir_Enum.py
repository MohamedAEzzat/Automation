# Description: A python script that automates web directory enumeration.

import argparse
import json
import re
import requests
from urllib3.exceptions import InsecureRequestWarning


def enumerate(base_url: str, dirs_file: str, recurse=False):
    # disable insecure HTTPS warning
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    valid_urls = []
    with open(dirs_file, 'r') as f:
        while True:
            tmp_dir = f.readline()
            if not tmp_dir:
                break
            tmp_dir = tmp_dir.strip()
            if tmp_dir == '':
                test_url = base_url
            else:
                if re.search(r'/$', base_url):
                    test_url = '{}{}'.format(base_url, tmp_dir)
                else:
                    test_url = '{}/{}'.format(base_url, tmp_dir)
            print('Checking {}'.format(test_url))
            result = requests.get('{}'.format(test_url), verify=False)
            if result.status_code == 200:
                url = result.url
                print('Found URL: {}'.format(url))
                valid_urls.append(url)
                if recurse and tmp_dir != '':
                    recurse_results = enumerate(url, dirs_file, recurse)
                    valid_urls.extend(recurse_results)
    return valid_urls


def main():
    parser = argparse.ArgumentParser(description='A web directory enumeration tool.')
    parser.add_argument('url', help='Base URL to search (must start with http:// or https://)')
    parser.add_argument('dirs_file', help='File containing directory names to enumerate')
    parser.add_argument('-r', '--recurse', help='Recursively enumerate sub-directories of discovered directories', action='store_true')
    parser.add_argument('-o', '--output', help='Output file to write to')
    parser.add_argument('-f', '--format', help='Output format (default is json)', default='json', choices=['json', 'plain'])
    args = parser.parse_args()

    base_url = args.url
    if not re.search(r'^https?://', base_url):
        print('Error, url parameter must begin with either http:// or https://')
        return
    dirs_file = args.dirs_file
    recurse = args.recurse
    output = args.output
    output_format = args.format

    print('Enumerating web directories.')
    valid_urls = list(set(enumerate(base_url, dirs_file, recurse)))

    if output:
        print('Writing output to {}.'.format(output))
        with open(output, 'w') as of:
            if output_format == 'json':
                json.dump(valid_urls, of, indent=2)
            else:
                for line in valid_urls:
                    of.write('{}\n'.format(line))
    else:
        print('Writing output to STDOUT.')
        if output_format == 'json':
            print(json.dumps(valid_urls, indent=2))
        else:
            for line in valid_urls:
                print(line)


if __name__ == '__main__':
    main()
