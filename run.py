import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import create_app, socketio
import socket

import subprocess
import re

def get_all_local_ips():
    ips = []
    try:
        # Standard socket-based method to find the main local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Use a non-routable address to find the interface used for external traffic
        s.connect(('8.8.8.8', 80))
        primary_ip = s.getsockname()[0]
        ips.append(primary_ip)
        s.close()
    except Exception:
        pass

    # Try to get all IPs including fallback
    try:
        hostname = socket.gethostname()
        all_ips = socket.gethostbyname_ex(hostname)[2]
        for ip in all_ips:
            if not ip.startswith('127.'):
                ips.append(ip)
    except Exception:
        pass
            
    if not ips:
        ips.append('127.0.0.1')
            
    return list(set(ips))

app = create_app()

import os

if __name__ == '__main__':
    # Print only in the main worker process to avoid duplicating the message
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        local_ips = get_all_local_ips()
        print("="*60)
        print("Classroom Server is running!")
        print(f"Classroom Portal: http://localhost:5555")
        
        for i, ip in enumerate(local_ips):
            print(f"Network Access: http://{ip}:5555")
            
        print("   (Share the Network Access link with your students)")
        print("="*60)
        
    socketio.run(app, debug=True, host='0.0.0.0', port=5555, use_reloader=True)
