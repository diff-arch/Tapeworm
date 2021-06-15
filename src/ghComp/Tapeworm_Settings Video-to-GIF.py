
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

"""Configures a set of instructions for a FFmpeg video-to-GIF conversion
    Inputs:
        IO: Tapeworm input/output information
        Loop : Optional loop count, by default 0 (infinite)
    Output:
        Settings: Set of Tapeworm instructions for a FFmpeg video-to-GIF conversion
"""

ghenv.Component.Name = "Video-to-GIF"
ghenv.Component.NickName = "Video-GIF"
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "Tapeworm"
ghenv.Component.SubCategory = "2 | Settings"

__version__ = "0.2.2 (2021-06-05)"

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
from Tapeworm import (InputOutput, SettingsVideoToGIF, is_integer_num,
                      VID_FORMATS)


def main(io, loop):
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
        if ext not in VID_FORMATS:
            e = "'{}' does not have a valid file format, \n" \
                .format(io.input_fname)
            e += "currently supported formats include: \n{}" \
                .format(", ".join(sorted(VID_FORMATS)))
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
    st = SettingsVideoToGIF(io, loop)
    return st


if __name__ == "__main__":
    Settings = main(IO, Loop)
