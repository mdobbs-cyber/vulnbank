import redis
import argparse
import sys

def ban_ip(ip_address):
    try:
        # Connect to Redis exposed on localhost
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        key = f"blacklist:{ip_address}"
        # Set persistent key
        r.set(key, "1")
        print(f"[+] Successfully banned IP: {ip_address}")
        
    except redis.ConnectionError:
        print("[-] Error: Could not connect to Redis at localhost:6379. Is Docker running?")
    except Exception as e:
        print(f"[-] Error banning IP: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ban an IP address from the Vulnerable Bank")
    parser.add_argument("ip", help="The IP address to ban")
    args = parser.parse_args()
    
    ban_ip(args.ip)
