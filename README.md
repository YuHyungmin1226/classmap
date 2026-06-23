# ClassMap (Classroom Map Application)

ClassMap is a real-time, interactive map application designed for classroom sessions. It allows an administrator to manage classes and map sessions, while participants can collaboratively drop pins, upload media (images and videos), share YouTube links, and write notes on a shared map in real-time.

## Features
- **Real-time Map Collaboration**: Synchronize pins and notes across all clients instantly using Socket.IO.
- **Media Uploads**: Attach images and videos to map pins with inline preview and playback.
- **YouTube Integration**: Simply paste a YouTube URL into a note to automatically embed the video player.
- **Hierarchy Management**: Administrators can create Classes, and within each Class, create multiple active Sessions.
- **Permissions**: Authors can edit and delete their own notes, while Administrators retain full moderation control.
- **Responsive UI**: Built with a sleek, modern, mobile-friendly interface using Leaflet.js.

### 🚀 Quick Start (Recommended)

#### For Windows Users:
Just double-click **`start_windows.bat`**. 
- It will automatically set up a portable Python environment and install all dependencies. No pre-installed Python required!

#### For macOS Users:
Run **`start_mac.command`**.
- It will set up the virtual environment and launch the server.

---

### Manual Installation (Optional)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YuHyungmin1226/classmap.git
   cd classmap
   ```

2. **Setup environment:**
   - **Windows**: `python -m venv venv` & `venv\Scripts\activate`
   - **macOS/Linux**: `python3 -m venv venv` & `source venv/bin/activate`

3. **Install dependencies & Run:**
   ```bash
   pip install -r requirements.txt
   python run.py
   ```
   The server will start on `http://localhost:5555`. 

4. **Admin Access:**
   Navigate to `/admin/login`. Default credentials:
   - Password: `admin123`
   (Note: You should change this in the Admin Menu after logging in.)

## Technologies Used
- **Backend**: Python, Flask, Flask-SocketIO, Flask-SQLAlchemy (SQLite)
- **Frontend**: HTML5, Vanilla CSS, JavaScript, Socket.io client
- **Mapping**: Leaflet.js, OpenStreetMap
- **Image Processing**: Pillow
