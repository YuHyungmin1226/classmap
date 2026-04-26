from app import create_app, socketio
import socket

import subprocess
import re

def get_all_local_ips():
    ips = []
    try:
        # Works on macOS / Linux
        output = subprocess.check_output(['ifconfig']).decode('utf-8')
        matches = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', output)
        for ip in matches:
            if not ip.startswith('127.'):
                ips.append(ip)
    except Exception:
        pass
        
    # Fallback
    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('10.255.255.255', 1))
            ips.append(s.getsockname()[0])
            s.close()
        except Exception:
            ips.append('127.0.0.1')
            
    return list(set(ips))

app = create_app()

if __name__ == '__main__':
    local_ips = get_all_local_ips()
    print("="*60)
    print("🚀 Server is running!")
    print(f"👉 Local Access (Teacher):   http://localhost:5555")
    
    for i, ip in enumerate(local_ips):
        print(f"👉 Network Access (Students {i+1}): http://{ip}:5555")
        
    print("   (Share the correct Network Access link with your students)")
    print("="*60)
    socketio.run(app, debug=True, host='0.0.0.0', port=5555, use_reloader=True)
