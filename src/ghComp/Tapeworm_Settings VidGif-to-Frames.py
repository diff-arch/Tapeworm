
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

"""Configures a set of instructions for a FFmpeg Video/GIF-to-frames conversion
    Inputs:
        IO: Tapeworm input/output information
        Format: Optional image format, by default 'PNG'
        StartFrame: Optional start frame, by default 0 or
            in case of an image sequence, its start number
        Padding: Optional number of padded zeros, by default 0 which means no padding.
            When zero padding is used the padding MUST account for the total number of
            frames to be extracted, with for instance 3 you can pad up to 999 frames.
        Framerate: Optional number of frames per second that will be extracted.
            ALL frames are extracted by default!
    Output:
        Settings: Set of Tapeworm instructions for a FFmpeg Video/GIF-to-frames conversion
"""

ghenv.Component.Name = "VidGIF-to-Frames"
ghenv.Component.NickName = "VidGIF-Frames"
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "Tapeworm"
ghenv.Component.SubCategory = "2 | Settings"

__version__ = "0.2.6 (2021-03-06)"

# ------------------------------ COMPONENT CODE --------------------------------

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
except ImportError:
    err = "No module named 'Tapeworm'. Is the same-titled folder " \
          + "available in '{}' ?".format(GH_COMPONENTS_FOLDER)
    ghenv.Component.AddRuntimeMessage(
        gh.Kernel.GH_RuntimeMessageLevel.Error, err
    )

# If Tapeworm is available, import the required classes and functions
if loaded:
    from Tapeworm import (InputOutput, SettingsVidGIFToFrames, is_integer_num,
                          is_num, VID_FORMATS, IMG_FORMATS)


SUPP_OUT_FORMATS = list(IMG_FORMATS)
SUPP_OUT_FORMATS.remove("GIF")
SUPP_IN_FORMATS = list(VID_FORMATS)
SUPP_IN_FORMATS.append("GIF")


def main(io, image_format, start_frame, padding, framerate, sub_dirname):
    # Verify values of the component inputs
    if io is None:
        e = "Input parameter IO failed to collect data"
        ghenv.Component.AddRuntimeMessage(
            gh.Kernel.GH_RuntimeMessageLevel.Warning, e
        )
        return

    ext = io.input_fname.split(".")[-1].upper()
    if ext not in SUPP_IN_FORMATS:
        e = "{} is not a valid format for this setting component.\n " \
            .format(ext)
        e += "'SourcePath' input from the I/O component must refer to " + \
             "one of the following currently available formats:\n"
        e += "{}".format(", ".join(SUPP_IN_FORMATS))
        ghenv.Component.AddRuntimeMessage(
            gh.Kernel.GH_RuntimeMessageLevel.Error, e
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

    if image_format is None:
        image_format = "PNG"  # default value
    else:
        if isinstance(image_format, str) and not is_integer_num(image_format):
            iformat = image_format.strip().upper().replace(".", "")
            if iformat not in SUPP_OUT_FORMATS:
                e = "'{}' is not a valid image format, ".format(image_format)
                e += "currently available formats include: {}" \
                    .format(", ".join(SUPP_OUT_FORMATS))
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
            image_format = iformat
        elif is_integer_num(image_format):
            idx = int(float(image_format))
            if idx < 0 or idx >= len(SUPP_OUT_FORMATS):
                options = ["{}: {}".format(i, fmt)
                           for i, fmt in enumerate(SUPP_OUT_FORMATS)]
                e = "{} is not a valid a image format choice, ".format(idx)
                e += "currently available choices include: {}" \
                    .format(", ".join(options))
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
            image_format = SUPP_OUT_FORMATS[idx]
        else:
            e = "Optional input parameter ImageFormat must be a string, " \
                + "representing a image file extension, or an integer number " \
                + "from 0 to {}".format(len(SUPP_OUT_FORMATS)-1)
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if start_frame is None:
        start_frame = 0  # default value
    else:
        if is_integer_num(start_frame):
            if int(float(start_frame)) < 0:  # fixes invalid string literal
                e = "Optional input parameter StartFrame must be greater " \
                    + "than or equal to 0"
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
            else:
                start_frame = int(start_frame)
        else:
            e = "Optional input parameter StartFrame must be an integer"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if padding is None or 0 <= padding <= 1:
        num_pattern = "%d"  # default value (also for 0 and 1)
    else:
        if is_integer_num(padding):
            if int(float(padding)) < 1:  # fixes invalid string literal
                e = "Optional input parameter Padding must be greater than " \
                    + "or equal to 0"
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
            else:  # custom padding
                e = "Use custom zero padding cautiously! \nAn insufficient " + \
                    "number of padded zeros for the total number of \n" + \
                    "frames to export, may produce unequal padding results."
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Warning, e
                )

                num_pattern = "%d"  # str(0) and str(1)
                if int(padding) > 1:
                    num_pattern = "%0{}d".format(int(padding))

        else:
            e = "Optional input parameter Padding must be an integer"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if not isinstance(sub_dirname, str):
        if sub_dirname is not None:  # default value
            e = "Input parameter TargetSubfolder must be a string"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if framerate is not None:
        if not is_num(framerate) or framerate <= 0:
            e = "Input parameter Framerate must be a number larger than 0"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    # Configure the settings
    st = SettingsVidGIFToFrames(
        io, image_format, start_frame, num_pattern, framerate, sub_dirname
    )

    return st


if __name__ == "__main__":
    if loaded:
        Settings = main(IO, Format, StartFrame, Padding, Framerate, None)
