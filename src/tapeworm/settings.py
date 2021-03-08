"""
(c) 2020-2021 Marc Differding and Antoine Maes <tapeworm.gh@gmail.com>
This file is part of Tapeworm.
https://www.github.com/diff-arch/Tapeworm
https://www.food4rhino.com/app/tapeworm
@license GPL-3.0 <https://www.gnu.org/licenses/gpl.html>

@version 1.0.0

Settings
"""

__version__ = "0.5.6 (2021-03-06)"


import os

from utils import (mb_to_octets, strip_digit_format_specifier,
                   parse_digit_format_specifier)
from config import SPECIAL_CHARS


class ParentSettings:
    """Parent settings class that all other Tapeworm settings classes
        are children of.

    Arguments:
        io: An instance of the InputOutput class

    Attributes:
        input_path: An absolute path to the source file, which for image
             sequences is a path with a digit format specifier filename
        legacy_input_path: A backup of the original input path that is
            changed for images sequences to a digit format specifier path
        output_dir: An absolute path to the target directory
        output_path: An absolute path to the target file
        ffmpeg_cmd: A list with one or more FFmpeg command strings
    """

    def __init__(self, io):
        self.input_path = io.input_path
        self.legacy_input_path = io.input_path  # original input path
        self.output_dir = io.output_dir
        self.output_path = io.output_path

        if io.im is not None:  # image sequence or single image
            in_basedir, in_filename = os.path.split(self.input_path)
            dfs_filename = io.im.get_dfs_filename()
            self.input_path = os.path.join(in_basedir, dfs_filename)

        self.ffmpeg_cmd = []

    def _compile(self):
        """Compiles a basic FFmpeg command and should be overridden."""
        basic = "-i {} {}".format(self.input_path, self.output_path)
        self.ffmpeg_cmd.append(basic)

    def _to_string(self):
        """Returns an informative settings string."""
        str_cmd = "TAPEWORM Settings ["
        if len(self.ffmpeg_cmd) > 1:
            for i, cmd in enumerate(self.ffmpeg_cmd):
                str_cmd += "\n- ffmpeg_cmd {}: *ffmpeg {}".format(i + 1, cmd)
        else:
            str_cmd += "\n ffmpeg_cmd: *ffmpeg {}".format(self.ffmpeg_cmd[0])
        str_cmd += "\n]"
        return str_cmd

    def __repr__(self):
        return self._to_string()


## -----------------------------------------------------------------------------


class SettingsFramesToFrames(ParentSettings):
    """Structure handling the FFmpeg frames-to-frames settings,
        and a child of ParentSettings."""

    def __init__(self, io, output_ext, output_subdirname):
        ParentSettings.__init__(self, io)

        # I/O file handling
        self.output_ext = output_ext
        self.output_subdirname = output_subdirname

        out_basedir, out_fname = os.path.split(self.output_path)  # no extension
        # Set default output subdirectory for frames
        if self.output_subdirname is None:
            suffix = " [{}s]".format(self.output_ext)
            self.output_subdirname, _ = strip_digit_format_specifier(
                out_fname, False, SPECIAL_CHARS
            )  # strip dfs and special characters (if necessary)
            self.output_subdirname += suffix

        # Limit subdirectory usage to image sequences only
        if io.im.get_start_number() >= 0:
            self.output_dir = os.path.join(out_basedir, self.output_subdirname)

        # Set the default root of the output filename
        # An image sequence out_root has a dfs, but a single image one has none
        out_root, _ = os.path.splitext(io.im.get_dfs_filename())
        # Change specific out_root to user-defined description
        if io.has_specific_out_root:
            dfs = ""  # single image with empty dfs
            if io.im.get_start_number() >= 0:  # image sequence with custom dfs
                dfs = parse_digit_format_specifier(
                    str(len(io.im.get_sequence_files(False)))
                )
                dfs += "-"  # delimiter between dfs and user-defined out_root
            out_root = "{}{}".format(dfs, out_fname)

        self.output_path = os.path.join(self.output_dir, out_root)
        self.output_path += ".{}".format(self.output_ext.lower())

        self.im = io.im

        self._compile()

    def _compile(self):
        """Compiles a FFmpeg command for frames-to-frames conversion."""

        # Inverted quotes for Windows compatibility
        args = [
            '-i "{}"',
            '-y "{}"'
        ]

        start_num = self.im.get_start_number()
        if start_num >= 0:
            # start_number is only necessary for image sequences larger than 1
            # and must be inserted before -i for the input frames...
            args.insert(0, '-start_number {}'.format(start_num))
            # ... and before -y for the output frames
            args.insert(-1, '-start_number {}'.format(start_num))

        # RGBA colorspace has to be defined for JPGs, otherwise TIFFs
        # are produced that can't be opened in most programs
        if self.output_ext in ["TIF", "TIFF"]:
            _, in_ext = os.path.splitext(self.legacy_input_path)
            if in_ext.strip(".").upper() in ["JPG", "JPEG"]:
                # Insert behind '-i ...'
                if start_num < 0:  # single image
                    args.insert(1, '-pix_fmt rgba')
                else:  # image sequence
                    args.insert(2, '-pix_fmt rgba')

        # Keep JPGs and JPEGs from degrading their quality frame by frame
        if self.output_ext in ["JPG", "JPEG"]:
            _, in_ext = os.path.splitext(self.legacy_input_path)
            # Insert in front of '-y ...'
            if start_num < 0:  # single image
                args.insert(-1, '-q:v 1 -qmin 1 -qmax 1')
            else:  # image sequence
                args.insert(-2, '-q:v 1 -qmin 1 -qmax 1')

        frames = " ".join(args).format(
            self.input_path, self.output_path
        )

        self.ffmpeg_cmd.append(frames)


class SettingsFramesToGIF(ParentSettings):
    """Structure handling the FFmpeg frames-to-GIF settings,
        and a child of ParentSettings."""

    def __init__(self, io, framerate, start_frame, loop):
        ParentSettings.__init__(self, io)

        # I/O file handling
        self.output_ext = "GIF"
        self.output_path += ".{}".format(self.output_ext.lower())

        # Optional temporary file handling
        self.tmp_files = []
        self.tmp_fname = "palette.png"
        self.tmp_fpath = os.path.join(self.output_dir, self.tmp_fname)
        self.tmp_files.append(self.tmp_fpath)

        # Settings
        self.framerate = framerate
        self.start_frame = start_frame
        self.loop = loop
        self.im = io.im

        self._compile()

    def _compile(self):
        """Compiles two FFmpeg commands for frames-to-GIF conversion."""

        # Inverted quotes for Windows compatibility
        pargs = [
            '-start_number {}',
            '-i "{}"',
            '-vf palettegen',
            '-y "{}"'
        ]

        palette = " ".join(pargs).format(
            self.im.get_start_number(), self.input_path, self.tmp_fpath
        )
        self.ffmpeg_cmd.append(palette)

        gargs = [
            '-r {}',
            '-start_number {}',
            '-i "{}"',
            '-i "{}"',
            '-lavfi paletteuse',
            '-loop "{}"',
            '-y "{}"'
        ]

        gif = " ".join(gargs).format(self.framerate, self.start_frame,
                                     self.input_path, self.tmp_fpath,
                                     self.loop, self.output_path)

        self.ffmpeg_cmd.append(gif)


class SettingsFramesToVideo(ParentSettings):
    """Structure handling the FFmpeg frames-to-video settings,
        and a child of ParentSettings."""

    def __init__(self, io, framerate, start_frame, output_ext, vbitrate, loop):
        ParentSettings.__init__(self, io)

        # # I/O file handling
        self.output_ext = output_ext
        self.output_path += ".{}".format(self.output_ext.lower())

        # Settings
        self.framerate = framerate
        self.start_frame = start_frame
        self.video_bitrate = int(round(mb_to_octets(vbitrate)))
        self.loop = loop

        # Predefined settings
        self.compression = "veryslow"
        self.audio_format = "AAC".lower()
        self.audio_bitrate = 3500
        self.pix_fmt = "yuv420p"
        self.codec = "libx264"
        self.resolution = "crop=trunc(iw/2)*2:trunc(ih/2)*2"

        if self.output_ext == "WEBM":
            self.codec = "libvpx"
            self.resolution = "scale=-1:-1"

        self._compile()

    def _compile(self):
        """Compiles a FFmpeg command for frames-to-video conversion."""

        # Inverted quotes for Windows compatibility
        args = [
            '-r {}',
            '-start_number {}',
            '-stream_loop {}',
            '-i "{}"',
            '-vf {}',
            '-c:v {}',
            '-c:a {}',
            '-ar {}',
            '-b:v {}',
            '-pix_fmt {}',
            '-preset {}',
            '-y "{}"'
        ]

        video = " ".join(args).format(self.framerate, self.start_frame,
                                      self.loop, self.input_path,
                                      self.resolution, self.codec,
                                      self.audio_format, self.audio_bitrate,
                                      self.video_bitrate, self.pix_fmt,
                                      self.compression, self.output_path)

        self.ffmpeg_cmd.append(video)


class SettingsGIFToVideo(ParentSettings):
    """Structure handling the FFmpeg GIF-to-video settings,
        and a child of ParentSettings."""

    def __init__(self, io, output_ext, vbitrate, loop):
        ParentSettings.__init__(self, io)

        # # I/O file handling
        self.output_ext = output_ext
        self.output_path += ".{}".format(self.output_ext.lower())

        # Settings
        self.video_bitrate = int(round(mb_to_octets(vbitrate)))
        self.loop = loop - 1

        # Predefined settings
        self.compression = "veryslow"
        self.audio_format = "AAC".lower()
        self.audio_bitrate = 3500
        self.pix_format = "yuv420p"
        self.codec = "libx264"
        self.resolution = "crop=trunc(iw/2)*2:trunc(ih/2)*2"

        if self.output_ext == "WEBM":
            self.codec = "libvpx"
            self.resolution = "scale=-1:-1"

        self._compile()

    def _compile(self):
        """Compiles a FFmpeg command for GIF-to-video conversion."""

        # Inverted quotes for Windows compatibility
        args = [
            '-stream_loop {}',
            '-i "{}"',
            '-vf {}',
            '-c:v {}',
            '-c:a {}',
            '-ar {}',
            '-b:v {}',
            '-pix_fmt {}',
            '-preset {}',
            '-y "{}"'
        ]

        video = " ".join(args).format(
            self.loop, self.input_path, self.resolution, self.codec,
            self.audio_format, self.audio_bitrate, self.video_bitrate,
            self.pix_format, self.compression, self.output_path
        )

        self.ffmpeg_cmd.append(video)


class SettingsVideoToGIF(ParentSettings):
    """Structure handling the FFmpeg video-to-GIF settings,
        and a child of ParentSettings."""

    def __init__(self, io, loop):
        ParentSettings.__init__(self, io)

        # I/O file handling
        self.output_ext = "GIF"
        self.output_path += ".{}".format(self.output_ext.lower())

        # Optional temporary file handling
        self.tmp_files = []
        self.tmp_fname = "palette.jpg"
        self.tmp_fpath = os.path.join(self.output_dir, self.tmp_fname)
        self.tmp_files.append(self.tmp_fpath)

        # Settings
        self.loop = loop

        self._compile()

    def _compile(self):
        """Compiles two FFmpeg commands for Video-to-GIF conversion."""

        # Inverted quotes for Windows compatibility
        pargs = [
            '-i "{}"',
            '-vf palettegen',
            '-y "{}"'
        ]

        palette = " ".join(pargs).format(self.input_path, self.tmp_fpath)

        self.ffmpeg_cmd.append(palette)

        gargs = [
            '-i "{}"',
            '-i "{}"',
            '-lavfi paletteuse',
            '-loop {}',
            '-y "{}"'
        ]

        gif = " ".join(gargs).format(
            self.input_path, self.tmp_fpath, self.loop, self.output_path
        )

        self.ffmpeg_cmd.append(gif)


class SettingsVidGIFToFrames(ParentSettings):
    """Structure handling the FFmpeg video-to-frames and
        GIF-to-frames settings, and a child of ParentSettings."""

    def __init__(self, io, output_ext, start_frame, num_pattern,
                 framerate, output_subdirname):
        ParentSettings.__init__(self, io)

        # # I/O file handling
        self.output_ext = output_ext
        self.start_frame = start_frame
        self.num_pattern = num_pattern
        self.framerate = framerate
        self.output_subdirname = output_subdirname

        out_basedir, out_fname = os.path.split(self.output_path)
        if self.output_subdirname is None:
            suffix = " [{}s]".format(self.output_ext)
            self.output_subdirname = out_fname + suffix

        self.output_dir = os.path.join(out_basedir, self.output_subdirname)
        self.output_path = os.path.join(self.output_dir, out_fname)

        self.output_path += "{}.{}".format(
            self.num_pattern, self.output_ext.lower()
        )

        self._compile()

    def _compile(self):
        """Compiles a FFmpeg command for video/GIF-to-frames conversion."""

        # Inverted quotes for Windows compatibility
        args = [
            '-i "{}"',
            '-start_number {}',
            '-y "{}"'
        ]

        # Add framerate extraction if specified
        if self.framerate is not None:
            args.insert(1, '-r {}'.format(self.framerate))  # insert after '-i'

        # RGBA colorspace has to be defined for video, otherwise TIFFs
        # are produced that can't be opened in most programs
        if self.output_ext in ["TIF", "TIFF"]:
            _, in_ext = os.path.splitext(self.legacy_input_path)
            if in_ext.strip(".").upper() != "GIF":  # only video formats
                args.insert(-2, '-pix_fmt rgba')  # insert behind '-i' and '-r'

        # Keep JPGs and JPEGs from degrading their quality frame by frame
        if self.output_ext in ["JPG", "JPEG"]:
            _, in_ext = os.path.splitext(self.legacy_input_path)
            args.insert(-1, '-q:v 1 -qmin 1 -qmax 1')  # insert in front of '-y'

        frames = " ".join(args).format(
            self.input_path, self.start_frame, self.output_path
        )

        self.ffmpeg_cmd.append(frames)
