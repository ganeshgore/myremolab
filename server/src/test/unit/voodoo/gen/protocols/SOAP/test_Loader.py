#!/usr/bin/env python
#-*-*- encoding: utf-8 -*-*-
#
# Copyright (C) 2005 onwards University of Deusto
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# This software consists of contributions made by many individuals,
# listed below:
#
# Author: Pablo Orduña <pablo@ordunya.com>
#

import unittest

class SOAPLoaderTestCase(unittest.TestCase):
    #TODO
    pass

def suite():
    return unittest.makeSuite(SOAPLoaderTestCase)

if __name__ == '__main__':
    unittest.main()

