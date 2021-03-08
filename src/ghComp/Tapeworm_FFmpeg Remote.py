
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

"""Main Tapeworm component that remotely communicates with FFmpeg
    Inputs:
        Settings: Set of instructions provided by a Tapeworm Settings component
        Overwrite: Optionally True to allow overwriting of existing files, by default False
        Send: Optionally True to send instructions to FFmpeg, by default False
"""

ghenv.Component.Name = "FFmpeg Remote"
ghenv.Component.NickName = "Remote"
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "Tapeworm"
ghenv.Component.SubCategory = "3 | Run"

__version__ = "0.2.9 (2021-03-06)"

# ------------------------------ COMPONENT CODE --------------------------------

import sys
import os
import re

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
    from Tapeworm import (ParentSettings, is_bool, detect_tool, invoke_tool,
                          delete, on_windows, has_digit_format_specifier,
                          is_blank, is_executable, update_config, read_config,
                          MAC_SEARCH_PATH, WIN_SEARCH_PATH)


CONFIG_PATH = os.path.join(GH_COMPONENTS_FOLDER, "Tapeworm/config.py")


def main(tool_path, settings, overwrite, send):

    def call_back(x):
        """Clear the data inside this component and all output parameters."""
        ghenv.Component.ClearData()

    if is_blank(tool_path):  # FFmpeg path is undefined
        # Set a platform-specific tool search location to check
        search_path = MAC_SEARCH_PATH
        if on_windows():
            search_path = WIN_SEARCH_PATH

        # Set a platform-specific tool executable to detect
        tool = "ffmpeg"
        if on_windows():
            tool += ".exe"

        # Detect FFmpeg installation
        ghenv.Component.Message = "Detecting FFmpeg"

        rc, tool_path = detect_tool(tool, search_path)
        if not rc:  # FFmpeg could not be found in search path
            e = "Unable to detect a FFmpeg installation in '{}'.\n" \
                .format(search_path)
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

        if on_windows():  # correct back- to forward slashes in Windows paths
            tool_path = re.sub(r'\\{1,2}', '/', tool_path)

        # Update config.py with detected FFmpeg path
        rc, msg = update_config(CONFIG_PATH, "FFMPEG_PATH", tool_path)
        if not rc:
            e = "Unable to save FFMPEG_PATH to 'config.py': "
            e += msg
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

        gh_doc = ghenv.Component.OnPingDocument() # get the Grasshopper document
        # Schedule this component to expire
        gh_doc.ScheduleSolution(1,
                                gh.Kernel.GH_Document.GH_ScheduleDelegate(call_back))

    else:  # FFmpeg path is already defined
        if not is_executable(os.path.join(tool_path)):
            # Spoof blank ffmpeg_path and recurse to re-run tool detection
            return main("", settings, overwrite, send)

    ghenv.Component.Message = None

    # Verify values of the component inputs
    if settings is None:
        e = "Input parameter Settings failed to collect data"
        ghenv.Component.AddRuntimeMessage(
            gh.Kernel.GH_RuntimeMessageLevel.Warning, e
        )
        return
    else:
        if not isinstance(settings, ParentSettings):
            e = "Data conversion failed from {} to Settings" \
                .format(type(settings).__name__)
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if overwrite is None:
        overwrite = False  # default value
    else:
        e = "Input parameter Overwrite must be set to a boolean " \
            + "(i.e. True, False), 0 (False), or 1 (True)"

        test, overwrite = is_bool(overwrite)
        if not test:
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    if send is None:
        send = False  # default value
    else:
        e = "Input parameter Send must be a boolean (i.e. True, False)," \
            + " 0 (False), or 1 (True)"
        test, send = is_bool(send)
        if not test:
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )
            return

    # Handle overwriting
    out_basedir, out_fname = os.path.split(settings.output_path)
    if not has_digit_format_specifier(out_fname):  # single file output
        if os.path.isfile(settings.output_path):
            if overwrite and send:
                # Remove existing file with the same filename
                try:
                    delete(settings.output_path)
                except Exception as e:
                    ghenv.Component.AddRuntimeMessage(
                        gh.Kernel.GH_RuntimeMessageLevel.Error, str(e)
                    )
                    return
            else:
                if send:
                    e = "'{}' already exists in '{}'. " \
                        .format(out_fname, out_basedir)
                    e += "Set the input parameter Overwrite to True, " \
                         + "to permit overwriting of the existing file"
                    ghenv.Component.AddRuntimeMessage(
                        gh.Kernel.GH_RuntimeMessageLevel.Warning, e
                    )
                    return

        else:
            # Create the output directory if it doesn't already exist
            if send and not os.path.exists(out_basedir):
                try:
                    os.mkdir(out_basedir)
                except OSError:
                    e = "Unable to create the output directory '{}'." \
                        .format(out_basedir)
                    ghenv.Component.AddRuntimeMessage(
                        gh.Kernel.GH_RuntimeMessageLevel.Error, e
                    )
                    return

    else:  # multi file output
        if os.path.isdir(out_basedir):
            if overwrite and send:
                # Remove existing frames folder with the same name
                try:
                    delete(out_basedir)
                except Exception as e:
                    ghenv.Component.AddRuntimeMessage(
                        gh.Kernel.GH_RuntimeMessageLevel.Error, str(e)
                    )
                    return
                # Create new empty frames folder
                try:
                    os.mkdir(out_basedir)
                except OSError:
                    e = "Unable to create the output directory '{}'." \
                        .format(out_basedir)
                    ghenv.Component.AddRuntimeMessage(
                        gh.Kernel.GH_RuntimeMessageLevel.Error, e
                    )
                    return
            elif overwrite and not send:
                e = "Enabling overwriting for multi file creation, deletes " \
                    + "the existing frames subfolder inside the TargetFolder" \
                    + ", including the contained files and subfolders"
                ghenv.Component.AddRuntimeMessage(
                    gh.Kernel.GH_RuntimeMessageLevel.Warning, e
                )
            else:
                if send:
                    e = "'" + out_basedir + "' already exists. Set the input " \
                        + "parameter Overwrite to True to permit overwriting " \
                        + "of the existing frames subfolder inside the " \
                        + "TargetFolder"
                    ghenv.Component.AddRuntimeMessage(
                        gh.Kernel.GH_RuntimeMessageLevel.Warning, e
                    )
                    return
        else:
            # Create the output directory if it doesn't already exist
            if send and not os.path.exists(out_basedir):
                try:
                    os.mkdir(out_basedir)
                except OSError:
                    e = "Unable to create the output directory '{}'." \
                        .format(out_basedir)
                    ghenv.Component.AddRuntimeMessage(
                        gh.Kernel.GH_RuntimeMessageLevel.Error, e
                    )
                    return

    # Communicate with FFmpeg
    if send:
        for cmd in settings.ffmpeg_cmd:
            ff_cmd = "{} {}".format(ffmpeg_path, cmd)
            stdout, stderr = invoke_tool(ff_cmd)

            if len(stdout) > 0:
                print " >", stdout
            if stderr is None:
                print " >", stderr

        # Clean up temporary files, if necessary
        if hasattr(settings, "tmp_files"):
            if len(settings.tmp_files) > 0:
                for f in settings.tmp_files:
                    try:
                        delete(f)
                    except Exception as e:
                        ghenv.Component.AddRuntimeMessage(
                            gh.Kernel.GH_RuntimeMessageLevel.Error, str(e)
                        )
                    return


if __name__ == "__main__":
    if loaded:
        # Get the FFMPEG_PATH from config.py
        ffmpeg_path, msg = read_config(CONFIG_PATH, "FFMPEG_PATH")
        if msg is not None:
            e = "Unable to get FFMPEG_PATH from 'config.py': "
            e += msg
            ghenv.Component.AddRuntimeMessage(
                gh.Kernel.GH_RuntimeMessageLevel.Error, e
            )

        main(ffmpeg_path, Settings, Overwrite, Send)
