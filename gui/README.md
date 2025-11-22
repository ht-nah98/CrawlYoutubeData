# 💻 YouTube Analytics GUI Client

This is the GUI client component of the YouTube Analytics application. It provides a user-friendly interface that connects to the backend API server.

## 📋 Features

- **Modern UI** - Built with CustomTkinter
- **API Integration** - Connects to backend server
- **Configuration** - Customizable settings
- **Theme Support** - Dark/Light/System themes
- **Windows Ready** - Can be built as .exe

## 🏗️ Architecture

```
gui/
├── src/
│   ├── ui/           # User interface components
│   ├── api_client/   # Backend API client
│   ├── storage/      # Configuration and cache
│   └── utils/        # Utilities
├── assets/           # Icons and images
├── main.py           # Entry point
├── config.json       # Configuration
└── requirements.txt  # Dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd gui
pip install -r requirements.txt
```

### 2. Configure Backend URL

Edit `config.json`:

```json
{
  "backend_url": "http://localhost:8000",
  "theme": "dark"
}
```

### 3. Start Backend Server

**Important**: The GUI requires the backend server to be running!

```bash
cd ../backend
python server.py
```

### 4. Run GUI

```bash
cd gui
python main.py
```

Or use the startup script:
```bash
start_gui.bat
```

## ⚙️ Configuration

### config.json

| Setting | Description | Default |
|---------|-------------|---------|
| backend_url | Backend API URL | http://localhost:8000 |
| api_timeout | Request timeout (seconds) | 30 |
| theme | UI theme (dark/light/system) | dark |
| window_size | Window dimensions | 1200x800 |
| auto_connect | Auto-connect on startup | true |

## 🎨 Features

### Current Features
- ✅ Backend connection management
- ✅ Account viewing
- ✅ Statistics dashboard
- ✅ Settings configuration
- ✅ Theme switching

### Planned Features (Full Version)
- 🔄 Complete account management
- 🔄 Channel management
- 🔄 Video list and details
- 🔄 Analytics visualization
- 🔄 Scraping controls
- 🔄 Export functionality

## 🔧 Development

### Project Structure

```
gui/
├── src/
│   ├── ui/
│   │   └── main_window.py      # Main application window
│   ├── api_client/
│   │   └── client.py           # Backend API client
│   └── storage/
│       └── config.py           # Configuration management
├── main.py                     # Entry point
└── config.json                 # Settings
```

### Adding New Features

1. Create new UI components in `src/ui/`
2. Use `api_client` to communicate with backend
3. Store settings in `config.json`

## 📦 Building Windows Executable

### Install PyInstaller

```bash
pip install pyinstaller
```

### Build .exe

```bash
pyinstaller --onefile --windowed --name YouTubeAnalytics main.py
```

Or use the build spec (when created):
```bash
pyinstaller build.spec
```

Output will be in `dist/YouTubeAnalytics.exe`

### Build Options

- `--onefile` - Single executable file
- `--windowed` - No console window
- `--name` - Executable name
- `--icon` - Application icon (add your .ico file)

## 🐛 Troubleshooting

### "Cannot connect to backend"

**Solution**: Make sure the backend server is running:
```bash
cd backend
python server.py
```

### "Module not found" errors

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Backend URL incorrect

**Solution**: Update `config.json`:
```json
{
  "backend_url": "http://your-server:8000"
}
```

Or use the Settings button in the GUI.

## 🔌 API Client Usage

The GUI uses the `BackendAPIClient` to communicate with the backend:

```python
from src.api_client.client import BackendAPIClient

# Create client
client = BackendAPIClient("http://localhost:8000")

# Check connection
if client.health_check():
    print("Connected!")

# Get accounts
accounts = client.get_accounts()

# Create account
account = client.create_account("My Account", "cookies.json")
```

## 📝 Notes

### This is a Simplified Version

This GUI demonstrates the new architecture with:
- ✅ API-based communication
- ✅ Clean separation from backend
- ✅ Modular structure
- ✅ Configuration management

The full version will include all features from the original monolithic GUI.

### Migration from Original GUI

The original GUI (`src/gui/app.py`) is still available in the main project.
This new GUI is a cleaner, more maintainable version that:
- Uses the backend API instead of direct database access
- Can be deployed independently
- Can be built as a Windows .exe
- Is easier to maintain and extend

## 🎯 Next Steps

1. **Test the GUI** - Run and verify it works
2. **Migrate Features** - Port remaining features from original GUI
3. **Build .exe** - Create Windows executable
4. **Deploy** - Distribute to users

## 📞 Support

For issues:
1. Check backend is running
2. Verify `config.json` settings
3. Check console for error messages
4. Review backend logs

## 📄 License

Proprietary - All rights reserved

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-22
