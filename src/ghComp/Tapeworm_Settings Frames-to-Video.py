# Tapeworm: FFmpeg Controller Grasshopper plug-in (GPL)
# initiated by Marc Differding and Antoine Maes
#
# This file is part of Tapeworm.
# GitHub : https://www.github.com/diff-arch/Tapeworm
# Food4Rhino : https://www.food4rhino.com/app/tapeworm
#
# Copyright (c) 2020-2021, Marc Differding and Antoine Maes <tapeworm.gh@gmail.com>
# Tapeworm is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 3 of the License,
# or (at your option) any later version.
#
# Tapeworm is distributed in the hope to be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tapeworm; if not see <http://www.gnu.org/licenses/>
#
# @license GPL-3.0 <http://www.gnu.org/licenses/gpl.html>

# -------------------------- COMPONENT INFORMATION -----------------------------

"""Configures a set of instructions for a FFmpeg frames-to-video conversion
    Inputs:
        IO: Tapeworm input/output information
        Framerate: Optional framerate, by default 30
        StartFrame: Optional start frame, by default the first frame of the image sequence
        Format: Optional output video format, by default 'MP4'
        Bitrate : Optional video quality between 0 and 12, by default 5
        Loop: Optional loop count, by default 1 (play once)
    Output:
        Settings: Set of Tapeworm instructions for a FFmpeg frames-to-video conversion
"""

ghenv.Component.Name = "Frames-to-Video"
ghenv.Component.NickName = "Frames-Video"
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "Tapeworm"
ghenv.Component.SubCategory = "2 | Settings"

__version__ = "0.2.8 (2021-03-06)"

# ------------------------------ COMPONENT CODE --------------------------------

import sys
import os

import Grasshopper as gh

# Add the Tapeworm installation directory to sys.path, if necessary
GH_COMPONENTS_FOLDER = gh.Folders.DefaultAssemblyFolder
if GH_COMPONENTS_FOLDER not in sys.path:
    sys.path.append(GH_COMPONENTS_FOLDER)
# Try to import from Tapeworm
loaded = False
try:
    from Tapeworm import __version__

    loaded = True
except ImportError:
    err = "No module named 'Tapeworm'. Is the same-titled folder " \
          + "available in '{}' ?".format(GH_COMPONENTS_FOLDER)
    ghenv.Component.AddRuntimeMessage(
        gh.Kernel.GH_RuntimeMessageLevel.Error, err
    )

# If Tapeworm is available, import the required classes and functions
if loaded:
    from Tapeworm import (InputOutput, SettingsFramesToVideo, is_integer_num,
                          is_num, VID_FORMATS, IMG_FORMATS)

SUPP_FORMATS = list(IMG_FORMATS)
SUPP_FORMATS.remove("GIF")


def main(io, framerate, start_frame, video_format, video_bitrate, loop):
    # Verify values of the component inputs
    if io is None:
        e = "Input parameter IO failed to collect data"
        ghenv.Component.AddRuntimeMessage(
            gh.Kernel.GH_RuntimeMessageLevel.Warning, e
        )
        return
    else:
        if not isinstance(io, InputOutput):
            e = "Data conversion failed from {} to I/O Information" \
                .format(type(io).__name__)
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

        ext = io.input_fname.split(".")[-1].upper()
        if ext not in SUPP_FORMATS:
            e = "'{}' does not have a valid file format, \n" \
                .format(io.input_fname)
            e += "currently supported formats include: \n{}" \
                .format(", ".join(sorted(SUPP_FORMATS)))
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if io.im is not None and io.im.get_start_number() < 0:  # is single image
        e = "This component does not work with single images"
        ghenv.Component.AddRuntimeMessage(
            gh.Kernel.GH_RuntimeMessageLevel.Error, e
        )
        return

    _, in_ext = os.path.splitext(io.input_fname)
    in_ext = in_ext.strip(".").upper()
    if in_ext not in SUPP_FORMATS:
        e = "'{}' is not a valid file format, ".format(in_ext)
        e += "currently supported formats include: \n{}" \
            .format(", ".join(SUPP_FORMATS))
        ghenv.Component.AddRuntimeMessage(
            gh.Kernel.GH_RuntimeMessageLevel.Error, e
        )
        return

    if framerate is None:
        framerate = 30  # default value
    else:
        if is_num(framerate):
            if float(framerate) <= 0:  # fixes invalid string literal
                e = "Optional input parameter Framerate must be greater than 0"
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
        else:
            e = "Optional input parameter Framerate must be a number"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if start_frame is None:
        start_frame = io.im.get_start_number()
    else:
        first_frame = io.im.get_start_number()
        last_frame = first_frame + len(io.im.get_sequence_files(False)) - 1
        if is_integer_num(start_frame):
            if first_frame > int(float(start_frame)) or \
                    int(float(start_frame)) >= last_frame:
                e = "Optional input parameter StartFrame must be bigger than or "
                e += "equal to {}, or smaller than {}".format(first_frame, last_frame)
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
            start_frame = int(start_frame)
        else:
            e = "Optional input parameter StartFrame must be an integer"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if video_format is None:
        video_format = "MP4"  # default value
    else:
        if isinstance(video_format, str) and not is_integer_num(video_format):
            vformat = video_format.strip().upper().replace(".", "")
            if vformat not in VID_FORMATS:
                e = "{} is not a valid video format, ".format(video_format)
                e += "currently available formats include: {}" \
                    .format(", ".join(VID_FORMATS))
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
            video_format = vformat
        elif is_integer_num(video_format):
            idx = int(float(video_format))
            if idx < 0 or idx >= len(VID_FORMATS):
                options = ["{}: {}".format(i, fmt)
                           for i, fmt in enumerate(VID_FORMATS)]
                e = "{} is not a valid a video format, ".format(idx)
                e += "currently available formats include: {}" \
                    .format(", ".join(options))
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
            video_format = VID_FORMATS[idx]
        else:
            e = "Optional input parameter VideoFormat must be a string, " \
                + "representing a video file extension, or an integer " \
                + "number from 0 to {}".format(len(VID_FORMATS) - 1)
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if video_bitrate is None:
        video_bitrate = 5.0  # default megabytes value
    else:
        if is_num(video_bitrate):
            if float(video_bitrate) < 0.1 or float(video_bitrate) > 12.0:
                e = "Optional input parameter VideoBitrate must be greater " \
                    + "than or equal to 0.1, and less than or equal to 12.0"
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
            else:
                # Convert from megabytes to octets and round to closest integer
                video_bitrate = float(video_bitrate)
        else:
            e = "Optional input parameter VideoBitrate must be a number " \
                + "greater than or equal to 0.1, and less than or equal to 12.0"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if loop is None:
        loop = 0  # default value
    else:
        if is_integer_num(loop):
            if int(float(loop)) < 0:  # fixes invalid string literal
                e = "Optional input parameter Loop must be greater than " \
                    + "or equal to 0"
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
            elif int(float(loop)) >= 15:  # excessive loop count message
                msg = "Setting an excessively high loop count for videos " \
                      + "can lead to huge file sizes and crash Rhino, " \
                      + "while FFmpeg keeps running in the background"
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Remark, msg
                )
            else:
                loop = int(loop)
        else:
            e = "Optional input parameter Loop must be an integer"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    # Configure the settings
    st = SettingsFramesToVideo(
        io, framerate, start_frame, video_format, video_bitrate, loop
    )

    return st


if __name__ == "__main__":
    if loaded:
        Settings = main(IO, Framerate, StartFrame, Format, Bitrate, Loop)
