"""
(c) 2020-2021 Marc Differding and Antoine Maes <tapeworm.gh@gmail.com>
This file is part of Tapeworm.
https://www.github.com/diff-arch/Tapeworm
https://www.food4rhino.com/app/tapeworm
@license GPL-3.0 <https://www.gnu.org/licenses/gpl.html>

@version 1.0.0

Configuration
"""

__version__ = "0.0.6 (2021-03-06)"

# MAC_SEARCH_PATH, WIN_SEARCH_PATH, FFMPEG_PATH can be customized
# Default FFmpeg paths
MAC_SEARCH_PATH = "/"  # macOS
WIN_SEARCH_PATH = "C:/"  # Windows

FFMPEG_PATH = ""  # absolute path of the FFmpeg executable

# IMG_FORMATS, VID_FORMATS, and SPECIAL_CHARS might break parts of the code if changed
# Supported file formats
IMG_FORMATS = ["BMP", "GIF", "JPG", "JPEG", "PNG", "TIF", "TIFF", "TGA"]
VID_FORMATS = ["AVI", "MKV", "MOV", "MP4", "MPG", "MPEG", "WEBM", "WMV"]

# Special characters to remove from output filenames derived from input filenames
SPECIAL_CHARS = ['.', ',', '/', '\\', '+', '-', '_', '|', '>', '<', '*', '%']
