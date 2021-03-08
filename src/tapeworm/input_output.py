"""
(c) 2020-2021 Marc Differding and Antoine Maes <tapeworm.gh@gmail.com>
This file is part of Tapeworm.
https://www.github.com/diff-arch/Tapeworm
https://www.food4rhino.com/app/tapeworm
@license GPL-3.0 <https://www.gnu.org/licenses/gpl.html>

@version 1.0.0

Input/Output
"""

import os
import re
import shutil
from datetime import datetime

from utils import (compare, delete, extract_digit_format_specifiers,
                   strip_digit_format_specifier, is_file)
from config import IMG_FORMATS, VID_FORMATS, SPECIAL_CHARS


__version__ = "0.3.7 (2021-03-08)"


SUPP_OUT_FORMATS = sorted(list(IMG_FORMATS + VID_FORMATS))


class InputOutput:
    """Input/output information for file and directory handling.

    Arguments:
        input_path: An absolute path to the source file
        output_root: Optional target filename without extension, by default
            None, which sets output_root to the root of input_path
        output_dir: Optional absolute path to the target directory, by default
            None, which sets output_dir to the base directory of input_path
        im: Optionally an ImageSequence instance, by default None, which sets
            the mode to treatment of single file media formats (e.g. MP4, GIF)

    Attributes:
        input_path: An absolute path to the source file
        input_dir: An absolute path to the source directory
        input_fname: A source filename (with extension)
        output_path: An absolute path to the target file
        output_dir: An absolute path to the target directory
        output_root: A target filename without extension
        has_specific_out_root: True if the user has specified a
            custom target filename root, otherwise by default False
        culled_spec_chars: A dictionary mapping start indices of removed
            special characters from output_root to the characters themselves,
            when output_root defaults to the root of input_path and input_path
            refers to an image sequence. Otherwise the dictionary is empty
        im: An ImageSequence instance or None
    """

    def __init__(self, input_path, output_root=None, output_dir=None, im=None):
        global SUPP_OUT_FORMATS
        self.input_path = input_path
        self.input_dir, self.input_fname = os.path.split(input_path)
        self.im = im

        self.output_root = output_root  # filename WITHOUT extension
        self.has_specific_out_root = False
        self.culled_spec_chars = {}  # keeps track of removed special characters

        if self.output_root is not None:  # specified filename root
            root, ext = os.path.splitext(self.output_root)
            if ext.strip('.').upper() in SUPP_OUT_FORMATS:
                self.output_root = root
            self.has_specific_out_root = True
        else:  # filename root from input filename root
            self.output_root, _ = os.path.splitext(self.input_fname)

            # Image sequences input filename root treatment
            if self.im is not None and self.im.get_start_number() > -1:
                # Strip dfs and special characters from dfs_filename
                self.output_root, _ = os.path.splitext(self.im.get_dfs_filename())
                self.output_root, self.culled_spec_chars = strip_digit_format_specifier(
                    self.output_root, False, SPECIAL_CHARS
                )
                # Remove leading points used to define dot files on Unix systems
                if self.output_root.startswith('.'):
                    stripped_count = len(self.output_root)  # no. of removed dots
                    self.output_root = self.output_root.lstrip('.')
                    stripped_count -= len(self.output_root)
                    self.culled_spec_chars[0] = '.' * stripped_count

        self.output_dir = output_dir
        if output_dir is None:
            self.output_dir = self.input_dir

        self.output_path = os.path.join(self.output_dir, self.output_root)

    def rename_sequence_files(self, start_num=0):
        """Batch renames image sequence files. If self.input_dir is the same
            as self.output_dir the original sequence files get renamed,
            otherwise the files get renamed and moved to the new location.

        Args:
          start_num: Optional sequence start number, by default 0

        Raises:
          RuntimeError: Batch renaming is currently only supported
            for files that are part of an image sequence
          OSError: ...
          RuntimeError: Unable to move and rename any files from 'self.input_dir...'
          RuntimeError: Unable to rename any files from 'self.input_dir...'
        """
        if self.im is None:
            raise RuntimeError("Batch renaming is currently only supported \n"
                               + "for files that are part of an image sequence")

        if self.im.get_start_number() < 0:  # single image
            return self._rename_file()

        # Create a temporary directory to rename the files in
        dt = datetime.now()
        tmp_dir = os.path.join(self.input_dir, "tmp" + dt.strftime("%y%m%d%H%M%S"))
        try:
            os.mkdir(tmp_dir)
        except OSError as e:
            raise e

        files = self.im.get_sequence_files()
        dfs_fname = self.im.get_dfs_filename()
        idx, _ = extract_digit_format_specifiers(dfs_fname)
        re_fname = self.im.get_regex_filename()
        width = len(str(len(files) + start_num))  # file count width for zero padding
        count = start_num  # number of renamed and moved files

        # Rename and move the files to the temporary directory
        tmp_filepaths = []
        for f in files:
            source_fpath = os.path.join(self.input_dir, f)
            if not os.path.isfile(source_fpath):
                continue
            match = re.match(re_fname, f)
            if match is None:
                continue

            root, ext = os.path.splitext(f)
            stripped_root = ""
            if self.im.get_start_number() >= 0:
                stripped_root = root.replace(match.group(1), "")

            out_root = self.output_root
            if "%%" in out_root:
                out_root = out_root.replace("%%", "%")

            root = root.replace(match.group(1), str(count).zfill(width))
            if stripped_root != out_root:
                if idx < int(len(dfs_fname) / 2):
                    root = str(count).zfill(width) + out_root
                else:
                    root = out_root + str(count).zfill(width)

            tmp_fpath = os.path.join(tmp_dir, root + ext)
            if compare(self.input_dir, self.output_dir):  # rename files only
                try:
                    shutil.move(source_fpath, tmp_fpath)
                except OSError as e:
                    raise e
            else:  # move and rename files
                try:
                    shutil.copy(source_fpath, tmp_fpath)
                except OSError as e:
                    raise e
            count += 1
            tmp_filepaths.append(tmp_fpath)

        if count - start_num == 0:
            e = "Unable to move and rename any files from {}. "
            if compare(self.input_dir, self.output_dir):
                e = "Unable to rename any files from {}. "
            rc, msg = is_file(self.input_path)
            if not rc:
                e += msg
            delete(tmp_dir)  # cleanup the still empty temporary directory
            raise RuntimeError(e.format(self.input_dir))

        # Move the renamed files from the temporary to the output directory
        count = 0
        for fpath in tmp_filepaths:
            _, fname = os.path.split(fpath)
            destination_fpath = os.path.join(self.output_dir, fname)
            try:
                shutil.move(fpath, destination_fpath)
            except OSError as e:
                raise e
            count += 1

        if count == 0:
            e = "Unable to move renamed files from the temporary directory "
            e += "to {}. The renamed files can probably be recovered from {}"
            raise RuntimeError(e.format(self.output_dir, tmp_dir))

        # Delete the empty temporary directory
        delete(tmp_dir)

    def _rename_file(self):
        """Batch renames an image sequence of a single file. If self.input_dir
            is the same as self.output_dir the original file gets renamed,
            otherwise the file gets renamed and moved to the new location."""
        _, ext = os.path.splitext(self.input_fname)
        out_root = self.output_root

        if "%%" in out_root:
            out_root = out_root.replace("%%", "%")

        destination_path = os.path.join(self.output_dir, out_root + ext)
        if compare(self.input_dir, self.output_dir):  # rename files only
            try:
                shutil.move(self.input_path, destination_path)
            except OSError as e:
                raise e
        else:  # move and rename files
            try:
                shutil.copy(self.input_path, destination_path)
            except OSError as e:
                raise e

        rc, msg = is_file(destination_path)
        if not rc:
            e = "Unable to move and rename file from {}. "
            if compare(self.input_dir, self.output_dir):
                e = "Unable to rename file from {}. "
            e += msg
            raise RuntimeError(e.format(self.input_dir))

    def _to_string(self):
        """Returns an informative I/O string."""
        supp_img_formats = list(IMG_FORMATS)
        supp_img_formats.remove("GIF")
        _, ext = os.path.splitext(self.input_fname)

        msg = "TAPEWORM I/O Information [" \
              + "\n- input_path: " + self.input_path + ", "
        if ext.strip(".").upper() in supp_img_formats:
            msg += "\n- output_path: " + self.output_path + ".*"
        else:
            msg += "\n- output_path: " + self.output_path + "<%<0*>d>.*"
        msg += "\n]"

        return msg

    def __repr__(self):
        return self._to_string()
