#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# ===========================================================================
# Copyright © 2023 Jan Erik Breimo. All rights reserved.
# Created by Jan Erik Breimo on 2023-03-05.
#
# This file is distributed under the BSD License.
# License text is included with the source distribution.
# ===========================================================================
import argparse
import os
import re
import sys

SPECIAL_ESCAPES = {
    0x07: "\\a",
    0x08: "\\b",
    0x09: "\\t",
    0x0A: "\\n",
    0x0B: "\\v",
    0x0C: "\\f",
    0x0D: "\\r",
    0x22: '\\"',
    0x5C: "\\\\"
}

TRIGRAPH_PREFIX = [ord("?"), ord("?")]
TRIGRAPH_SUFFIXES = set(b"=/'()!<>-")


def get_char_literal(byte, preceded_by_octal: bool) -> str:
    if byte >= 0x7F:
        return "\\%03o" % byte
    if byte in SPECIAL_ESCAPES:
        return SPECIAL_ESCAPES[byte]
    if byte < 0x20:
        return "\\%o" % byte
    if preceded_by_octal and 0x30 <= byte <= 0x39:
        return "\\%o" % byte
    return chr(byte)


def is_escaped_octal(string):
    """
    Returns True if the string ends with an octal escape sequence.
    """
    if not string or string[0] != "\\":
        return False
    return all(c.isdigit() for c in string[1:])


class LineStuffer:
    """
    Builds lines of text from the strings added with the `add` method.
    The resulting lines will be as long as possible within the limit set by
    the `line_width` argument.
    """
    def __init__(self, line_width=78, first_prefix="", prefix="",
                 suffix="\n", last_suffix="\n", separator="", output_func=None):
        self._line_width = line_width
        self._first_prefix = first_prefix
        self._prefix = first_prefix
        self._suffix = suffix
        self._last_suffix = last_suffix
        self._separator = separator
        self._output_func = output_func or sys.stdout.write

        self._next_prefix = prefix
        self.words = []
        self._min_suffix_len = min(len(self._last_suffix.rstrip("\n")),
                                   len(self._suffix.rstrip("\n")))

    def _get_width_of_candidates(self):
        if not self.words:
            return 0
        return (sum(len(s) for s in self.words)
                + (len(self.words) - 1) * len(self._separator))

    def _write_line(self, force=False):
        line = [self._prefix, self.words[0]]
        line_width = sum(len(s) for s in line) + len(self._suffix.rstrip("\n"))

        complete_line = False
        for i in range(1, len(self.words)):
            width = len(self._separator) + len(self.words[i])
            if line_width + width < self._line_width and not force :
                line.append(self._separator)
                line.append(self.words[i])
                line_width += width
            else:
                complete_line = True
                break
        if complete_line or force:
            line.append(self._suffix)
            self._output_func("".join(line))
            self._prefix = self._next_prefix
            self.words = []

    def add(self, s) -> bool:
        if not s:
            return False

        self.words.append(s)
        if len(self.words) == 1:
            return False

        width = len(self._prefix) + self._get_width_of_candidates()
        if width + self._min_suffix_len > self._line_width:
            self._write_line()
            return True

        return False

    def end(self):
        while len(self.words) > 1:
            width = (len(self._prefix)
                     + self._get_width_of_candidates()
                     + len(self._last_suffix))

            if width < self._line_width:
                break

            last_word = self.words.pop()
            self._write_line(True)
            self.words.append(last_word)

        line = [self._prefix]
        if self.words:
            line.append(self.words[0])
            for word in self.words[1:]:
                line.append(self._separator)
                line.append(word)
        line.append(self._last_suffix)
        self._output_func("".join(line))
        self._prefix = self._first_prefix
        self.words = []


def unescape_digits(words: list[str]) -> bool:
    for i in range(len(words)):
        if "\\60" <= words[i] <= "\\71":
            words[i] = chr(int(words[i][1:], 8))
        else:
            return False
    return True


class Encoder:
    def __init__(self):
        self._prefix = [0, 0]
        self._i = 0
        self.preceded_by_octal = False

    def encode(self, byte):
        if byte in TRIGRAPH_SUFFIXES and self._prefix == TRIGRAPH_PREFIX:
            ch = "\\%o" % byte
        else:
            ch = get_char_literal(byte, self.preceded_by_octal)
        self._prefix[self._i % 2] = byte
        self._i += 1
        self.preceded_by_octal = is_escaped_octal(ch)
        return ch


def get_path(file_name, paths):
    if os.path.exists(file_name):
        return file_name
    for path in paths:
        file_path = os.path.join(path, file_name)
        if os.path.exists(file_path):
            return file_path
    return None


def write_file_as_string(file_path, line_width, first_prefix, last_suffix,
                         output_func, fix_newlines=False):
    if not first_prefix or first_prefix[-1] != '"':
        first_prefix += '"'
    if not last_suffix or last_suffix[0] != '"':
        last_suffix = '"' + last_suffix

    for i in range(len(first_prefix)):
        if not first_prefix[i].isspace():
            prefix = first_prefix[:i] * 2
            break
    else:
        prefix = "    "

    ls = LineStuffer(line_width=line_width,
                     first_prefix=first_prefix,
                     prefix=f"{prefix}\"",
                     suffix="\"\n",
                     last_suffix=last_suffix,
                     output_func=output_func)
    encoder = Encoder()
    data = open(file_path, "rb").read()
    if fix_newlines:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    for byte in data:
        if ls.add(encoder.encode(byte)) and unescape_digits(ls.words):
            encoder.preceded_by_octal = False
    ls.end()


REGEX = re.compile("""#embed(_text)? *(<[^>]*>|"[^"]*")""")


def process_template(file, search_paths, line_width, output_func):
    for line in file:
        match = REGEX.search(line)
        if match:
            file_path = get_path(match.group(2)[1:-1], search_paths)
            if not file_path:
                raise IOError(f"File not found: {match.group(2)[1:-1]}")
            write_file_as_string(file_path, line_width, line[:match.start(0)],
                                 line[match.end(0):], output_func,
                                 match.group(1) == "_text")
        else:
            output_func(line)


def list_files(file, search_paths, line_width, output_func):
    for line in file:
        match = REGEX.search(line)
        if match:
            if file_path := get_path(match.group(2)[1:-1], search_paths):
                output_func(file_path + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stdin", action="store_const", const=True,
                    help="Read input from stdin instead of [FILE].")
    ap.add_argument("-w", "--width", metavar="COLS", default=78, type=int,
                    help="Set the line width. Default is 78.")
    ap.add_argument("-i", "--include", metavar="PATH", action="append",
                    help="Add PATH to the list of paths where the program looks"
                         " for embedded files.")
    ap.add_argument("-o", "--output", metavar="PATH",
                    help="Set the name of the output file. Default is stdout.")
    ap.add_argument("--list-files", action="store_const", const=True,
                    help="List the files that would be embedded, but do not"
                         " output the actual C/C++ code.")
    ap.add_argument("file", metavar="FILE", nargs="?",
                    help="A C or C++ file with #embed directives.")
    args = ap.parse_args()
    if (not args.file) == (not args.stdin):
        ap.error("Must either specify FILE or --stdin")

    include_dirs = args.include or []
    input_file = sys.stdin
    if args.file:
        input_file = open(args.file)
        include_dirs.insert(0, os.path.realpath(os.path.dirname(args.file)))

    include_dirs.append(os.path.curdir)

    if args.output:
        dir_name = os.path.dirname(args.output)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        output_file = open(args.output, "w")
    else:
        output_file = sys.stdout

    try:
        if args.list_files:
            list_files(input_file, include_dirs, args.width,
                       output_file.write)
        else:
            process_template(input_file, include_dirs, args.width,
                             output_file.write)
    except IOError as ex:
        print(ex)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
