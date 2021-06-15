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

##-------------------------- COMPONENT INFORMATION -----------------------------

"""Configures a set of instructions for a FFmpeg GIF-to-video conversion
    Inputs:
        IO: Tapeworm input/output information
        Format: Optional output video format, by default 'MP4'
        Bitrate: Optional video quality (between 0.1 and 15), by default 5
        Loop: Optional loop count, by default 1 (play the animation once)
    Output:
        Settings: Set of Tapeworm instructions for a FFmpeg GIF-to-video conversion
"""

ghenv.Component.Name = "GIF-to-Video"
ghenv.Component.NickName = "GIF-Video"
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "Tapeworm"
ghenv.Component.SubCategory = "2 | Settings"

__version__ = "0.2.3 (2021-06-05)"

##------------------------------ COMPONENT CODE --------------------------------

import sys

import Grasshopper as gh
import Rhino as rh


if "Tapeworm" not in sys.modules:
    plugin_path = gh.Folders.DefaultAssemblyFolder
    if plugin_path not in sys.path:
        sys.path.append(plugin_path)

    try:
        from Tapeworm import __version__
    except ImportError:
        sys.path.remove(plugin_path)

        # Recurse the auto-install plug-in folders and
        # get directories with "active" versions of plug-ins
        avd = rh.Runtime.HostUtils.GetActivePlugInVersionFolders(True)
        # Return the Tapeworm installation directory, or None
        find_path = lambda: next((a.FullName for a in avd
                                  if a.FullName.find("Tapeworm") != -1), None)
        plugin_path = find_path()
        if plugin_path not in sys.path:
            sys.path.append(plugin_path)

        try:
            from Tapeworm import __version__
        except ImportError as e:
            raise e


# If Tapeworm is available, import the required classes and functions
from Tapeworm import (InputOutput, SettingsGIFToVideo, is_integer_num,
                      is_num, VID_FORMATS)


def main(io, video_format, video_bitrate, loop):
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
        if ext != "GIF":
            e = "'{}' does not have a valid file format, \n" \
                .format(io.input_fname)
            e += "currently supported formats include: GIF"
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
                e = "'{}' is not a valid video format, ".format(video_format)
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
                e = "{} is not a valid a video format choice, ".format(idx)
                e += "currently available choices include: {}" \
                    .format(", ".join(options))
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
            video_format = VID_FORMATS[idx]

        else:
            e = "Optional input parameter VideoFormat must be a string, " \
                + "representing a video file extension, or an integer number " \
                + "from 0 to {}".format(len(VID_FORMATS) - 1)
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if video_bitrate is None:
        video_bitrate = 5.0  # default megabytes value
    else:
        if is_num(video_bitrate):
            if float(video_bitrate) < 0.1 or float(video_bitrate) > 15.0:
                e = "Optional input parameter VideoBitrate must be greater " \
                    + "than or equal to 0.1, and less than or equal to 15.0"
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
            else:
                # Convert from megabytes to octets and round to closest integer
                video_bitrate = float(video_bitrate)
        else:
            e = "Optional input parameter Bitrate must be a number greater " \
                + "than or equal to 0.1, and less than or equal to 15.0"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if loop is None:
        loop = 1  # default value
    else:
        if is_integer_num(loop):
            if int(float(loop)) < 1:  # fixes invalid string literal
                e = "Optional input parameter Loop must be greater than " \
                    + "or equal to 1"
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
    st = SettingsGIFToVideo(io, video_format, video_bitrate, loop)
    return st


if __name__ == "__main__":
    Settings = main(IO, Format, Bitrate, Loop)
