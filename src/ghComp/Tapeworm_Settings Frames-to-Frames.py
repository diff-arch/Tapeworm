
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

"""Configures a set of instructions for a FFmpeg frames-to-frames conversion
    Inputs:
        IO: Tapeworm Input/output information
        Format: Image format to export to

    Output:
        Settings: Set of Tapeworm instructions for a FFmpeg frames-to-frames conversion
"""

ghenv.Component.Name = "Frames-to-Frames"
ghenv.Component.NickName = "Frames-Frames"
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "Tapeworm"
ghenv.Component.SubCategory = "2 | Settings"

__version__ = "0.2.6 (2021-06-05)"

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
from Tapeworm import (InputOutput, SettingsFramesToFrames, is_integer_num,
                      IMG_FORMATS)


SUPP_FORMATS = list(IMG_FORMATS)
SUPP_FORMATS.remove("GIF")


def main(io, image_format, sub_dirname):
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

    if image_format is None:
        w = "Input parameter Format failed to collect data"
        ghenv.Component.AddRuntimeMessage(
            gh.Kernel.GH_RuntimeMessageLevel.Warning, w
        )
        return
    else:
        if isinstance(image_format, str) and not is_integer_num(image_format):
            ext = image_format.strip().upper().replace(".", "")
            if ext not in SUPP_FORMATS:
                e = "'{}' is not a valid image format, ".format(image_format)
                e += "currently available formats include: {}" \
                    .format(", ".join(SUPP_FORMATS))
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return

            image_format = ext

        elif is_integer_num(image_format):
            idx = int(float(image_format))
            if idx < 0 or idx >= len(SUPP_FORMATS):
                options = ["{}: {}".format(i, fmt)
                           for i, fmt in enumerate(SUPP_FORMATS)]
                e = "{} is not a valid a image format choice, ".format(idx)
                e += "currently available formats include: {}" \
                    .format(", ".join(options))
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return

            image_format = SUPP_FORMATS[idx]

        else:
            e = "Optional input parameter ImageFormat must be a string, " \
                + "representing a image file extension, or an integer number " \
                + "from 0 to {}".format(len(SUPP_FORMATS) - 1)
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    # Desired file format is the same as the original format
    if image_format == io.input_fname.split(".")[-1].upper():
        e = "'{}' is already a {}.\n ".format(io.input_fname, image_format)
        e += "Unable to convert to the same file format."
        ghenv.Component.AddRuntimeMessage(
            gh.Kernel.GH_RuntimeMessageLevel.Error, e
        )
        return

    if not isinstance(sub_dirname, str):
        if sub_dirname is not None: # default value
            e = "Input parameter TargetSubfolder must be a string"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    # Configure the settings
    st = SettingsFramesToFrames(io, image_format, sub_dirname)
    return st


if __name__ == "__main__":
    Settings = main(IO, Format, None)
