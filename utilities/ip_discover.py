import socket
import ipaddress
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def generate_ips_in_subnet(local_ip, subnet_mask='24'):
    """Generate all IPs in the same subnet."""
    network = ipaddress.ip_network(f"{local_ip}/{subnet_mask}", strict=False)
    return [str(ip) for ip in network.hosts()]

def send_get_request(ip, timeout=1):
    """Send GET request to the IP."""
    try:
        response = requests.get(f"http://{ip}:5000/api/discover", timeout=timeout)
        return ip, response.status_code
    except Exception as e:
        return ip, None

def main():
    local_ip = get_local_ip()
    print(f"[+] Local IP: {local_ip}")

    ips = generate_ips_in_subnet(local_ip)
    print(f"[+] Scanning {len(ips)} IPs in subnet...")

    results = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_ip = {executor.submit(send_get_request, ip): ip for ip in ips}
        for future in as_completed(future_to_ip):
            ip, status = future.result()
            if status is not None:
                print(f"[+] {ip} responded with status code {status}")
                results.append((ip, status))
            else:
                print(f"[-] {ip} did not respond.")

    print("\n[+] Active HTTP responses:")
    for ip, status in results:
        print(f"{ip} -> {status}")

if __name__ == "__main__":
    main()