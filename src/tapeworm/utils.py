"""
(c) 2020-2021 Marc Differding and Antoine Maes <tapeworm.gh@gmail.com>
This file is part of Tapeworm.
https://www.github.com/diff-arch/Tapeworm
https://www.food4rhino.com/app/tapeworm
@license GPL-3.0 <https://www.gnu.org/licenses/gpl.html>

@version 1.0.0

Utilities
"""

from __future__ import print_function
from collections import OrderedDict
from subprocess import Popen, PIPE
import platform
import filecmp
import shutil
import shlex
import math
import sys
import os
import re


__version__ = "0.3.0 (2021-03-01)"


def compare(dir_path1, dir_path2, strict=False):
    """Compares two directories to find out whether they match or
        differ from one another.

    Args:
      dir_path1: The absolute path to the first directory to compare
      dir_path2: The absolute path to the second directory to compare
      strict: Optionally True to compare both paths directly,
        by default False to only compare the directory contents

    Raises:
      OSError: The specified path 'dir_path' does not exist
      OSError: The specified path 'dir_path' is not a valid directory

    Returns:
      True if the directories are the same, otherwise False.
    """
    for path in [dir_path1, dir_path2]:
        if not os.path.exists(path):
            raise OSError("The specified path '{}' does not exist"
                          .format(path))
        elif not os.path.isdir(path):
            raise OSError("The specified path '{}' is not a valid directory"
                          .format(path))
        else:
            continue

    if strict:
        if dir_path1 != dir_path2:
            return False

    if len(os.listdir(dir_path1)) != len(os.listdir(dir_path2)):
        return False
    else:
        dc = filecmp.dircmp(dir_path1, dir_path2)
        if len(dc.common) != 0 and len(dc.common_funny) == 0:
            return True
    return False


def delete(path):
    """Deletes a local file or directory with all its contents.

        Use cautiously, because deleted files and directories
        can probably not easily be recovered!

    Args:
      path (str): The absolute path to a file or directory to delete

    Raises:
      OSError: The specified path 'path' does not exist
      OSError: Unable to delete 'filename' in 'directory'
      OSError: Unable to delete 'path'

    Returns:
      True if the file or directory was deleted, otherwise False.
    """
    basedir, fname = os.path.split(path)
    if not os.path.exists(path):
        raise OSError("The specified path '{}' does not exist"
                      .format(path))
    elif os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            raise ("Unable to delete '{}' in '{}'"
                   .format(fname, basedir))
    elif os.path.isdir(path):
        try:
            shutil.rmtree(path)
        except OSError:
            raise ("Unable to delete '{}'".format(path))


def detect_tool(path, specific=None):
    """Checks whether path is an executable file, or optionally whether
        its filename can be detected at one or more specific locations.

    Args:
      path (str): The absolute path to an executable tool
      specific (str|list): Optional full directory path or
        list of paths

    Raises:
      IOError: Optional argument 'specific' is not an existing
        directory path
      AttributeError: Optional argument 'specific' is not a valid
        directory path
      AttributeError: Optional argument 'specific' does not contain
        any valid directory paths
      ValueError: Optional argument 'specific' must be passed a string
        or list of strings, representing directory paths, or None

    Returns:
      A tuple with True/False [0] and the executable path/None [1]
    """
    basedir, fname = os.path.split(path)
    if basedir:
        if is_executable(path):
            return True, path
    else:
        if specific is None:
            return False, None,
        elif isinstance(specific, str):  # check specific single locations
            if not os.path.exists(specific):
                raise IOError("Optional argument 'specific' is not an "
                              + "existing directory path")
            elif not os.path.isdir(specific):
                raise AttributeError("Optional argument 'specific' is not a "
                                     + "valid directory path")
            else:
                match = find_in(fname, specific)
                if match is not None and is_executable(match):
                    return True, match
        elif isinstance(specific, list):  # check list of specific locations
            io_count = 0  # I/O errors count
            for dir_path in specific:
                if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                    io_count += 1
                else:
                    match = find_in(fname, dir_path)
                    if match is not None and is_executable(match):
                        return True, match
            if io_count == len(specific):
                raise AttributeError("Optional argument 'specific' does not "
                                     + "contain any valid directory paths")
        else:
            raise ValueError("Optional argument 'specific' must be passed "
                             + "a string or list of strings, representing "
                             + "directory paths, or None")
    return False, None


def extract_digit_format_specifiers(filename):
    """Returns a tuple with an indices list [0] and digit format specifier list
        [1] or a tuple with a single index [0] and specifier [1] that exist in
        a string filename, or (None, None). The list of indices or single index
        indicate the position of the specifier in the filename string."""
    if not has_digit_format_specifier(filename):
        return None, None
    specifiers = re.findall(r"(%\d*d)", filename)
    indices = [filename.find(spec) for spec in specifiers]
    if len(specifiers) > 1:
        return indices, specifiers
    return indices[0], specifiers[0]


def fetch_dir(path, restrict=None, sort_files=True):
    """Searches for files of optionally supported type at a
        given directory path.

        Optionally files are sorted with sort(), which is not
        optimal to sort non-zero-padded sequence files!!
        For numbered file sequences - zero-padded or not -,
        it is thus recommended to use their class method
        ImageSequence.fetch_sequence_files().

    Args:
      path (str): An absolute path to a directory
      restrict (None|str|list): An allowed file extension (e.g. "JPG"),
        a list of allowed file extensions (e.g. ["JPG", "PNG", "TIFF"]),
        or by default None, if no restrictions apply
      sort_files (bool): By default True to sort the found files,
        otherwise False.

    Returns:
      A list of optionally sorted filenames of optionally restricted type.
      If path is not a valid directory an empty list gets returned.
    """
    files = []
    if not os.path.isdir(path):
        return files
    for f in os.listdir(path):
        fpath = os.path.join(path, f)
        if is_file(fpath, restrict)[0]:
            files.append(f)
    if sort_files and len(files) > 0:
        files.sort()
    return files


def find_in(name, path):
    """Searches a directory and its subdirectories for a name.

    Args:
      name (str): A name to search for
      path (str): The absolute path of a directory to search

    Returns:
      The absolute path of the first match, otherwise None.
    """
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
    return None


def get_length(spec):
    """Returns the maximum number of digits or length of an item
        of a number sequence, defined by a digit format specifier
        (e.g. '%d': 1, '%02d': 2, '%03d': 3, etc.)."""
    return len(str((get_max_count(spec) - 1)))


def get_max_count(spec):
    """Computes the maximum integer count for a given digit format specifier.

    Args:
      spec: A digit format specifier (e.g. '%d', '%03', ...)

    Raises:
      AttributeError: Argument 'spec' is not a valid digit format specifier
        (i.e. '%d' or '%0<n>d')
      OSError: Argument 'spec' has a maximum count that depasses the
        maximum available system integer

    Returns:
      The maximum integer count.

    To use:
      >>> get_max_count('%d')
      10
      >>> get_max_count('%03d')
      1000
    """
    if not has_digit_format_specifier(spec):
        raise AttributeError("Argument 'spec' is not a valid digit format "
                             + "specifier (i.e. '%d' or '%0<n>d')")

    size = int(spec[-2]) if spec[-2].isdigit() else 1
    if len(spec) > 4:
        offset = len(spec) - 1
        size = int(spec[-offset + 1:-1])
    num_digits = int(math.floor(1 + math.log10(int(size * "1"))))
    max_count = int(math.pow(10, num_digits))

    if max_count >= sys.maxint:
        raise OSError("Argument 'spec' has a maximum count that is greater"
                      + " than the maximum available system integer")

    return max_count


def has_digit_format_specifier(filename):
    """Returns True if a filename string includes a format specifier for
        zero-padded (i.e. 'my_file_%03d') or simple digits (i.e. '%d-my_file'),
        otherwise False."""
    return True if re.search(r"(%\d*d)", filename) else False


def invoke_tool(cmd):
    """Invokes a shell process by command using the subprocess module.

    Args:
      cmd (str): A shell command starting with the tool name or path,
        and usually followed by some arguments.

    Returns:
      The standard output [0] and standard error [1] of the process.
    """
    args = cmd
    if on_macos():
        args = shlex.split(cmd)

    # Run the command using subprocess
    process = Popen(args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    return stdout, stderr


def is_bool(val):
    """Returns True [0] and the boolean [1] if a value is a boolean,
        otherwise False [0] and None [1]."""
    if isinstance(val, bool):
        return True, val
    elif is_integer_num(val):
        if int(float(val)) == 0:  # fixes invalid string literal
            return True, False
        elif int(float(val)) == 1:
            return True, True
        else:
            return False, None
    elif isinstance(val, str):
        if val.strip() in ["true", "True"]:
            return True, True
        elif val.strip() in ["false", "False"]:
            return True, False
        else:
            return False, None
    else:
        return False, None


def is_blank(string):
    """Returns True if a string is None, blank, or empty, otherwise True."""
    return not (string and string.strip())


def is_executable(path):
    """Returns True, if the path exists, is a file, and can be executed,
        otherwise False is returned."""
    return os.path.isfile(path) and os.access(path, os.X_OK)


def is_file(path, restrict=None):
    """Verifies whether a path exists, points to a file, and if restrictions
        apply, whether the file is of a supported format.

    Args:
      path (str): An absolute path to a file
      restrict (None|str|list): An allowed file extension (e.g. "JPG"),
        a list of allowed file extensions (e.g. ["JPG", "PNG", "TIFF"]),
        or None, if no restrictions apply

    Raises:
      ValueError: Argument 'restrict' must be passed a string or
        list of strings, representing file extensions"

    Returns:
      True/False [0], and None/an error message [1].
    """
    if not os.path.exists(path):
        return False, "The specified path '{}' does not exist".format(path)
    if not os.path.isfile(path):
        return False, "The specified path '{}' is not a filepath".format(path)
    if restrict is not None:
        allowed_formats = []
        if isinstance(restrict, list):
            allowed_formats = restrict
        elif isinstance(restrict, str):
            allowed_formats.append(restrict)
        else:
            raise ValueError("Argument 'restrict' must be passed a string or " +
                             "list of strings, representing file extensions")
        basedir, filename = os.path.split(path)
        root, ext = os.path.splitext(filename)
        if ext.strip(".").upper() not in allowed_formats:
            return False, "'{}' is not a supported file format".format(ext)
    return True, None


def is_integer_num(val):
    """Returns True if a value is an integer number, otherwise False."""
    try:
        float(val)
    except ValueError:
        return False
    else:
        return float(val).is_integer()


def is_num(val):
    """Returns True if a value is a valid number, otherwise False."""
    try:
        float(val)
    except ValueError:
        return False
    return True


def levenshtein_distance(s, t, verbose=False):
    """Measures the difference between two sequences.

        Informally, the Levenshtein distance between two words is
        the minimum number of single-character edits - insertions,
        deletions or substitutions - required to change one word s
        into the other t.
        (cf. https://en.wikipedia.org/wiki/Levenshtein_distance)

    Args:
      s (str): A source string
      t (str): A target string
      verbose (bool): True to print the matrix, or False by default

    Returns:
      The Levenshtein distance between s and t.
    """
    # For all i and j, d[i, j] will hold the Levenshtein distance between
    # the first i characters of s and the first j characters of t
    d = [[0 for j in xrange(len(s) + 1)] for i in range(len(t) + 1)]
    # Source prefixes can be transformed into empty string by
    # dropping all characters
    for i in xrange(1, len(s) + 1):
        d[0][i] = i
    # Target prefixes can be reached from empty source prefix
    # by inserting every character
    for j in xrange(1, len(t) + 1):
        d[j][0] = j
    for j in xrange(1, len(t) + 1):
        for i in xrange(1, len(s) + 1):
            if s[i - 1] == t[j - 1]:
                substitution_cost = 0
            else:
                substitution_cost = 1
            # Deletion, insertion, and substitution costs
            d[j][i] = min(d[j][i - 1] + 1,
                          d[j - 1][i] + 1,
                          d[j - 1][i - 1] + substitution_cost)
    if verbose:  # print matrix
        for row in d:
            print(row)
    return d[-1][-1]


def mb_to_octets(val):
    """Converts a numerical value from megabytes to octets."""
    if not is_num(val):
        raise ValueError("Expected numerical value, got {} for argument 'val'"
                         .format(type(val).__name__))
    return val * 1000000


def on_windows():
    """Returns True if this script is used on Windows, otherwise False."""
    return platform.system() == "Windows"


def on_macos():
    """Returns True if this script is used on macOS, otherwise False."""
    return platform.system() == "Darwin"


def parse_digit_format_specifier(num_string):
    """Parses a number string as a digit format specifier.

    Args:
      num_string: An integer number as a string

    Raises:
      ValueError: Argument 'num_string' must be passed a
        string representing an integer number

    Returns:
      The digit format specifier.

    To use:
      >>> parse_digit_format_specifier('077')
      %03d
      >>> parse_digit_format_specifier('8')
      %d
    """
    try:
        n = int(num_string)
        padding = len(num_string)
        if padding > 1:
            pattern = "%0{}d".format(padding)
        else:
            pattern = "%d"
        return pattern
    except ValueError:
        raise ValueError("Argument 'num_string' must be passed a string "
                         + "representing an optionally zero-padded integer number")


def read_config(fpath, key):
    """Reads the string value mapped to key from a config file.

    Args:
        fpath (str): An absolute path to a config file
        key (str): A key to return the value for

    Returns:
        The value as a string/None [0], None/an error message [1].
    """
    _, fname = os.path.split(fpath)
    try:
        with open(fpath, 'r') as f:
            config = f.read()
    except IOError:
        return None, False, "Could not to read '{}'".format(fname)

    if is_blank(config):
        return None, False, "'{}' seems to be empty".format(fname)

    pattern = r'({}\s*=\s*)([^#\r\n]+)'.format(key)
    match = re.search(pattern, config)
    if match is None:
        return None, "Could not find '{}' in '{}'".format(key, fname)

    # Strip left and right whitespace and double quotes for strings
    return match.group(2).strip().strip('"'), None


def split_at_digit(root, join_mid=False):
    """Splits the root of a filename at digits into a dictionary
        that maps its segments to the keys 'head', 'mid', and 'tail'.
        The mid section (i.e. 'mid') is None, if the root segmentation
        results in only two parts. If it results in a single part the
        tail section is also None.

    Args:
      root (str): A filename without extension
      join_mid (bool): True to join the list of strings of the
        midsection, or by default False to keep them separate

    Returns:
      The ordered dictionary of categorised root segements

    To use:
      >>> split('20200504_my-file_0075')
      {'head': '20200504', 'mid': '_my-file_', 'tail': '0075'}
      >>> split('my_file75')
      {'head': my_file, 'mid': None, 'tail': '75'}
      >>> split('my_file')
      {'head': my_file, 'mid': None, 'tail': None}
    """
    prev_isdigit = root[0].isdigit()  # previous char type (digit or not)
    split_root = [root[0]]  # list of strings
    substr_index = 0  # current substring index
    # Split the root string
    for i in range(1, len(root)):
        char = root[i]
        if not char.isdigit() and not prev_isdigit \
                or char.isdigit() and prev_isdigit:
            # Add to current substring
            split_root[substr_index] += char
        else:
            # Begin a new substring
            split_root.append(char)
            substr_index += 1
        prev_isdigit = char.isdigit()

    # Sort the split fragments into categories
    sorted_root = OrderedDict()
    # Get head
    sorted_root["head"] = split_root[0]
    # Get midsection
    if len(split_root) < 3:
        # Midsection does not exists
        sorted_root["mid"] = None
    else:
        midsection = split_root[1:-1]
        if len(midsection) == 1:
            # Midsection is composed of a single item
            midsection = midsection[0]
        else:
            # Midsection is composed of multiple items
            if join_mid:
                midsection = "".join(midsection)
        sorted_root["mid"] = midsection
    # Get tail
    if len(split_root) < 2:
        # Tail does not exist
        sorted_root["tail"] = None
    else:
        sorted_root["tail"] = split_root[-1]
    return sorted_root


def strip_digit_format_specifier(filename, has_ext, spec_chars=[]):
    """Strips the digit format specifier from a filename, and optionally
         removes special characters in its immediate vicinity.

    Args:
      filename (str): A filename with or without a digit format specifier
      has_ext (bool): Has to be set to False for filenames without extension,
        and otherwise to True. If this option is wrongly set, filenames with
        no extension and including dots are likely to get erroneously split,
        and stripping the digit format specifier thus fails.
      spec_chars (list): An optional list of special characters to remove
        around the digit format specifier, by default an empty list

    Returns:
      The stripped filename [0] and a dictionary mapping indices of
        where the special characters have been removed, to the characters
        themselves [1]. If the input filename has no digit format specifier,
        it gets returned unaltered.
    """
    root, ext = filename, ""
    if has_ext:
        root, ext = os.path.splitext(filename)
    culled_spec_chars = {}  # keeps track of removed special characters

    if not has_digit_format_specifier(root):
        return filename, culled_spec_chars

    idx, dfs = extract_digit_format_specifiers(root)
    if len(spec_chars) == 0:
        return root.replace(dfs, "") + ext, culled_spec_chars

    # Split the dfs filename root into at most two parts
    split_dfs_root = re.split(dfs, root, 1)

    # Parse the special character search patterns
    pattern_t_head = r"^([{}]+)".format('\\' + '\\'.join(spec_chars))
    pattern_h_tail = r"([{}]+)$".format('\\' + '\\'.join(spec_chars))

    # Remove special characters in direct vicinity of the dfs
    root_head, root_tail = "", ""
    if idx == 0:  # leading dfs
        root_tail = split_dfs_root[-1]
        match_tail = re.search(pattern_t_head, root_tail)
        if match_tail:
            chars_tail = match_tail.group(1)
            culled_spec_chars[0] = chars_tail
            root_tail = re.sub(pattern_t_head, r"", root_tail)

    elif idx == len(root) - len(dfs):  # trailing dfs
        root_head = split_dfs_root[0]
        match_head = re.search(pattern_h_tail, root_head)
        if match_head:
            chars_head = match_head.group(1)
            ci = len(root_head) - len(chars_head)
            culled_spec_chars[ci] = chars_head
            root_head = re.sub(pattern_h_tail, r"", root_head)

    else:  # in-between dfs
        root_head, root_tail = split_dfs_root
        match_head = re.search(pattern_h_tail, root_head)
        match_tail = re.search(pattern_t_head, root_tail)

        if match_head and match_tail:  # chars at root head AND tail
            chars_head = match_head.group(1)
            chars_tail = match_tail.group(1)

            if len(root_head) == len(chars_head) \
                    and len(root_tail) == len(chars_tail):
                # Root head and tail both are all chars
                culled_spec_chars[0] = chars_head
                culled_spec_chars[len(root_head)] = chars_tail
                root_head, root_tail = "", ""  # remove root head

            elif len(root_head) != len(chars_head) \
                    and len(root_tail) != len(chars_tail):
                # Root head and tail both are only part chars
                culled_spec_chars[len(root_head)] = chars_tail
                root_tail = re.sub(
                    pattern_t_head, r"", root_tail
                )  # remove root tail chars

            else:  # root head or tail is all chars
                if len(root_head) == len(chars_head):
                    # Root head is all chars
                    culled_spec_chars[0] = chars_head
                    root_head = ""  # remove root head

                if len(root_tail) == len(chars_tail):
                    # Root tail is all chars
                    ci = len(root_head)
                    culled_spec_chars[ci] = chars_tail
                    root_tail = ""  # remove root tail

        else:  # chars at root head OR tail
            if match_head:
                chars_head = match_head.group(1)
                if len(root_head) == len(chars_head):
                    # Root head is all chars
                    culled_spec_chars[0] = chars_head
                    root_head = ""  # remove root head

            if match_tail:
                chars_tail = match_tail.group(1)
                if len(root_tail) == len(chars_tail):
                    # Root tail is all chars
                    ci = len(root_head)
                    culled_spec_chars[ci] = chars_tail
                    root_tail = ""  # remove root tail

    # Reset to input filename if no root head and tail
    if len(root_head) == 0 and len(root_tail) == 0:
        culled_spec_chars.clear()
        return root.replace(dfs, ""), culled_spec_chars

    return root_head + root_tail + ext, culled_spec_chars


def to_re_pattern(spec, strict=True):
    """Turns a digit format specifier into a regular expression pattern.

    Args:
      spec: A digit format specifier (e.g. '%d', '%03', ...)
      strict: Optionally False to match a range of digits from a single to
        the maximum digit of the format specifier, by default True

    Raises:
      AttributeError: Argument 'spec' is not a valid digit format specifier
        (i.e. '%d' or '%0<n>d')

    Returns:
        The regular expression pattern.

    To use:
      >>> to_re_pattern('%d')
      r'\d+'
      >>> to_re_pattern('%03d')
      r'\d{3}'
      >>> to_re_pattern('%03d', False)
      r'\d{1,3}'
    """
    if not has_digit_format_specifier(spec):
        raise AttributeError("Argument 'spec' is not a valid digit "
                             + "format specifier (i.e. '%d' or '%0<n>d')")
    if spec != "%d":
        size = int(spec[-2]) if spec[-2].isdigit() else 1
        if len(spec) > 4:
            offset = len(spec) - 1
            size = int(spec[-offset + 1:-1])
        if strict:
            return r"\d{" + str(size) + r"}"
        else:
            return r"\d{1," + str(size) + r"}"
    return r"\d+"


def update_config(fpath, key, value):
    """Replaces the value of a key in a config file with a new value.

    Args:
      fpath (str): An absolute path to a config file
      key (str): A key to replace the value of
      value (str): A new value to replace with

    Returns:
      True/False [0], and None/an error message [1].
    """
    _, fname = os.path.split(fpath)
    try:
        with open(fpath, 'r') as f:
            config = f.read()
    except IOError:
        return False, "Could not to read '{}'".format(fname)

    if is_blank(config):
        return False, "'{}' seems to be empty".format(fname)

    pattern = r'({}\s*=\s*)(".*")'.format(key)
    match = re.search(pattern, config)
    if match is None:
        return False, "Could not find '{}' in '{}'".format(key, fname)

    old = ''.join(match.groups())
    new = '{}"{}"'.format(match.group(1), value)
    if old == new:  # new value is the same as the existing one
        return True, None  # skip
    updated_config = config.replace(old, new)
    if updated_config == config:
        return False, 'Failed to replace {} with "{}"'.format(
            match.group(2), value
        )

    try:
        with open(fpath, 'w') as f:
            f.write(updated_config)
    except IOError:
        return False, "Could not to write to '{}'".format(fname)

    return True, None


if __name__ == "__main__":
    print(strip_digit_format_specifier("%03d.", False, ["."]))
