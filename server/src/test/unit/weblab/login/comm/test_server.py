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
#         Jaime Irurzun <jaime.irurzun@gmail.com>
#

import sys
import unittest
import mocker

import time

from test.util.ports import new as new_port

import weblab.configuration_doc as configuration_doc

import weblab.admin.bot.client as Client

import weblab.comm.server as RemoteFacadeServer
import weblab.login.comm.server as LoginFacadeServer

import voodoo.configuration as ConfigurationManager
import test.unit.configuration as configuration

import voodoo.sessions.session_id as SessionId
from test.util.module_disposer import uses_module

USERNAME         ='myusername'
PASSWORD         ='mypassword'
REAL_ID          ='this_is_the_real_id'


class WrappedRemoteFacadeServer(LoginFacadeServer.LoginRemoteFacadeServer):
    rfm_mock = None
    
    def _create_zsi_remote_facade_manager(self, *args, **kwargs):
        return self.rfm_mock
    
    def _create_json_remote_facade_manager(self, *args, **kwargs):
        return self.rfm_mock
    
    def _create_xmlrpc_remote_facade_manager(self, *args, **kwargs):
        return self.rfm_mock

ZSI_PORT    = new_port()
JSON_PORT   = new_port()
XMLRPC_PORT = new_port()

class LoginRemoteFacadeServerTestCase(mocker.MockerTestCase):

    def setUp(self):
        self.configurationManager = ConfigurationManager.ConfigurationManager()
        self.configurationManager.append_module(configuration)
        self.configurationManager._set_value(configuration_doc.FACADE_TIMEOUT, 0.01)

        time.sleep( 0.01 * 5 )

        self.configurationManager._set_value(LoginFacadeServer.LOGIN_FACADE_ZSI_PORT, ZSI_PORT)
        self.configurationManager._set_value(LoginFacadeServer.LOGIN_FACADE_ZSI_SERVICE_NAME, '/weblab/login/soap/')
        self.configurationManager._set_value(LoginFacadeServer.LOGIN_FACADE_ZSI_LISTEN, '')

        self.configurationManager._set_value(LoginFacadeServer.LOGIN_FACADE_JSON_PORT, JSON_PORT)
        self.configurationManager._set_value(LoginFacadeServer.LOGIN_FACADE_JSON_LISTEN, '')

        self.configurationManager._set_value(LoginFacadeServer.LOGIN_FACADE_XMLRPC_PORT, XMLRPC_PORT)
        self.configurationManager._set_value(LoginFacadeServer.LOGIN_FACADE_XMLRPC_LISTEN, '')

    if RemoteFacadeServer.ZSI_AVAILABLE:

        @uses_module(RemoteFacadeServer)
        def test_simple_use_zsi(self):
            session_to_return = SessionId.SessionId(REAL_ID)
            rfm_obj = self.mocker.mock()
            rfm_obj.login(USERNAME, PASSWORD)
            self.mocker.result(session_to_return)
            WrappedRemoteFacadeServer.rfm_mock = rfm_obj
            self.rfs = WrappedRemoteFacadeServer(None, self.configurationManager)
        
            self.mocker.replay()
            self.rfs.start()
            try:
                zsi_client = Client.BotZSI("http://localhost:%s/weblab/soap/" % ZSI_PORT, "http://localhost:%s/weblab/login/soap/" % ZSI_PORT)
                session = zsi_client.do_login(USERNAME, PASSWORD)
                self.assertEquals(session.id, REAL_ID)
            finally:
                self.rfs.stop()
    else:
        
        print >> sys.stderr, "Optional library 'ZSI' not available. Skipping test int weblab.login.comm.RemoteFacadeServer"

    @uses_module(RemoteFacadeServer)
    def test_simple_use_json(self):
        session_to_return = {'id' : REAL_ID}
        rfm_json = self.mocker.mock()
        rfm_json.login( username = unicode(USERNAME), password = unicode(PASSWORD))
        self.mocker.result(session_to_return)
        WrappedRemoteFacadeServer.rfm_mock = rfm_json
        self.rfs = WrappedRemoteFacadeServer(None, self.configurationManager)
        
        self.mocker.replay()
        self.rfs.start()
        try:
            json_client = Client.BotJSON("http://localhost:%s/weblab/json/" % JSON_PORT, "http://localhost:%s/weblab/login/json/" % JSON_PORT)
            session = json_client.do_login(USERNAME, PASSWORD)
            self.assertEquals(session.id, REAL_ID)
        finally:
            self.rfs.stop()

    @uses_module(RemoteFacadeServer)
    def test_simple_use_xmlrpc(self):
        session_to_return = {'id' : REAL_ID}
        rfm_xmlrpc = self.mocker.mock()
        rfm_xmlrpc._dispatch('login', (USERNAME, PASSWORD))
        self.mocker.result(session_to_return)
        WrappedRemoteFacadeServer.rfm_mock = rfm_xmlrpc
        self.rfs = WrappedRemoteFacadeServer(None, self.configurationManager)
        
        self.mocker.replay()
        self.rfs.start()
        try:
            xmlrpc_client = Client.BotXMLRPC("http://localhost:%s/weblab/xmlrpc/" % XMLRPC_PORT, "http://localhost:%s/weblab/login/xmlrpc/" % XMLRPC_PORT)
            session = xmlrpc_client.do_login(USERNAME, PASSWORD)
            self.assertEquals(session.id, REAL_ID)
        finally:
            self.rfs.stop()


def suite():
    return unittest.makeSuite(LoginRemoteFacadeServerTestCase)

if __name__ == '__main__':
    unittest.main()

