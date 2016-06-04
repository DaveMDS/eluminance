#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015-2016 Davide Andreoli <dave@gurumeditation.it>
#
# This file is part of Eluminance.
#
# Eluminance is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# Eluminance is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Eluminance. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function, unicode_literals

import os
import re
from efl.ecore import Exe


def xdg_open(url_or_file):
    Exe('xdg-open "%s"' % url_or_file)

def clamp(low, val, high):
    if val < low: return low
    if val > high: return high
    return val

def file_hum_size(file_path):
    bytes = float(os.path.getsize(file_path))
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.1fT' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.1fG' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.1fM' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.1fK' % kilobytes
    else:
        size = '%.1fb' % bytes
    return size

def natural_sort(l): 
   convert = lambda text: int(text) if text.isdigit() else text.lower() 
   alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
   return sorted(l, key=alphanum_key)


HOMEPAGE = 'https://github.com/davemds/eluminance'

AUTHORS = """
<br>
<align=center>

<hilight>Davide Andreoli (davemds)</hilight><br>
dave@gurumeditation.it<br><br>

<hilight>Wolfgang Morawetz (wfx)</hilight><br>
wolfgang.morawetz@gmail.com<br><br>

</align>
"""

INFO = """
<align=center>
<hilight>Eluminance</hilight> is a fast photo browser written in python.<br> 
</align>
"""

LICENSE = """
<align=center>
<hilight>
GNU GENERAL PUBLIC LICENSE<br>
Version 3, 29 June 2007<br><br>
</hilight>

This program is free software: you can redistribute it and/or modify 
it under the terms of the GNU General Public License as published by 
the Free Software Foundation, either version 3 of the License, or 
(at your option) any later version.<br><br>

This program is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
GNU General Public License for more details.<br><br>

You should have received a copy of the GNU General Public License 
along with this program. If not, see<br>
<link><a href=http://www.gnu.org/licenses>http://www.gnu.org/licenses/</a></link>
</align>
"""
