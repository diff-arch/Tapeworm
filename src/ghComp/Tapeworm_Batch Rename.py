
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

"""Configures a set of instructions for a Batch Renaming operation
    Inputs:
        IO: Tapeworm input/output information
        StartNumber : Optional number to start numbering from, by default 0
        Rename : Optionally True to rename files, by default False
"""

ghenv.Component.Name = "Batch Rename"
ghenv.Component.NickName = "BatchRename"
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "Tapeworm"
ghenv.Component.SubCategory = "3 | Run"

__version__ = "0.2.3 (2021-03-06)"

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
    from Tapeworm import InputOutput, is_bool, compare, is_integer_num


def main(io, start_num, rename):
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

    if start_num is None:
        start_num = 0  # default value
    else:
        if is_integer_num(start_num):
            if int(float(start_num)) < 0:  # fixes invalid string literal
                e = "Optional input parameter StartNumber must be greater" \
                    + " than or equal to 0"
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Error, e
                )
                return
            else:
                start_num = int(start_num)
        else:
            e = "Optional input parameter StartNumber must be an integer"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if rename is None:
        rename = False
    else:
        test, rename = is_bool(rename)
        if not test:
            e = "Input parameter Rename must be a boolean (i.e. True, False)," \
                + " 0 (False), or 1 (True)"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    # (Move and) rename the files
    if rename:
        try:
            io.rename_sequence_files(start_num)
        except Exception as e:
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, str(e)
            )
    else:
        if compare(io.input_dir, io.output_dir, True):
            e = "The initial files - defined by SourcePath -, are going to " \
                + "be renamed, \nsince the specified TargetFolder is equal " \
                + "to the source folder"
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Warning, e
            )


if __name__ == "__main__":
    main(IO, StartNumber, Rename)