"""Check if Flask server is running and responding"""
import socket
import sys

def check_port(host, port, timeout=5):
    """Check if a port is open and accepting connections"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error checking port: {e}")
        return False

def main():
    host = "34.30.19.150"
    port = 5000
    
    print(f"Checking server at {host}:{port}...")
    
    if check_port(host, port):
        print(f"[OK] Port {port} is open and accepting connections")
        print("Server appears to be running but may be hanging on requests")
        print("\nPossible issues:")
        print("1. Database connection timeout")
        print("2. Query hanging (check database indexes)")
        print("3. Application error causing requests to hang")
    else:
        print(f"[ERROR] Port {port} is not accessible")
        print("\nPossible issues:")
        print("1. Server is not running")
        print("2. Firewall blocking port 5000")
        print("3. Server crashed on startup")
        print("\nTo start the server:")
        print("  py main.py")
        print("\nTo check if server is running locally:")
        print("  netstat -an | findstr :5000")

if __name__ == "__main__":
    main()
