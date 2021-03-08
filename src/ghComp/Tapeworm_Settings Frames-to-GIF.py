
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

"""Configures a set of instructions for a FFmpeg frames-to-GIF conversion
    Inputs:
        IO: Tapeworm Input/output information
        Framerate: Optional framerate, by default 30
        StartFrame: Optional start frame, by default the first frame of the image sequence
        Loop : Optional loop count, by default 0 (infinite)
    Output:
        Settings: Set of Tapeworm instructions for a FFmpeg frames-to-GIF conversion
"""

ghenv.Component.Name = "Frames-to-GIF"
ghenv.Component.NickName = "Frames-GIF"
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "Tapeworm"
ghenv.Component.SubCategory = "2 | Settings"

__version__ = "0.2.7 (2021-03-06)"

##------------------------------ COMPONENT CODE --------------------------------

import sys
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
except:
    err = "No module named 'Tapeworm'. Is the same-titled folder " \
          + "available in '{}' ?".format(GH_COMPONENTS_FOLDER)
    ghenv.Component.AddRuntimeMessage(
        gh.Kernel.GH_RuntimeMessageLevel.Error, err
    )

# If Tapeworm is available, import the required classes and functions
if loaded:
    from Tapeworm import (InputOutput, SettingsFramesToGIF, is_integer_num,
                          is_num, IMG_FORMATS)


SUPP_FORMATS = list(IMG_FORMATS)
SUPP_FORMATS.remove("GIF")


def main(io, framerate, start_frame, loop):
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

    if loop is None:
        loop = 0  # default value
    else:
        if is_integer_num(loop):
            if int(float(loop)) < 0:  # fixes invalid string literal
                e = "Optional input parameter Loop must be " \
                    + "greater than or equal to 0"
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
            else:
                loop = int(loop)
        else:
            e = "Optional input parameter Loop must be an integer"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    # Configure the settings
    st = SettingsFramesToGIF(io, framerate, start_frame, loop)
    return st


if __name__ == "__main__":
    if loaded:
        Settings = main(IO, Framerate, StartFrame, Loop)
