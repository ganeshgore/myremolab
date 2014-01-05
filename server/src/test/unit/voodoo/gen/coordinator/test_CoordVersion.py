#!/usr/bin/python
# -*- coding: utf-8 -*-
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

import voodoo.gen.coordinator.CoordVersion as CoordVersion
import voodoo.gen.coordinator.CoordAddress as CoordAddress
import voodoo.gen.exceptions.coordinator.CoordVersionErrors as CoordVersionErrors

class VersionTestCase(unittest.TestCase):
    def test_version_change(self):
        address = CoordAddress.CoordAddress('machine_id')
        self.assertRaises(
                CoordVersionErrors.CoordVersionNotAnActionError,
                CoordVersion.CoordVersionChange,
                address,
                'NEW2'
            )
        self.assertRaises(
                CoordVersionErrors.CoordVersionNotAnAddressError,
                CoordVersion.CoordVersionChange,
                'machine_id',
                CoordVersion.ChangeActions.NEW
            )

def suite():
    return unittest.makeSuite(VersionTestCase)

if __name__ == '__main__':
    unittest.main()

