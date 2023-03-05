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


def get_string_literal(byte, next_byte):
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
    if byte >= 0x7F:
        return "\\%03o" % byte
    if byte in SPECIAL_ESCAPES:
        return SPECIAL_ESCAPES[byte]
    if byte < 0x20:
        if 0x30 <= next_byte <= 0x37:
            return "\\%03o" % byte
        else:
            return "\\%o" % byte
    return chr(byte)


class LineBuilder:
    def __init__(self, line_width=78, first_prefix="", prefix="",
                 suffix="", last_suffix="", separator="", output=None):
        self._line_width = line_width
        self._first_prefix = first_prefix
        self._prefix = first_prefix
        self._suffix = suffix
        self._last_suffix = last_suffix
        self._separator = separator
        self._output = output or (lambda s: sys.stdout.write(s + "\n"))
        self._next_prefix = prefix
        self._words = []

    def _get_width_of_candidates(self):
        if not self._words:
            return 0
        return (sum(len(s) for s in self._words)
                + (len(self._words) - 1) * len(self._separator))

    def _write_line(self):
        line = [self._prefix, self._words[0]]
        line_width = sum(len(s) for s in line) + len(self._suffix)
        for i in range(1, len(self._words)):
            width = len(self._separator) + len(self._words[i])
            if line_width + width < self._line_width:
                line.append(self._separator)
                line.append(self._words[i])
                line_width += width
            else:
                line.append(self._suffix)
                self._output("".join(line))
                self._prefix = self._next_prefix
                self._words = self._words[i:]
                break

    def add(self, s):
        if not s:
            return

        self._words.append(s)
        if len(self._words) == 1:
            return

        width = len(self._prefix) + self._get_width_of_candidates()
        if width + min(len(self._last_suffix), len(self._suffix)) > self._line_width:
            self._write_line()

    def end(self):
        while len(self._words) > 1:
            width = (len(self._prefix)
                     + self._get_width_of_candidates()
                     + len(self._last_suffix))

            if width < self._line_width:
                break

            last_word = self._words.pop()
            self._write_line()
            self._words.append(last_word)

        line = [self._prefix]
        if self._words:
            line.append(self._words[0])
            for word in self._words[1:]:
                line.append(self._separator)
                line.append(word)
        line.append(self._last_suffix)
        self._output("".join(line))
        self._prefix = self._first_prefix
        self._words = []


def get_path(file_name, paths):
    if os.path.exists(file_name):
        return file_name
    for path in paths:
        file_path = os.path.join(path, file_name)
        if os.path.exists(file_path):
            return file_path
    return None


def write_file_as_string(file_path, line_width, first_prefix, last_suffix):
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

    lb = LineBuilder(line_width=line_width,
                     first_prefix=first_prefix,
                     prefix=f"{prefix}\"",
                     suffix="\"",
                     last_suffix=last_suffix)
    data = open(file_path, "rb").read()
    if data:
        for i in range(len(data) - 1):
            lb.add(get_string_literal(data[i], data[i + 1]))
        lb.add(get_string_literal(data[-1], 0))
    lb.end()


def process_template(file, search_paths, line_width):
    rex = re.compile("""#embed *(<[^>]*>|"[^"]*")""")
    for line in file:
        match = rex.search(line)
        if match:
            file_path = get_path(match.group(1)[1:-1], search_paths)
            if not file_path:
                raise IOError(f"File not found: {file_path}")
            write_file_as_string(file_path, line_width, line[:match.start(0)],
                                 line[match.end(0):-1])
        else:
            sys.stdout.write(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stdin", action="store_const", const=True,
                    help="Read input from stdin")
    ap.add_argument("-w", "--width", metavar="COLS", default=78, type=int,
                    help="Set the line width. Default is 78.")
    ap.add_argument("-i", "--include", metavar="PATH", action="append",
                    help="Add a include path.")
    ap.add_argument("file", metavar="FILE", nargs="?",
                    help="A file that will be encoded as a C char array")
    args = ap.parse_args()
    if (not args.file) == (not args.stdin):
        ap.error("Must either specify FILE or --stdin")

    include_dirs = args.include or []
    input_file = sys.stdin
    if args.file:
        input_file = open(args.file)
        include_dirs.insert(0, os.path.realpath(os.path.dirname(args.file)))

    include_dirs.append(os.path.curdir)

    try:
        process_template(input_file, include_dirs, args.width)
    except IOError as ex:
        print(ex)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())