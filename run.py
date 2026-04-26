from app import create_app, socketio
import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

app = create_app()

if __name__ == '__main__':
    local_ip = get_local_ip()
    print("="*60)
    print("🚀 Server is running!")
    print(f"👉 Local Access (Teacher):   http://localhost:5555")
    print(f"👉 Network Access (Students): http://{local_ip}:5555")
    print("   (Share the Network Access link with your students)")
    print("="*60)
    socketio.run(app, debug=True, host='0.0.0.0', port=5555, use_reloader=True)
