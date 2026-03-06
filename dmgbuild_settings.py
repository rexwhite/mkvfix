# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Application bundle to package
application = 'dist/MKV Tool.app'

# Volume name
appname = 'MKV Tool'

# Format
format = 'UDBZ'

# Files to include
files = [application]

# Symlinks to create
symlinks = {
    'Applications': '/Applications'
}

# Icon locations
icon_locations = {
    'MKV Tool.app': (140, 120),
    'Applications': (500, 120)
}

# Background
background = None

# Window settings
window_rect = ((100, 100), (640, 280))

# Icon size
icon_size = 128

# Text size
text_size = 16
