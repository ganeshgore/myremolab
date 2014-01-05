#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 onwards University of Deusto
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

from weblab.login.simple import SimpleAuthnUserAuth

#######################################################################
# 
#        Trusted Ip addresses
# 

from weblab.comm.context import get_context

class TrustedIpAddressesUserAuth(SimpleAuthnUserAuth):

    NAME = 'TRUSTED-IP-ADDRESSES'

    def __init__(self, auth_configuration, user_auth_configuration):
        self.addresses = []
        if auth_configuration:
            self.addresses += [ ip.strip() for ip in auth_configuration.split(',') ]
        if user_auth_configuration:
            self.addresses += [ ip.strip() for ip in user_auth_configuration.split(',') ]

    def authenticate(self, login, password):
        return get_context().ip_address in self.addresses

    def __repr__(self):
        return "TrustedIpAddressesUserAuth(configuration=%r)" % self.addresses

