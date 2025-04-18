import socket
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


NUM_SUBNETS_AROUND = 2  # How many subnets above and below to scan
PORT = 5000
ENDPOINT = '/api/discoverSPS'
TIMEOUT = 1  # seconds

# run this on a device on the same network as the RPi to find its IP
def get_local_ip():
    """Get the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def get_subnet_base(ip):
    """Return the base network address as an integer and the class C subnet string."""
    network = ipaddress.ip_network(f"{ip}/24", strict=False)
    return int(network.network_address), network

def generate_ips_in_adjacent_subnets(base_network_int, count=2):
    """Generate IPs from N subnets above and below the current subnet."""
    all_ips = []
    for offset in range(-count, count + 1):
        subnet_ip = ipaddress.IPv4Address(base_network_int + (offset << 8))
        network = ipaddress.ip_network(f"{subnet_ip}/24", strict=False)
        for host in network.hosts():
            all_ips.append(str(host))
    return all_ips

# def generate_ips_in_subnet(local_ip, subnet_mask='24'):
#     """Generate all IPs in the same subnet."""
#     network = ipaddress.ip_network(f"{local_ip}/{subnet_mask}", strict=False)
#     return [str(ip) for ip in network.hosts()]

def send_get_request(ip, port=PORT,endpoint=ENDPOINT,timeout=1):
    """Send GET request to the IP."""
    try:
        response = requests.get(f"http://{ip}:{port}{endpoint}", timeout=timeout)
        return ip, response.status_code
    except:
        return ip, None

def main():
    local_ip = get_local_ip()
    print(f"[+] Local IP: {local_ip}")

    # ips = generate_ips_in_subnet(local_ip)
    # print(f"[+] Scanning {len(ips)} IPs in subnet...")

    base_network_int, current_network = get_subnet_base(local_ip)
    print(f"[+] Scanning subnets around: {current_network}")

    ips = generate_ips_in_adjacent_subnets(base_network_int, NUM_SUBNETS_AROUND)
    print(f"[+] Total IPs to scan: {len(ips)}")

    results = []
    found = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        future_to_ip = {executor.submit(send_get_request, ip): ip for ip in ips}
        for future in as_completed(future_to_ip):
            ip, status = future.result()
            if status == 200:
                print(f"[+] {ip} responded with status code {status}")
                results.append((ip, status))
                found.append((ip,status))
            elif status is not None:
                print(f"[+] {ip} responded with status code {status}")
                results.append((ip, status))
            else:
                print(f"[-] {ip} did not respond.")

    print("\n[+] Active HTTP responses:")
    for ip, status in results:
        print(f"{ip} -> {status}")

if __name__ == "__main__":
    main()
