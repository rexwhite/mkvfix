# MKV Tool

A GUI application for editing MKV file metadata (audio and subtitle track names and flags).

This is really just a UI, implemented as a tkinter wrapper around TCL/TK, that calls `mkvpropedit` 
to edit audio track and subtitle metadata in MKV files.

## Prerequisites

### System Dependencies
- Python 3.11+ (recommended for macOS compatibility)
  - On macOS: `brew install python@3.11 python-tk@3.11`
- [MKVToolNix](https://mkvtoolnix.download/) - Provides `mkvmerge` and `mkvpropedit` command-line tools
  - On macOS: `brew install mkvtoolnix`

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

The project includes a `mkvfix.spec` file for consistent builds.

### macOS Application Bundle

Using Poetry:
```bash
poetry run pyinstaller mkvfix.spec
```

Or using venv:
```bash
source venv/bin/activate
pyinstaller mkvfix.spec
```

This creates `mkvfix.app` in the `dist/` directory that can be dragged to Applications.

### macOS DMG Installer (Requires Python 3.10+)

First, install the optional dmg dependency:

Using Poetry:
```bash
poetry install --extras dmg
```

Or using venv:
```bash
pip install dmgbuild
```

Then build:

Using Poetry:
```bash
poetry run pyinstaller mkvfix.spec
poetry run dmgbuild -s dmgbuild_settings.py "mkvfix" dist/mkvfix.dmg
```

Or using venv:
```bash
source venv/bin/activate
pyinstaller mkvfix.spec
dmgbuild -s dmgbuild_settings.py "mkvfix" dist/mkvfix.dmg
```

The DMG file will be created in the `dist/` directory with a drag-to-Applications installer interface.

**Note:** Users will still need to install MKVToolNix separately (recommended via Homebrew: `brew install mkvtoolnix`).