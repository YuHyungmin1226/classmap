from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    print("🚀 Server is running! Open your browser and go to: http://localhost:5555")
    socketio.run(app, debug=True, host='0.0.0.0', port=5555, use_reloader=True)
