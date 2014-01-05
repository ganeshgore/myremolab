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
import weblab.experiment.devices.exc as DeviceErrors

class InvalidGpibProperty(DeviceErrors.MisconfiguredDeviceError):
    def __init__(self, *args, **kargs):
        DeviceErrors.MisconfiguredDeviceError.__init__(self, *args, **kargs)

class CantFindGpibProperty(DeviceErrors.MisconfiguredDeviceError):
    def __init__(self, *args, **kargs):
        DeviceErrors.MisconfiguredDeviceError.__init__(self, *args, **kargs)

class AlreadyProgrammingDeviceError(DeviceErrors.AlreadyProgrammingDeviceError):
    def __init__(self, *args, **kargs):
        DeviceErrors.AlreadyProgrammingDeviceError.__init__(self, *args, **kargs)

class ErrorProgrammingDeviceError(DeviceErrors.ProgrammingDeviceError):
    def __init__(self,*args,**kargs):
        DeviceErrors.ProgrammingDeviceError.__init__(self,*args,**kargs)

class ErrorRetrievingOutputFromProgrammingProgramError(DeviceErrors.ProgrammingDeviceError):
    def __init__(self,*args,**kargs):
        DeviceErrors.ProgrammingDeviceError.__init__(self,*args,**kargs)

class ErrorWaitingForProgrammingFinishedError(DeviceErrors.ProgrammingDeviceError):
    def __init__(self,*args,**kargs):
        DeviceErrors.ProgrammingDeviceError.__init__(self,*args,**kargs)

class ProgrammingGotErrors(DeviceErrors.ProgrammingDeviceError):
    def __init__(self,*args,**kargs):
        DeviceErrors.ProgrammingDeviceError.__init__(self,*args,**kargs)
