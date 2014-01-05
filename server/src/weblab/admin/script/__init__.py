#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 onwards University of Deusto
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

import sys

from weblab import __version__ as weblab_version

from weblab.admin.script.creation import weblab_create, Creation
assert Creation != None # Avoid pyflakes warning, wcloud still uses "from weblab.admin.script import Creation"
from weblab.admin.script.run import weblab_start, weblab_stop
from weblab.admin.script.monitor import weblab_monitor
from weblab.admin.script.admin import weblab_admin
from weblab.admin.script.upgrade import weblab_upgrade

# 
# TODO
#  - --virtual-machine
# 

SORTED_COMMANDS = []
SORTED_COMMANDS.append(('create',     'Create a new weblab instance')), 
SORTED_COMMANDS.append(('start',      'Start an existing weblab instance')), 
SORTED_COMMANDS.append(('stop',       'Stop an existing weblab instance')),
SORTED_COMMANDS.append(('admin',      'Adminstrate a weblab instance')),
SORTED_COMMANDS.append(('monitor',    'Monitor the current use of a weblab instance')),
SORTED_COMMANDS.append(('upgrade',    'Upgrade the current setting')), 

COMMANDS = dict(SORTED_COMMANDS)
HIDDEN_COMMANDS = ('-version', '--version', '-V')

def weblab():
    if len(sys.argv) == 2 and sys.argv[1] in HIDDEN_COMMANDS:
        if sys.argv[1] in ('--version', '-version', '-V'):
            print weblab_version
        else:
            print >> sys.stderr, "Command %s not implemented" % sys.argv[1]
        sys.exit(0)
    if len(sys.argv) in (1, 2) or sys.argv[1] not in COMMANDS:
        command_list = ""
        max_size = max((len(command) for command in COMMANDS))
        for command, help_text in SORTED_COMMANDS:
            filled_command = command + ' ' * (max_size - len(command))
            command_list += "\t%s\t%s\n" % (filled_command, help_text)
        print >> sys.stderr, "Usage: %s option DIR [option arguments]\n\n%s\n" % (sys.argv[0], command_list)
        sys.exit(0)
    main_command = sys.argv[1]
    if main_command == 'create':
        weblab_create(sys.argv[2])
        sys.exit(0)

    if main_command == 'start':
        weblab_start(sys.argv[2])
    elif main_command == 'stop':
        weblab_stop(sys.argv[2])
    elif main_command == 'monitor':
        weblab_monitor(sys.argv[2])
    elif main_command == 'admin':
        weblab_admin(sys.argv[2])
    elif main_command == 'upgrade':
        weblab_upgrade(sys.argv[2])
    elif main_command == '--version':
        print weblab_version
    else:
        print >>sys.stderr, "Command %s not yet implemented" % sys.argv[1]


