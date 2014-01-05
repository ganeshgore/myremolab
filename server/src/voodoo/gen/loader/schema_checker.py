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

import os
import sys
from StringIO import StringIO

try:
    from lxml import etree
except ImportError:
    LXML_AVAILABLE = False
    MESSAGE_SHOWN  = False
else:
    LXML_AVAILABLE = True

from weblab.util import data_filename
import voodoo.log as log
import voodoo.gen.exceptions.loader.LoaderErrors as LoaderErrors

module_directory = os.path.join(*__name__.split('.')[:-1])

class SchemaChecker(object):
    def check_schema(self, xmlfile_path, xsdfile_path):
        if not LXML_AVAILABLE:
            global MESSAGE_SHOWN
            if not MESSAGE_SHOWN:
                msg = "The optional library 'lxml' is not available. The syntax of the configuration files will not be checked."
                print >> sys.stderr, msg
                log.log( SchemaChecker, log.level.Warning, msg )
                MESSAGE_SHOWN = True
            return
        
        xmlfile_content = self._read_xml_file(xmlfile_path)
        xsdfile_full_path = data_filename(os.path.join(module_directory, 'xsd', xsdfile_path))
        try:
            xsdfile_content   = self._read_xsd_file(xsdfile_full_path)
        except:
            msg = "The XSD file %s could not be loaded. The syntax of the configuration files will not be checked." % xsdfile_full_path
            print >> sys.stderr, msg
            log.log( SchemaChecker, log.level.Warning, msg )
            return

        try:
            sio_xsd = StringIO(xsdfile_content)
            xmlschema_doc = etree.parse(sio_xsd)
            xmlschema = etree.XMLSchema(xmlschema_doc)
        except Exception as e:
            log.log( SchemaChecker, log.level.Warning, 'Invalid syntax file configuration: File %s: %s' % (xsdfile_path, e))
            log.log_exc( SchemaChecker, log.level.Info)
            raise LoaderErrors.InvalidSyntaxFileConfigurationError( e, xsdfile_path )

        try:
            sio_xml = StringIO(xmlfile_content)
            xml_doc = etree.parse(sio_xml)
            xmlschema.assertValid(xml_doc)
        except etree.DocumentInvalid as di:
            log.log( SchemaChecker, log.level.Warning, 'Not a valid configuration file. Check it with a XML Schema validator: File %s' % (xmlfile_path))
            raise LoaderErrors.InvalidSyntaxFileConfigurationError( 'Not a valid configuration file. Check it with a XML Schema validator. %s' % di.args, xmlfile_path)
        except Exception as e:
            log.log( SchemaChecker, log.level.Warning, 'Invalid syntax file configuration: File %s: %s' % (xmlfile_path, e))
            log.log_exc( SchemaChecker, log.level.Info)
            raise LoaderErrors.InvalidSyntaxFileConfigurationError( e, xmlfile_path)

    # For testing purposes
    def _read_xml_file(self, xmlfile_path):
        return open(xmlfile_path).read()
    def _read_xsd_file(self, xsdfile_path):
        return open(xsdfile_path).read()

