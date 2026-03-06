# MKV Tool

A GUI application for editing MKV file metadata (audio and subtitle track names and flags).

## Prerequisites

### System Dependencies
- Python 3.9+
- [MKVToolNix](https://mkvtoolnix.download/) - Provides `mkvmerge` and `mkvpropedit` command-line tools

### Linux Only
On Linux systems, you may need to install tkinter separately:
```bash
sudo apt-get install python3-tk  # Debian/Ubuntu
sudo yum install python3-tkinter  # RHEL/Fedora
```

## Setup

### Using Poetry (Recommended)

1. Install Poetry:
   ```bash
   pip install poetry
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Run the application:
   ```bash
   poetry run python mkvfix.py
   ```

### Using venv (Alternative)

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python mkvfix.py
   ```

## Building a Standalone Executable

### Basic Executable

Using Poetry:
```bash
poetry run pyinstaller mkvfix.py
```

Or using venv:
```bash
source venv/bin/activate
pyinstaller mkvfix.py
```

The executable will be created in the `dist/` directory.

### macOS Application Bundle
To create a proper macOS `.app` bundle:

Using Poetry:
```bash
poetry run pyinstaller --windowed --name="MKV Tool" mkvfix.py
```

Or using venv:
```bash
source venv/bin/activate
pyinstaller --windowed --name="MKV Tool" mkvfix.py
```

This creates `MKV Tool.app` in the `dist/` directory that can be dragged to Applications.

### macOS DMG Installer
To create a distributable `.dmg` installer:

Using Poetry:
```bash
poetry run pyinstaller --windowed --name="MKV Tool" mkvfix.py
poetry run dmgbuild -s dmgbuild_settings.py "MKV Tool" dist/MKVTool.dmg
```

Or using venv:
```bash
source venv/bin/activate
pyinstaller --windowed --name="MKV Tool" mkvfix.py
dmgbuild -s dmgbuild_settings.py "MKV Tool" dist/MKVTool.dmg
```

The DMG file will be created in the `dist/` directory with a drag-to-Applications installer interface.

**Note:** Users will still need to install MKVToolNix separately (recommended via Homebrew: `brew install mkvtoolnix`).