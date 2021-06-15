
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

"""Configures Tapeworm input/output information for file handling
    Inputs:
        SourcePath: Absolute path to an input file, for image sequences preferably to the
            first image in the sequence
        TargetFolder: Optional absolute path to an output folder, by default the source folder
        TargetFilename: Optional output filename, by default the modified source filename
    Output:
        IO: Tapeworm input/output information
"""

ghenv.Component.Name = "Input-Output Information"
ghenv.Component.NickName = "I/O"
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "Tapeworm"
ghenv.Component.SubCategory = "1 | I/O"

__version__ = "0.3.3 (2021-06-05)"

# ------------------------------ COMPONENT CODE --------------------------------

import sys
import os

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
from Tapeworm import (InputOutput, ImageSequence, on_windows,
                      IMG_FORMATS, VID_FORMATS)


# Generally supported file formats
SUPP_FORMATS = sorted(list(IMG_FORMATS + VID_FORMATS))
# Supported image sequence file formats
SUPP_IM_FORMATS = list(IMG_FORMATS)
if "GIF" in SUPP_IM_FORMATS:
    SUPP_IM_FORMATS.remove("GIF")
# Unsupported output file formats in Rhino 7.0 or earlier for Windows
BUG_IM_FORMATS = list(SUPP_IM_FORMATS)
if "PNG" in BUG_IM_FORMATS:
    BUG_IM_FORMATS.remove("PNG")


def main(in_path, out_fname, out_dir):
    im = None  # image sequence data

    # Verify values of the component inputs
    if in_path is None:
        e = "Input parameter SourcePath failed to collect data"
        ghenv.Component.AddRuntimeMessage(
            gh.Kernel.GH_RuntimeMessageLevel.Warning, e
        )
        return
    elif isinstance(in_path, str):
        if not os.path.isfile(in_path):
            e = "Path specified for input parameter SourcePath " \
                + "is not a valid filepath"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

        _, in_filename = os.path.split(in_path)
        _, in_ext = os.path.splitext(in_filename)
        in_ext = in_ext.strip(".").upper()

        if in_ext not in SUPP_FORMATS:
            e = "'{}' is not a valid file format, ".format(in_ext)
            e += "currently supported formats include: \n{}" \
                .format(", ".join(sorted(SUPP_FORMATS)))
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return
        else:
            if in_ext in SUPP_IM_FORMATS:
                # Buggy Rhino animate function fixed in Rhino 7.1
                if on_windows() and in_ext in BUG_IM_FORMATS:
                    w = "WARNING! In Rhino 7.0 or lower for Windows, " + \
                        "when exporting animation frames with the " + \
                        "animate function of Rhino or Grasshopper,\n" + \
                        "you HAVE to use the PNG format, as a bug " + \
                        "prevents creating any other format.\n" + \
                        "If your {} files were NOT made that way, ".format(in_ext)
                    w += "or you're using a later version of Rhino, " + \
                        "please ignore this warning."
                    ghenv.Component.AddRuntimeMessage(
                        gh.Kernel.GH_RuntimeMessageLevel.Warning, w
                    )

                try:
                    im = ImageSequence(in_path, SUPP_IM_FORMATS)
                    if len(im.messages) > 0:
                        msg = ".\n".join(im.messages)
                        ghenv.Component.AddRuntimeMessage(
                            gh.Kernel.GH_RuntimeMessageLevel.Remark, msg
                        )
                    # Detect incomplete sequences
                    gaps = im.detect_gaps()
                    if gaps is not None:
                        e = "The sequence '{}' appears to be incomplete." \
                            .format(im.get_dfs_filename())
                        e += "This may lead to unreliable results and thus " \
                             + "renaming the images is recommended."
                        ghenv.Component.AddRuntimeMessage(
                            gh.Kernel.GH_RuntimeMessageLevel.Warning, e
                        )
                except Exception as e:
                    e = "{}: {}".format(type(e).__name__, e)
                    ghenv.Component.AddRuntimeMessage(
                        gh.Kernel.GH_RuntimeMessageLevel.Error, e
                    )
                    return
            else:
                pass  # maybe add support for video sequences here
    else:
        e = "Input parameter SourcePath must be a string, " \
            + "representing an absolute file path"
        ghenv.Component.AddRuntimeMessage(
            gh.Kernel.GH_RuntimeMessageLevel.Error, e
        )
        return

    if out_fname is not None:  # defaults to None (not specified)
        if not isinstance(out_fname, str):
            e = "Input parameter TargetFilename must be a string"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if out_dir is not None:  # defaults to None (not specified)
        if isinstance(out_dir, str):
            if not os.path.isdir(out_dir):
                e = "Path specified for input parameter TargetFolder " \
                    + "is not a valid directory path"
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
        else:
            e = "Input parameter TargetFolder must be a string, " \
                + "representing an absolute directory path"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    # Instantiate I/O information
    io = InputOutput(in_path, out_fname, out_dir, im)
    return io


if __name__ == "__main__":
    IO = main(SourcePath, TargetFilename, TargetFolder)
