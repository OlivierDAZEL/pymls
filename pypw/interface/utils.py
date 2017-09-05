#! /usr/bin/env python
# -*- coding:utf8 -*-
#
# utils.py
#
# This file is part of pypw, a software distributed under the MIT license.
# For any question, please contact one of the authors cited below.
#
# Copyright (c) 2017
# 	Olivier Dazel <olivier.dazel@univ-lemans.fr>
# 	Mathieu Gaborit <gaborit@kth.se>
# 	Peter Göransson <pege@kth.se>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#


from .interfaces import\
    fluid_elastic_interface,\
    elastic_fluid_interface,\
    fluid_pem_interface
from ..media import *


def generic_interface(medium_right, medium_left):
    """
    Returns a callable to the interface function corresponding to the
    two given media.

    Note: interface functions are not symmetrical ( generic_interface(m1, m2) !=
    generic_interface(m2, m1) ).
    """

    if medium_right.MODEL == 'fluid':
        if medium_left.MODEL == 'fluid':
            return None
        if medium_left.MODEL == 'elastic':
            return elastic_fluid_interface
        if medium_left.MODEL == 'pem':
            return fluid_pem_interface

    if medium_right.MODEL == 'elastic':
        if medium_left.MODEL == 'fluid':
            return fluid_elastic_interface
        if medium_left.MODEL == 'elastic':
            return None
        if medium_left.MODEL == 'pem':
            raise NotImplementedError

    if medium_right.MODEL == 'pem':
        raise NotImplementedError
