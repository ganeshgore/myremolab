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
#         Luis Rodriguez <luis.rodriguez@opendeusto.es>
#

import weblab.comm.web_server as WebFacadeServer

class LanguageMethod(WebFacadeServer.Method):
    path = '/language/'

    def avoid_weblab_cookies(self):
        return True

    def run(self):
        accept_language = self.req.headers.get('Accept-Language')
        if accept_language is None:
            return 'var acceptLanguageHeader = null;'
        else:
            return 'var acceptLanguageHeader = "%s";' % accept_language


