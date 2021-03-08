"""
(c) 2020-2021 Marc Differding and Antoine Maes <tapeworm.gh@gmail.com>
This file is part of Tapeworm.
https://www.github.com/diff-arch/Tapeworm
https://www.food4rhino.com/app/tapeworm
@license GPL-3.0 <https://www.gnu.org/licenses/gpl.html>

@version 1.0.0

ImageSequence
"""

from __future__ import print_function
import os
import re

from utils import (is_file, split_at_digit, levenshtein_distance,
                   parse_digit_format_specifier, fetch_dir,
                   extract_digit_format_specifiers, to_re_pattern)


__version__ = "0.7.5 (2021-03-06)"

# ------------------------------------------------------------------------------


class ImageSequence:
    """Analyses an image sequence from a first frame.

    If the real, existing first frame is not not provided, it is searched for
    and - if found - will replace the initially provided one as start frame.
    If only a single image is provided and no other images found in its base
    directory, the inital filename replaces the digit format sepecified one
    and -1 indicates that the sequence start could not be determined.
    However, When other images of the same type are discovered in the same
    location, but with different filenames an exception is raised.

    Arguments:
        path: An absolute path to the first image file in the sequence
        supp_formats: Optional list of supported image format strings

    To use:
        >>> im = ImageSequence("../Desktop/images/img_000.jpg")
        <__main__.ImageSequence instance at 0x00000000000000XX>
        >>> dfs_fname = im.get_dfs_filename()
        img_%03d.jpg
        >>> im.get_start_number()
        000
        >>> im.starts_at_zero()
        True
        >>> im.detect_gaps()
        None
    """

    def __init__(self, path, supp_formats=None):
        """Inits this ImageSequence."""
        self.path = path
        test, error = is_file(self.path, supp_formats)
        if not test:
            raise IOError(error)

        self.basedir, self.filename = os.path.split(self.path)

        # Raise error for filenames with percent symbols
        if "%" in self.filename:
            e = "The specified filename '{}' is not FFmpeg compliant. " \
              .format(self.filename)
            e += "It includes one or more % characters, "
            e += "which are currently not allowed."
            raise ValueError(e)

        self.root, self.ext = os.path.splitext(self.filename)
        self.head, self.mid, self.tail = split_at_digit(self.root).values()

        # Gets all files from the base directory with the same extension as path
        self.files = fetch_dir(self.basedir, self.ext.strip(".").upper())
        self.fcount = len(self.files)
        self.sequence_files = None
        self.messages = []
        if self.fcount < 2:  # single image
            # Set filename as digit format specifier filename
            self.dfs_filename = self.filename
            # Set the sequence start number to -1 to indicate missing sequence
            self.start_num = -1
            self.messages.append("Unable to find image sequence files, " +
                                 "other than '{}' at the specified path."
                                 .format(self.filename))
        else:  # image sequence
            # Get digit format specifier filename and initial image sequence number
            self.dfs_filename, self.start_num = self._parse_filename_pattern()
            # Verify the initial image number as real sequence start number
            self.start_num = self.get_start_number()

    def _predict_sequence(self, body, strict=False):
        """Predicts the part(s) of a filename root that is a/are number
            sequence(s), by comparing each of the components to the
            corresponding components of the filename roots inside the
            base directory.

        Args:
          body (list): Head, midsection, and tail of a filename root
          strict (bool): True, to check against all filename roots in
            the base directory, or by default False, to only compare
            to a minimum amount

        Raises:
          RuntimeError: Unable to predict number sequence for 'self.filename'

        Returns:
          A list of indices of the predicted body components.
        """
        # Get the max. number of files from the base directory to check
        max_count = int("1" + "".join(["0" for _ in range(len(
            str(self.fcount)) - 1)]))
        max_count = max_count if max_count > 10 else self.fcount
        # Predict the sequence(s)
        si = 0  # string start index of body component
        predicted = []  # indices of predicted sequence body components

        for i in xrange(len(body)):
            ln = len(body[i])  # string length of body component
            total_dist = 0  # total Levenshtein distance
            count = 0  # number of checked files

            for f in self.files:
                if not strict and count >= max_count:
                    break  # skip the remaining files
                fpath = os.path.join(self.basedir, f)
                if is_file(fpath, self.ext.strip(".").upper())[0] \
                        and f != self.filename:
                    froot, fext = os.path.splitext(f)
                    # Compute the Levenshtein distance
                    dist = levenshtein_distance(froot[si:si + ln], body[i])
                    total_dist += dist
                count += 1

            # Distances greater than zero mean a high sequence probability
            # because this body component changes from root to root, and
            # the digit verification filters out indices of body components
            # that are not numbers, especially important for a roots with
            # non-zero padded sequences, because the absence of padding
            # makes the root length bigger for higher ranging roots, and
            # thus a distance greater than 0 gets erroneously predicted
            if total_dist > 0 and body[i].isdigit():
                predicted.append(i)
            # Increment si to the start index of the next body component
            si += ln

        # if len(predicted) < 1 or len(predicted) >= len(body):
        if len(predicted) < 1 or len(predicted) > len(body):
            raise RuntimeError("Unable to predict number sequence for '{}'"
                               .format(self.filename))

        return predicted

    def _get_body(self):
        """Returns the existing head, midsection, and tail in a flat list."""
        body = [self.head]
        if self.mid is not None:  # Midsection exists
            if isinstance(self.mid, list):
                body.extend(self.mid)
            else:
                body.append(self.mid)
        if self.tail is not None:  # Tail exists
            body.append(self.tail)
        return body

    def _parse_filename_pattern(self, strict=True, verbose=False):
        """Parses the filename pattern of this image sequence. The sequence
            itself gets replaced by a digit format specifier.

        Args:
          strict (bool): By default True to catch image sequences with more
            than one number sequence and if caught raise an error, or False
            thus allowing easier debugging and more diverse filenames
          verbose (bool): True to output the parsing information,
            or by default False

        Raises:
          RuntimeError: Image sequence contains more than a single number
            sequence (<n> found)

        Returns:
          The parsed digit format specifier filename pattern [0] and the
            predicted sequence [1], which is equal to the sequence number
            of the initial image, but not necessarily the real sequence
            start number.
        """
        msg = "ANALYSING...\n"
        msg += "> Filename:\t\t{}\n".format(self.filename)

        body = self._get_body()
        bsi = self._predict_sequence(body)  # body sequence indices

        parsed_root = self.root
        sequence = None
        offset = 0  # root sequence index offset
        for n, i in enumerate(bsi):
            sequence = str(body[i])
            parsed_seq = parse_digit_format_specifier(sequence)
            ri = len("".join(body[:i]))  # root sequence index
            if len(bsi) > 1:
                msg += "> Sequence {}:\t{} (at index {})\n" \
                    .format(n + 1, sequence, ri)
            else:
                msg += "> Sequence:\t\t{} (at index {})\n" \
                    .format(sequence, ri)
            ri -= offset
            parsed_root = parsed_root[:ri] + parsed_seq + \
                          parsed_root[ri + len(body[i]):]
            offset += len(sequence) - len(parsed_seq)

        if len(bsi) > 1 and strict:
            raise RuntimeError("Image sequence contains more than a single "
                               + "number sequence ({} found)".format(len(bsi)))

        msg += "> Pattern:\t\t{}".format(parsed_root + self.ext)
        if verbose:
            print(msg)
            if len(bsi) > 1:
                print("DONE! INVALID IMAGE FILENAME PATTERN WITH "
                      + "{} NUMBER SEQUENCES FOUND".format(len(bsi)))
            else:
                if not strict:
                    print("DONE! VALID IMAGE FILENAME PATTERN FOUND")
                else:
                    print("DONE!")

        return parsed_root + self.ext, int(sequence)

    def detect_gaps(self):
        """Returns a list of filenames that are missing from the
            image sequence, or None if the sequence is complete
            or if the sequence consists only of a single image."""
        if self.start_num < 0:  # single image
            return None
        missing_files = []
        for i in xrange(self.start_num, len(self.files)):
            fname = self.dfs_filename % i
            if fname not in self.files:
                missing_files.append(fname)
        return missing_files if len(missing_files) > 0 else None

    def starts_at_zero(self):
        """Returns True if the optionally zero-padded start number of
            the image sequence is equal to zero, otherwise False."""
        return self.start_num == 0

    def get_start_number(self):
        """Gets the start number of the image sequence. If the sequence does
            not start at zero, a smaller start number is searched for."""
        other_num = -1
        if not self.starts_at_zero():
            for i in xrange(self.start_num - 1, -1, -1):
                fname = self.dfs_filename % i
                fpath = os.path.join(self.basedir, fname)
                if is_file(fpath)[0]:
                    other_num = i
        return self.start_num if other_num < 0 else other_num

    def get_dfs_filename(self):
        """Returns the digit format specifier filename of the image sequence."""
        return self.dfs_filename

    def get_regex_filename(self):
        """Returns the regular expression filename from the digit format
            specifier one of the image sequence. If the image sequence
            is a pseudo-sequence - consists of only a single image -,
            the filename of this image gets returned."""
        _, dfs = extract_digit_format_specifiers(self.dfs_filename)
        if dfs is None or self.start_num < 0:  # single image
            return self.dfs_filename
        elif isinstance(dfs, list):  # multiple dfs; currently unsupported
            raise ValueError("More than one digit format specifier found")
        group_pattern = "({})".format(to_re_pattern(dfs)) #
        re_filename = r"^" + self.dfs_filename.replace(dfs, group_pattern) + "$"
        if "%%" in re_filename:  # fix for filenames with escaped %-symbols
            re_filename = re_filename.replace("%%", "%")
        return re_filename

    def get_sequence_files(self, sort_files=True):
        """Searches for sequence files at directory path of the input image,
            whose names match the parsed digit format specifier filename.

            Optionally files can be sorted by their sequence numbers, which
            for numbered sequences is in some cases more reliable than using
            sort() or sorted() from the standard library.

        Args:
          sort_files (bool): By default True to sort the found files by
            their sequence number, otherwise False.

        Returns:
          A list of optionally sorted, matched filenames.
        """
        re_fname = self.get_regex_filename()
        files = []
        seq_nums = []  # sequence numbers

        for f in os.listdir(self.basedir):
            fpath = os.path.join(self.basedir, f)
            if not os.path.isfile(fpath):
                continue
            match = re.match(re_fname, f)
            if match is None:
                continue
            if sort_files:
                num = int(match.group(1))  # strip padding
                seq_nums.append(num)
            files.append(f)

        if sort_files and len(files) > 0:
            files = [f for _, f in sorted(zip(seq_nums, files))]

        return files
