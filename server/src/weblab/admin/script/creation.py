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

try:
    from PIL import Image
except ImportError:
    PIL_AVAILABLE = False
else:
    PIL_AVAILABLE = True

import os
import getpass
import sys
import stat
import uuid
import traceback
import sqlite3
import urlparse
import json
from optparse import OptionParser, OptionGroup

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import sqlalchemy

from weblab.util import data_filename

import weblab.db.model as Model
from weblab.db.upgrade import DbRegularUpgrader, DbSchedulingUpgrader

import weblab.admin.deploy as deploy

import voodoo.sessions.db_lock_data as DbLockData
import voodoo.sessions.sqlalchemy_data as SessionSqlalchemyData

from voodoo.dbutil import generate_getconn


#########################################################################################
# 
# 
# 
#      W E B L A B     D I R E C T O R Y     C R E A T I O N
# 
# 
# 

class OptionWrapper(object):
    """ OptionWrapper is a wrapper of an OptionParser options object, 
    which makes it possible to refer to options['force'] instead of options.force.
    """
    def __init__(self, options):
        self._options = options

    def __contains__(self, name):
        return hasattr(self._options, name)

    def __getitem__(self, name):
        return getattr(self._options, name)

    def __setitem__(self, name, value):
        return setattr(self._options, name, value)

    def __getattribute__(self, name):
        if name == '_options':
            return object.__getattribute__(self, '_options')
        return getattr(self._options, name)

    def __repr__(self):
        return repr(self._options)

class Creation(object):

    """ This class wraps the options for creating a new WebLab-Deusto directory """
    
    FORCE             = 'force'
    VERBOSE           = 'verbose'

    # General information

    ADD_TEST_DATA     = 'add_test_data'
    CORES             = 'cores'
    START_PORTS       = 'start_ports'
    SYSTEM_IDENTIFIER = 'system_identifier'
    ENABLE_HTTPS      = 'enable_https'
    BASE_URL          = 'base_url'
    ENTITY_LINK       = 'entity_link'
    SERVER_HOST       = 'server_host'
    POLL_TIME         = 'poll_time'
    INLINE_LAB_SERV   = 'inline_lab_serv'
    HTTP_SERVER_PORT  = 'http_server_port'
    LAB_COPIES        = 'lab_copies'
    ADMIN_USER        = 'admin_user'
    ADMIN_NAME        = 'admin_name'
    ADMIN_PASSWORD    = 'admin_password'
    ADMIN_MAIL        = 'admin_mail'
    LOGO_PATH         = 'logo_path'

    # XMLRPC experiment
    XMLRPC_EXPERIMENT      = 'xmlrpc_experiment'
    XMLRPC_EXPERIMENT_PORT = 'xmlrpc_experiment_port'

    # Dummy experiment
    DUMMY_NAME          = 'dummy_name'
    DUMMY_CATEGORY_NAME = 'dummy_category_name'
    DUMMY_COPIES        = 'dummy_copies'

    # Visir
    VISIR_SERVER             = 'visir_server'
    VISIR_SLOTS              = 'visir_slots'
    VISIR_EXPERIMENT_NAME    = 'visir_experiment_name'
    VISIR_BASE_URL           = 'visir_base_url'
    VISIR_MEASUREMENT_SERVER = 'visir_measurement_server'
    VISIR_USE_PHP            = 'visir_use_php'
    VISIR_LOGIN              = 'visir_login'
    VISIR_PASSWORD           = 'visir_password'

    # Logic experiment
    LOGIC_SERVER       = 'logic_server'
    
    # Virtual Machine experiment
    VM_SERVER                       = 'vm_server'
    VM_EXPERIMENT_NAME              = 'vm_experiment_name'
    VM_STORAGE_DIR                  = 'vm_storage_dir'
    VBOX_VM_NAME                    = 'vbox_vm_name'
    VBOX_BASE_SNAPSHOT              = 'vbox_base_snapshot'
    VM_URL                          = 'vm_url'
    HTTP_QUERY_USER_MANAGER_URL     = 'http_query_user_manager_url'
    VM_ESTIMATED_LOAD_TIME          = 'vm_estimated_load_time'
    
    # Federated laboratories
    ADD_FEDERATED_LOGIC     = 'federated_logic'
    ADD_FEDERATED_ROBOT     = 'federated_robot'
    ADD_FEDERATED_VISIR     = 'federated_visir'
    ADD_FEDERATED_SUBMARINE = 'federated_submarine'
    
    # Sessions
    SESSION_STORAGE    = 'session_storage'
    SESSION_DB_ENGINE  = 'session_db_engine'
    SESSION_DB_HOST    = 'session_db_host'
    SESSION_DB_PORT    = 'session_db_port'
    SESSION_DB_NAME    = 'session_db_name'
    SESSION_DB_USER    = 'session_db_user'
    SESSION_DB_PASSWD  = 'session_db_passwd'
    SESSION_REDIS_DB   = 'session_redis_db'
    SESSION_REDIS_HOST = 'session_redis_host'
    SESSION_REDIS_PORT = 'session_redis_port'

    # Database
    DB_ENGINE          = 'db_engine'
    DB_NAME            = 'db_name'
    DB_HOST            = 'db_host'
    DB_PORT            = 'db_port'
    DB_USER            = 'db_user'
    DB_PASSWD          = 'db_passwd'
    
    # Coordination
    COORD_ENGINE       = 'coord_engine'
    COORD_DB_ENGINE    = 'coord_db_engine'
    COORD_DB_NAME      = 'coord_db_name'
    COORD_DB_USER      = 'coord_db_user'
    COORD_DB_PASSWD    = 'coord_db_passwd'
    COORD_DB_HOST      = 'coord_db_host'
    COORD_DB_PORT      = 'coord_db_port'
    COORD_REDIS_DB     = 'coord_redis_db'
    COORD_REDIS_PASSWD = 'coord_redis_passwd'
    COORD_REDIS_PORT   = 'coord_redis_port'

    # Other
    NOT_INTERACTIVE      = 'not_interactive'
    MYSQL_ADMIN_USER     = 'mysql_admin_username'
    MYSQL_ADMIN_PASSWORD = 'mysql_admin_password'

class CreationFlags(object):
    HTTP_SERVER_PORT = '--http-server-port'

COORDINATION_ENGINES = ['sql',   'redis'  ]
DATABASE_ENGINES     = ['mysql', 'sqlite' ]
SESSION_ENGINES      = ['sql',   'redis', 'memory']


def load_template(name, stdout = sys.stdout, stderr = sys.stderr):
    """ Reads the specified template file. Only the name needs to be specified. The file should be located
    in the config_templates folder. """
    path = "weblab" + os.sep + "admin" + os.sep + "config_templates" + os.sep + name
    try:
        f = file(path, "r")
        template = f.read()
        f.close()
    except:
        print >> stderr, "Error: Could not load template file %s. Probably couldn't be found." % path
    return template

def _test_redis(what, verbose, redis_port, redis_passwd, redis_db, redis_host, stdout, stderr, exit_func):
    if verbose: print >> stdout, "Checking redis connection for %s..." % what,; stdout.flush()
    kwargs = {}
    if redis_port   is not None: kwargs['port']     = redis_port
    if redis_passwd is not None: kwargs['password'] = redis_passwd
    if redis_db     is not None: kwargs['db']       = redis_db
    if redis_host   is not None: kwargs['host']     = redis_host
    try:
        import redis
    except ImportError:
        print >> stderr, "redis selected for %s; but redis module is not available. Try installing it with 'pip install redis'" % what
        exit_func(-1)
    else:
        try:
            client = redis.Redis(**kwargs)
            client.get("this.should.not.exist")
        except:
            print >> stderr, "redis selected for %s; but could not use the provided configuration" % what
            traceback.print_exc(file=stderr)
            exit_func(-1)
        else:
            if verbose: print >> stdout, "[done]"

def uncomment_json(lines):
    new_lines = []
    for line in lines:
        if '//' in line:
            if '"' in line or "'" in line:
                single_quote_open = False
                double_quote_open = False
                previous_slash    = False
                counter           = 0
                comment_found     = False
                for c in line:
                    if c == '/':
                        if previous_slash and not single_quote_open and not double_quote_open:
                            comment_found = True
                            break # counter is the previous one 
                        previous_slash = True
                    else:
                        previous_slash = False
                    if c == '"':
                        double_quote_open = not double_quote_open
                    if c == "'":
                        single_quote_open = not single_quote_open
                        
                    counter += 1

                if comment_found:
                    new_lines.append(line[:counter - 1] + '\n')
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line.split('//')[0])
        else:
            new_lines.append(line)
    return new_lines

DB_ROOT     = None
DB_PASSWORD = None

def _check_database_connection(what, metadata, upgrader_class, directory, verbose, db_engine, db_host, db_port, db_name, db_user, db_passwd, options, stdout, stderr, exit_func):
    if verbose: print >> stdout, "Checking database connection for %s..." % what,; stdout.flush()

    if db_engine == 'sqlite':
        base_location = os.path.join(os.path.abspath(directory), 'db', '%s.db' % db_name)
        if sys.platform.startswith('win'):
            sqlite_location     = base_location
            location = '/' + base_location
        else:
            sqlite_location = '/' + base_location
            location = '/' + base_location
        sqlite3.connect(database = sqlite_location).close()
    else:
        if db_port is not None:
            port_str = ':%s' % db_port
        else:
            port_str = ''

        if db_engine == 'mysql':
            try:
                import MySQLdb
                assert MySQLdb is not None # Avoid warnings
            except ImportError:
                try:
                    import pymysql_sa
                except ImportError:
                    pass
                else:
                    pymysql_sa.make_default_mysql_dialect()
                    
        location = "%(user)s:%(password)s@%(host)s%(port)s/%(name)s" % { 
                        'user'     : db_user, 
                        'password' : db_passwd, 
                        'host'     : db_host,
                        'name'     : db_name,
                        'port'     : port_str,
                    }
    
    db_str = "%(engine)s://%(location)s" % { 
                        'engine'   : db_engine,
                        'location' : location,
                    }

    getconn = generate_getconn(db_engine, db_user, db_passwd, db_host, db_port, db_name, dirname = directory)
    pool = sqlalchemy.pool.QueuePool(getconn)

    try:
        engine = create_engine(db_str, echo = False, pool = pool)
        engine.execute("select 1")
    except Exception as e:
        print >> stderr, "error: database used for %s is misconfigured" % what
        print >> stderr, "error: %s"  % str(e)
        if verbose:
            traceback.print_exc(file=stderr)
        else:
            print >> stderr, "error: Use -v to get more detailed information"

        try:
            create_database = deploy.generate_create_database(db_engine)
        except Exception as e:
            print >> stderr, "error: You must create the database and the db credentials"
            print >> stderr, "error: reason: there was an error trying to offer you the creation of users:", str(e)
            exit_func(-1)
        else:
            if create_database is None:
                print >> stderr, "error: You must create the database and the db credentials"
                print >> stderr, "error: reason: weblab does not support creating a database with engine %s" % db_engine
                exit_func(-1)
            else:
                if options[Creation.NOT_INTERACTIVE]:
                    should_create = True
                else:
                    should_create = raw_input('Would you like to create it now? (y/N) ').lower().startswith('y')
                    if not should_create:
                        print >> stderr, "not creating"
                        exit_func(-1)
                if db_engine == 'sqlite':
                    create_database(admin_username = None, admin_password = None, database_name = db_name, new_user = None, new_password = None, db_dir = os.path.join(directory, 'db'))
                elif db_engine == 'mysql':
                    if Creation.MYSQL_ADMIN_USER in options and Creation.MYSQL_ADMIN_PASSWORD in options:
                        admin_username = options[Creation.MYSQL_ADMIN_USER]
                        admin_password = options[Creation.MYSQL_ADMIN_PASSWORD]
                    else:
                        if options[Creation.NOT_INTERACTIVE]:
                            exit_func(-5)
                        global DB_ROOT, DB_PASSWORD
                        if DB_ROOT is None or DB_PASSWORD is None:
                            admin_username = raw_input("Enter the MySQL administrator username [default: root]: ") or 'root'
                            admin_password = getpass.getpass("Enter the MySQL administrator password: ")
                        else:
                            admin_username = DB_ROOT
                            admin_password = DB_PASSWORD
                    try:
                        create_database("Did you type your password incorrectly?", admin_username, admin_password, db_name, db_user, db_passwd, db_host, db_port)
                    except Exception as e:
                        print >> stderr, "error: could not create database. reason:", str(e)
                        exit_func(-1)
                    else:
                        DB_ROOT     = admin_username
                        DB_PASSWORD = admin_password
                else:
                    print >> stderr, "error: You must create the database and the db credentials"
                    print >> stderr, "error: reason: weblab does not support gathering information to create a database with engine %s" % db_engine
                    exit_func(-1)
                engine = create_engine(db_str, echo = False, pool = pool)



    if verbose: print >> stdout, "[done]"
    if verbose: print >> stdout, "Adding information to the %s database..." % what,; stdout.flush()
    metadata.drop_all(engine)
    metadata.create_all(engine)

    if upgrader_class is not None:
        if 'alembic_version' in metadata.tables:
            upgrader = upgrader_class(db_str)
            Session = sessionmaker(bind=engine)
            session = Session()
            session.execute(
                metadata.tables['alembic_version'].insert().values(version_num = upgrader.head)
            )
            session.commit()
            session.close()

    if verbose: print >> stdout, "[done]"
    return engine

def resize_image(image_path, max_width, max_height, final_path):
    img = Image.open(image_path)

    width, height = img.size
    
    # Example, (max_width = 200) / (width = 400) = 0.5 (height must be half)
    wpercent   = max_width / float(width)
    # 0.5 * 400 = 200 px is the new height
    new_height = wpercent * height
    
    # If 200 > 200
    if new_height > max_height:
        # Then invert height and width
        new_height = max_height
        new_width  = width  * (max_height / float(height))
    else:
        # Otherwise, the new_width is half what it was
        new_width  = max_width

    new_size = int(new_width), int(new_height)

    img = img.resize( new_size, Image.ANTIALIAS)
    img.save(final_path)


def _build_parser():
    parser = OptionParser(usage="%prog create DIR [options]")

    parser.add_option("-f", "--force",            dest = Creation.FORCE, action="store_true", default=False,
                                                   help = "Overwrite the contents even if the directory already existed.")

    parser.add_option("-v", "--verbose",          dest = Creation.VERBOSE, action="store_true", default=False,
                                                   help = "Show more information about the process.")

    parser.add_option("--add-test-data",          dest = Creation.ADD_TEST_DATA, action="store_true", default=False,
                                                  help = "Populate the database with sample data")

    parser.add_option("--cores",                  dest = Creation.CORES,           type="int",    default=1,
                                                  help = "Number of core servers.")

    parser.add_option("--start-port",             dest = Creation.START_PORTS,     type="int",    default=10000,
                                                  help = "From which port start counting.")

    parser.add_option("-i", "--system-identifier",dest = Creation.SYSTEM_IDENTIFIER, type="string", default="",
                                                  help = "A human readable identifier for this system.")

    parser.add_option("--enable-https",           dest = Creation.ENABLE_HTTPS,   action="store_true", default=False,
                                                  help = "Tell external federated servers that they must use https when connecting here")

    parser.add_option("--base-url",               dest = Creation.BASE_URL,       type="string",    default="",
                                                  help = "Base location, before /weblab/. Example: /deusto.")

    parser.add_option(CreationFlags.HTTP_SERVER_PORT,  dest = Creation.HTTP_SERVER_PORT,   type="int",    default=None,
                                                  help = "Enable the builtin HTTP server (so as to not require apache while testing) and listen in that port.")

    parser.add_option("--entity-link",            dest = Creation.ENTITY_LINK,       type="string",  default="http://www.yourentity.edu",
                                                  help = "Link of the host entity (e.g. http://www.deusto.es ).")

    parser.add_option("--logo-path",              dest = Creation.LOGO_PATH,       metavar="IMG_FILE_PATH", type="string",  default=None,
                                                  help = "Path of the entity logo.")

    parser.add_option("--server-host",            dest = Creation.SERVER_HOST,     type="string",    default="localhost",
                                                  help = "Host address of this machine. Example: weblab.domain.")

    parser.add_option("--poll-time",              dest = Creation.POLL_TIME,     type="int",    default=350,
                                                  help = "Time in seconds that will wait before expiring a user session.")

    parser.add_option("--inline-lab-server",      dest = Creation.INLINE_LAB_SERV, action="store_true", default=False,
                                                  help = "Laboratory server included in the same process as the core server. " 
                                                         "Only available if a single core is used." )

    parser.add_option("--lab-copies",             dest = Creation.LAB_COPIES, type="int",   default=1,
                                                  help = "Each experiment can be managed by a single laboratory server. "
                                                         "However, if the number of experiments managed by a single laboratory server "
                                                         "is high, it can become a bottleneck. This bottleneck effect can be reduced by "
                                                         "balancing the amount of experiments among different copies of the laboratories. "
                                                         "By establishing a higher number of laboratories, the generated deployment will "
                                                         "have the experiments balanced among them.")

    admin_data = OptionGroup(parser, "Administrator data",
                                                "Administrator basic data: username, password, etc.")
    admin_data.add_option("--admin-user",             dest = Creation.ADMIN_USER,       type="string",    default="admin",
                                                  help = "Username for the WebLab-Deusto administrator")
    admin_data.add_option("--admin-name",             dest = Creation.ADMIN_NAME,       type="string",    default="Administrator",
                                                  help = "Full name of the administrator")
    admin_data.add_option("--admin-password",       dest = Creation.ADMIN_PASSWORD, type="string",    default="password",
                                                  help = "Administrator password ('password' is the default)")
    admin_data.add_option("--admin-mail",             dest = Creation.ADMIN_MAIL,       type="string",    default="",
                                                  help = "E-mail address of the system administrator.")

    parser.add_option_group(admin_data)

    # TODO
    experiments = OptionGroup(parser, "Experiments options",
                                "While most laboratories are specific to a particular equipment, "
                                "some of them are useful anywhere (such as the VM experiment, as long as " 
                                "you have a VirtualBox virtual machine that you'd like to deploy, or the "
                                "logic game, which does not require any equipment). Other experiments, "
                                "such as VISIR, have been deployed in many universities. Finally, for "
                                "development purposes, the XML-RPC experiment is particularly useful.")

    experiments.add_option("--xmlrpc-experiment",      dest = Creation.XMLRPC_EXPERIMENT, action="store_true", default=False,
                                                       help = "By default, the Experiment Server is located in the same process as the  " 
                                                              "Laboratory server. However, it is possible to force that the laboratory  "
                                                              "uses XML-RPC to contact the Experiment Server. If you want to test a "
                                                              "Java, C++, .NET, etc. Experiment Server, you can enable this option, "
                                                              "and the system will try to find the Experiment Server in other port ")

    experiments.add_option("--xmlrpc-experiment-port", dest = Creation.XMLRPC_EXPERIMENT_PORT, type="int",    default=None,
                                                       help = "What port should the Experiment Server use. Useful for development.")

    experiments.add_option("--dummy-experiment-name",  dest = Creation.DUMMY_NAME, type="string",    default="dummy",
                                                       help = "There is a testing experiment called 'dummy'. You may change this name "
                                                              "(e.g. to dummy1 or whatever) by changing this option." )

    experiments.add_option("--dummy-category-name",    dest = Creation.DUMMY_CATEGORY_NAME, type="string",    default="Dummy experiments",
                                                       help = "You can change the category name of the dummy experiments. (by default,"
                                                              " Dummy experiments).")

    experiments.add_option("--dummy-copies",           dest = Creation.DUMMY_COPIES, type="int",    default=1,
                                                       help = "You may want to test the load balance among different copies of dummy." )

    experiments.add_option("--visir", "--visir-server", dest = Creation.VISIR_SERVER, action="store_true", default=False,
                                                       help = "Add a VISIR server to the deployed system. "  )

    experiments.add_option("--visir-slots",            dest = Creation.VISIR_SLOTS, default=60, type="int", metavar='SLOTS',
                                                       help = "Number of concurrent users of VISIR. "  )

    experiments.add_option("--visir-experiment-name",  dest = Creation.VISIR_EXPERIMENT_NAME, default='visir', type="string", metavar='EXPERIMENT_NAME',
                                                       help = "Name of the VISIR experiment. "  )

    experiments.add_option("--visir-base-url",         dest = Creation.VISIR_BASE_URL, default='', type="string", metavar='VISIR_BASE_URL',
                                                       help = "URL of the VISIR system (e.g. http://weblab-visir.deusto.es/electronics/ ). It should contain login.php, for instance. "  )

    experiments.add_option("--visir-measurement-server", dest = Creation.VISIR_MEASUREMENT_SERVER, default=None, type="string", metavar='MEASUREMENT_SERVER',
                                                       help = "Measurement server. E.g. weblab-visir.deusto.es:8080 "  )

    experiments.add_option("--visir-use-php",          dest = Creation.VISIR_USE_PHP, action="store_true", default=True,
                                                       help = "VISIR can manage the authentication through a PHP code. This option is slower, but required if that scheme is used."  )

    experiments.add_option("--visir-login",            dest = Creation.VISIR_LOGIN, default='guest', type="string", metavar='USERNAME',
                                                       help = "If the PHP version is used, define which username should be used. Default: guest."  )

    experiments.add_option("--visir-password",         dest = Creation.VISIR_PASSWORD, default='guest', type="string", metavar='PASSWORD',
                                                       help = "If the PHP version is used, define which password should be used. Default: guest."  )

    experiments.add_option("--logic", "--logic-server", dest = Creation.LOGIC_SERVER, action="store_true", default=False,
                                                       help = "Add a logic server to the deployed system. "  )

    # TODO
    experiments.add_option("--vm", "--virtual-machine", "--vm-server",  dest = Creation.VM_SERVER, action="store_true", default=False,
                                                       help = "Add a VM server to the deployed system. "  )
    
    experiments.add_option("--vm-experiment-name",  dest = Creation.VM_EXPERIMENT_NAME, default='vm', type="string", metavar='EXPERIMENT_NAME',
                                                       help = "Name of the VM experiment. "  )

    experiments.add_option("--vm-storage-dir",  dest = Creation.VM_STORAGE_DIR, default='C:\Users\lrg\.VirtualBox\Machines', type="string", metavar='STORAGE_DIR',
                                                   help = "Directory where the VirtualBox machines are located. For example: c:\users\lrg\.VirtualBox\Machines"  )

    experiments.add_option("--vbox-vm-name",  dest = Creation.VBOX_VM_NAME, default='UbuntuDefVM2', type="string", metavar='VBOX_VM_NAME',
                                                   help = "Name of the Virtual Box machine which this experiment uses. Is often different from the Hard Disk name."  )
    
    experiments.add_option("--vbox-base-snapshot",  dest = Creation.VBOX_BASE_SNAPSHOT, default='Ready', type="string", metavar='VBOX_BASE_SNAPSHOT',
                                                   help = "Name of the VirtualBox snapshot to which the system will be reset after every usage. It should be an snapshot of an started machine. Otherwise, it will take too long to start."  ) 

    experiments.add_option("--vm-url",  dest = Creation.VM_URL, default='vnc://192.168.51.82:5901', type="string", metavar='URL',
                                                   help = "URL which will be provided to users so that they can access the VM through VNC. For instance: vnc://192.168.51.82:5901"  )
    
    experiments.add_option("--http-query-user-manager-url",  dest = Creation.HTTP_QUERY_USER_MANAGER_URL, default='http://192.168.51.82:18080', type="string", metavar='URL',
                                                   help = "URL through which the user manager (which runs on the VM and resets it when needed) can be reached. For instance: http://192.168.51.82:18080"  )
    
    experiments.add_option("--vm-estimated-load-time",  dest = Creation.VM_ESTIMATED_LOAD_TIME, default='20', type="string", metavar='LOAD_TIME',
                                                   help = "Estimated time which is required for restarting the VM. Does not need to be accurate. It is displayed to the user and is essentially for cosmetic purposes. "  )
    
    

    parser.add_option_group(experiments)

    fed = OptionGroup(parser, "Federation options",
                                "WebLab-Deusto at the University of Deusto federates a set of laboratories. "
                                "You may put them by default in your WebLab-Deusto instance.")

    fed.add_option("--add-fed-submarine",       dest = Creation.ADD_FEDERATED_SUBMARINE, action="store_true", default=False,
                                                help = "Add the submarine laboratory.")

    fed.add_option("--add-fed-logic",           dest = Creation.ADD_FEDERATED_LOGIC, action="store_true", default=False,
                                                help = "Add the logic laboratory.")

    fed.add_option("--add-fed-visir",           dest = Creation.ADD_FEDERATED_VISIR, action="store_true", default=False,
                                                help = "Add the VISIR laboratory.")

    parser.add_option_group(fed)

    sess = OptionGroup(parser, "Session options",
                                "WebLab-Deusto may store sessions in a database, in memory or in redis."
                                "Choose one system and configure it." )

    sess.add_option("--session-storage",          dest = Creation.SESSION_STORAGE, choices = SESSION_ENGINES, default='memory',
                                                  help = "Session storage used. Values: %s." % (', '.join(SESSION_ENGINES)) )

    sess.add_option("--session-db-engine",        dest = Creation.SESSION_DB_ENGINE, type="string", default="sqlite",
                                                  help = "Select the engine of the sessions database.")

    sess.add_option("--session-db-host",          dest = Creation.SESSION_DB_HOST, type="string", default="localhost",
                                                  help = "Select the host of the session server, if any.")

    sess.add_option("--session-db-port",          dest = Creation.SESSION_DB_PORT, type="int", default=None,
                                                  help = "Select the port of the session server, if any.")

    sess.add_option("--session-db-name",          dest = Creation.SESSION_DB_NAME, type="string", default="WebLabSessions",
                                                  help = "Select the name of the sessions database.")

    sess.add_option("--session-db-user",          dest = Creation.SESSION_DB_USER, type="string", default="",
                                                  help = "Select the username to access the sessions database.")

    sess.add_option("--session-db-passwd",        dest = Creation.SESSION_DB_PASSWD, type="string", default="",
                                                  help = "Select the password to access the sessions database.")
                                                  
    sess.add_option("--session-redis-db",         dest = Creation.SESSION_REDIS_DB, type="int", default=1,
                                                  help = "Select the redis db on which store the sessions.")

    sess.add_option("--session-redis-host",       dest = Creation.SESSION_REDIS_HOST, type="string", default="localhost",
                                                  help = "Select the redis server host on which store the sessions.")

    sess.add_option("--session-redis-port",       dest = Creation.SESSION_REDIS_PORT, type="int", default=6379,
                                                  help = "Select the redis server port on which store the sessions.")

    parser.add_option_group(sess)

    dbopt = OptionGroup(parser, "Database options",
                                "WebLab-Deusto uses a relational database for storing users, permissions, etc."
                                "The database must be configured: which engine, database name, user and password." )

    dbopt.add_option("--db-engine",               dest = Creation.DB_ENGINE,       choices = DATABASE_ENGINES, default = 'sqlite',
                                                  help = "Core database engine to use. Values: %s." % (', '.join(DATABASE_ENGINES)))

    dbopt.add_option("--db-name",                 dest = Creation.DB_NAME,         type="string", default="WebLab",
                                                  help = "Core database name.")

    dbopt.add_option("--db-host",                 dest = Creation.DB_HOST,         type="string", default="localhost",
                                                  help = "Core database host.")

    dbopt.add_option("--db-port",                 dest = Creation.DB_PORT,         type="int", default=None,
                                                  help = "Core database port.")

    dbopt.add_option("--db-user",                 dest = Creation.DB_USER,         type="string", default="weblab",
                                                  help = "Core database username.")

    dbopt.add_option("--db-passwd",               dest = Creation.DB_PASSWD,       type="string", default="weblab",
                                                  help = "Core database password.")

    
    parser.add_option_group(dbopt)

    coord = OptionGroup(parser, "Scheduling options",
                                "These options are related to the scheduling system.  "
                                "You must select if you want to use a database or redis, and configure it.")

    coord.add_option("--coordination-engine",    dest = Creation.COORD_ENGINE,    choices = COORDINATION_ENGINES, default = 'sql',
                                                  help = "Coordination engine used. Values: %s." % (', '.join(COORDINATION_ENGINES)))

    coord.add_option("--coordination-db-engine", dest = Creation.COORD_DB_ENGINE, choices = DATABASE_ENGINES, default = 'sqlite',
                                                  help = "Coordination database engine used, if the coordination is based on a database. Values: %s." % (', '.join(DATABASE_ENGINES)))

    coord.add_option("--coordination-db-name",   dest = Creation.COORD_DB_NAME,   type="string", default="WebLabCoordination",

                                                  help = "Coordination database name used, if the coordination is based on a database.")

    coord.add_option("--coordination-db-user",   dest = Creation.COORD_DB_USER,   type="string", default="weblab",
                                                  help = "Coordination database userused, if the coordination is based on a database.")

    coord.add_option("--coordination-db-passwd", dest = Creation.COORD_DB_PASSWD,  type="string", default="weblab",
                                                  help = "Coordination database password used, if the coordination is based on a database.")

    coord.add_option("--coordination-db-host",    dest = Creation.COORD_DB_HOST,    type="string", default="localhost",
                                                  help = "Coordination database host used, if the coordination is based on a database.")

    coord.add_option("--coordination-db-port",    dest = Creation.COORD_DB_PORT,    type="int", default=None,
                                                  help = "Coordination database port used, if the coordination is based on a database.")

    coord.add_option("--coordination-redis-db",  dest = Creation.COORD_REDIS_DB,   type="int", default=None,
                                                  help = "Coordination redis DB used, if the coordination is based on redis.")

    coord.add_option("--coordination-redis-passwd",  dest = Creation.COORD_REDIS_PASSWD,   type="string", default=None,
                                                  help = "Coordination redis password used, if the coordination is based on redis.")

    coord.add_option("--coordination-redis-port",  dest = Creation.COORD_REDIS_PORT,   type="int", default=None,
                                                  help = "Coordination redis port used, if the coordination is based on redis.")

    parser.add_option_group(coord)

    return parser

class CreationResult(dict):
    """Object returned by the weblab_create method, providing information about what was done and in which files."""

    APACHE_FILE      = 'apache_file'
    IMG_FILE         = 'img_file'
    IMG_MOBILE_FILE  = 'img_mobile_file'
    START_PORT       = 'start_port'
    END_PORT         = 'end_port'

    COORD_REDIS_PORT = 'coord_redis_port'
    COORD_REDIS_DB   = 'coord_redis_db'


def weblab_create(directory, options_dict = None, stdout = sys.stdout, stderr = sys.stderr, exit_func = sys.exit):
    """Creates a new WebLab-Deusto instance in the directory "directory". If options_dict is None, it uses sys.argv to
    retrieve the arguments from the Command Line Interface. If it is provided, then it uses the default values unless
    a value is provided. The stdout, stderr and exit_func arguments are sys.stdout, sys.stderr and sys.exit by default, so
    they can be properly managed. More arguments can be passed, such as:

     - MYSQL_ADMIN_USERNAME 
     - MYSQL_ADMIN_PASSWORD 

    To avoid using the standard input to retrieve usernames and passwords.
    """
    creation_results = CreationResult()
    
    parser = _build_parser()

    if options_dict is None:
        parser_options, _ = parser.parse_args()
        options = OptionWrapper(parser_options)
        options[Creation.NOT_INTERACTIVE] = False
    else:
        options = parser.defaults.copy()
        options[Creation.NOT_INTERACTIVE] = True
        options.update(options_dict)

    verbose = options[Creation.VERBOSE]

    ###########################################
    # 
    # Validate basic options
    # 

    if verbose: print >> stdout, "Validating basic operations...",; stdout.flush()

    if options[Creation.COORD_ENGINE] == 'sql':
        coord_engine = 'sqlalchemy'
    else:
        coord_engine = options[Creation.COORD_ENGINE]

    if options[Creation.SESSION_STORAGE] == 'sql':
        session_storage = 'sqlalchemy'
    elif options[Creation.SESSION_STORAGE] == 'memory':
        session_storage = 'Memory'
    else:
        session_storage = options[Creation.SESSION_STORAGE]

    if options[Creation.CORES] > 1:
        if (coord_engine == 'sqlalchemy' and options[Creation.COORD_DB_ENGINE] == 'sqlite') or options[Creation.DB_ENGINE] == 'sqlite':
            sqlite_purpose = ''
            if coord_engine == 'sqlalchemy' and options[Creation.COORD_DB_ENGINE] == 'sqlite':
                sqlite_purpose = 'coordination'
            if options[Creation.DB_ENGINE] =='sqlite':
                if sqlite_purpose:
                    sqlite_purpose += ', '
                sqlite_purpose += 'general database'
                
            print >> stderr, "ERROR: sqlite engine selected for %s is incompatible with multiple cores" % sqlite_purpose
            exit_func(-1)

    if options[Creation.CORES] <= 0:
        print >> stderr, "ERROR: There must be at least one core server."
        exit_func(-1)

    base_url = options[Creation.BASE_URL]
    if base_url != '' and not base_url.startswith('/'):
        base_url = '/' + base_url
    if base_url.endswith('/'):
        base_url = base_url[:len(base_url) - 1]
    if options[Creation.ENABLE_HTTPS]:
        protocol = 'https://'
    else:
        protocol = 'http://'
    server_url = protocol + options[Creation.SERVER_HOST] + base_url + '/weblab/'

    if options[Creation.XMLRPC_EXPERIMENT] and options[Creation.DUMMY_COPIES] > 1:
        print >> stderr, "ERROR: there must be a single XML-RPC laboratory using the weblab-admin create at this point"
        exit_func(-1)

    if options[Creation.START_PORTS] < 1 or options[Creation.START_PORTS] >= 65535:
        print >> stderr, "ERROR: starting port number must be at least 1"
        exit_func(-1)

    if options[Creation.LOGO_PATH] is not None:
        original_logo_path = options[Creation.LOGO_PATH]
        if not os.path.exists(original_logo_path):
            print >> stderr, "ERROR: logo path does not exist"
            exit_func(-1)
    else:
        original_logo_path = data_filename(os.path.join('weblab','admin','generic-logo.jpg'))


    if options[Creation.INLINE_LAB_SERV] and options[Creation.CORES] > 1:
        print >> stderr, "ERROR: Inline lab server is incompatible with more than one core servers. It would require the lab server to be replicated in all the processes, which does not make sense."
        exit_func(-1)
        
    if verbose: print >> stdout, "[done]"

    if os.path.exists(directory) and not options[Creation.FORCE]:
        print >> stderr, "ERROR: Directory %s already exists. Use --force if you want to overwrite the contents." % directory
        exit_func(-1)

    if os.path.exists(directory):
        if not os.path.isdir(directory):
            print >> stderr, "ERROR: %s is not a directory. Delete it before proceeding." % directory
            exit_func(-1)
    else:
        try:
            os.mkdir(directory)
        except Exception as e:
            print >> stderr, "ERROR: Could not create directory %s: %s" % (directory, str(e))
            exit_func(-1)

    ###########################################
    # 
    # Validate database configurations
    # 

    if verbose: print >> stdout, "Start building database configuration"; stdout.flush()

    db_dir = os.path.join(directory, 'db')
    if not os.path.exists(db_dir):
        os.mkdir(db_dir)

    if options[Creation.COORD_ENGINE] == 'redis':
        redis_passwd = options[Creation.COORD_REDIS_PASSWD]
        redis_port   = options[Creation.COORD_REDIS_PORT]
        redis_db     = options[Creation.COORD_REDIS_DB]
        redis_host   = None
        _test_redis('coordination', verbose, redis_port, redis_passwd, redis_db, redis_host, stdout, stderr, exit_func)
        creation_results[CreationResult.COORD_REDIS_PORT] = redis_port
        creation_results[CreationResult.COORD_REDIS_DB]   = redis_db
    elif options[Creation.COORD_ENGINE] in ('sql', 'sqlalchemy'):
        db_engine  = options[Creation.COORD_DB_ENGINE]
        db_host    = options[Creation.COORD_DB_HOST]
        db_port    = options[Creation.COORD_DB_PORT]
        db_name    = options[Creation.COORD_DB_NAME]
        db_user    = options[Creation.COORD_DB_USER]
        db_passwd  = options[Creation.COORD_DB_PASSWD]
        import weblab.core.coordinator.sql.model as CoordinatorModel
        CoordinatorModel.load()
        _check_database_connection("coordination", CoordinatorModel.Base.metadata, DbSchedulingUpgrader, directory, verbose, db_engine, db_host, db_port, db_name, db_user, db_passwd, options, stdout, stderr, exit_func)
    else:
        print >> stderr, "The coordination engine %s is not registered" % options[Creation.COORD_ENGINE]
        exit_func(-1)
        

    if options[Creation.SESSION_STORAGE] == 'redis':
        redis_passwd = None
        redis_port   = options[Creation.SESSION_REDIS_PORT]
        redis_db     = options[Creation.SESSION_REDIS_DB]
        redis_host   = options[Creation.SESSION_REDIS_HOST]
        _test_redis('sessions', verbose, redis_port, redis_passwd, redis_db, redis_host, stdout, stderr, exit_func)
    elif options[Creation.SESSION_STORAGE] in ('sql', 'sqlalchemy'):
        db_engine = options[Creation.SESSION_DB_ENGINE]
        db_host   = options[Creation.SESSION_DB_HOST]
        db_host   = options[Creation.SESSION_DB_PORT]
        db_name   = options[Creation.SESSION_DB_NAME]
        db_user   = options[Creation.SESSION_DB_USER]
        db_passwd = options[Creation.SESSION_DB_PASSWD]
        _check_database_connection("sessions", SessionSqlalchemyData.SessionBase.metadata, None, directory, verbose, db_engine, db_host, db_port, db_name, db_user, db_passwd, options, stdout, stderr, exit_func)
        _check_database_connection("sessions locking", DbLockData.SessionLockBase.metadata, None, directory, verbose, db_engine, db_host, db_port, db_name, db_user, db_passwd, options, stdout, stderr, exit_func)
    elif options[Creation.SESSION_STORAGE] != 'memory':
        print >> stderr, "The session engine %s is not registered" % options[Creation.SESSION_STORAGE]
        exit_func(-1)

    db_engine = options[Creation.DB_ENGINE]
    db_name   = options[Creation.DB_NAME]
    db_host   = options[Creation.DB_HOST]
    db_port   = options[Creation.DB_PORT]
    db_user   = options[Creation.DB_USER]
    db_passwd = options[Creation.DB_PASSWD]
    engine = _check_database_connection("core database", Model.Base.metadata, DbRegularUpgrader, directory, verbose, db_engine, db_host, db_port, db_name, db_user, db_passwd, options, stdout, stderr, exit_func)
    
    if verbose: print >> stdout, "Adding required initial data...",; stdout.flush()
    deploy.insert_required_initial_data(engine)
    if verbose: print >> stdout, "[done]"
    if options[Creation.ADD_TEST_DATA]:
        if verbose: print >> stdout, "Adding test data...",; stdout.flush()
        deploy.populate_weblab_tests(engine, '1')
        if verbose: print >> stdout, "[done]"
    
    Session = sessionmaker(bind=engine)
    group_name = 'Administrators'
    deploy.add_group(Session, group_name)
    deploy.grant_admin_panel_on_group(Session, group_name)
    deploy.add_user(Session, options[Creation.ADMIN_USER], options[Creation.ADMIN_PASSWORD], options[Creation.ADMIN_NAME], options[Creation.ADMIN_MAIL])
    deploy.add_users_to_group(Session, group_name, options[Creation.ADMIN_USER])

    # dummy@Dummy experiments (local)
    deploy.add_experiment_and_grant_on_group(Session, options[Creation.DUMMY_CATEGORY_NAME], options[Creation.DUMMY_NAME], group_name, 200)

    # external-robot-movement@Robot experiments (federated)
    deploy.add_experiment_and_grant_on_group(Session, 'Robot experiments', 'external-robot-movement', group_name, 200)

    if options[Creation.ADD_FEDERATED_SUBMARINE]:
        deploy.add_experiment_and_grant_on_group(Session, 'Aquatic experiments', 'submarine', group_name, 200)

    # visir@Visir experiments (optional)
    if options[Creation.VISIR_SERVER] or options[Creation.ADD_FEDERATED_VISIR]:
        deploy.add_experiment_and_grant_on_group(Session, 'Visir experiments', options[Creation.VISIR_EXPERIMENT_NAME], group_name, 1800)

    # vm@VM experiments (optional)
    if options[Creation.VM_SERVER]:
        deploy.add_experiment_and_grant_on_group(Session, 'VM experiments', options[Creation.VM_EXPERIMENT_NAME], group_name, 200)

    # logic@PIC experiments (optional)
    if options[Creation.LOGIC_SERVER] or options[Creation.ADD_FEDERATED_LOGIC]:
        deploy.add_experiment_and_grant_on_group(Session, 'PIC experiments', 'ud-logic', group_name, 1800)

    ###########################################
    # 
    # Create voodoo infrastructure
    # 

    if verbose: print >> stdout, "Creating configuration files and directories...",; stdout.flush()

    machine_config = ("""<?xml version="1.0" encoding="UTF-8"?>""" 
    """<machines
        xmlns="http://www.weblab.deusto.es/configuration" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="global_configuration.xsd"
    >

    <machine>core_machine</machine>""")

    if options[Creation.XMLRPC_EXPERIMENT]:
        machine_config += """    <machine>exp_machine</machine>\n""" 

    machine_config += "\n\n</machines>\n"

    open(os.path.join(directory, 'configuration.xml'), 'w').write(machine_config)

    if options[Creation.XMLRPC_EXPERIMENT]:
        exp_machine_dir = os.path.join(directory, 'exp_machine')
        if not os.path.exists(exp_machine_dir):
            os.mkdir(exp_machine_dir)

        exp_machine_configuration_xml = ("""<?xml version="1.0" encoding="UTF-8"?>"""
        """<instances
            xmlns="http://www.weblab.deusto.es/configuration" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="machine_configuration.xsd"
        >

        <runner file="run-xmlrpc.py"/>

        <instance>exp_instance</instance>\n
        </instances>""")

        open(os.path.join(exp_machine_dir, 'configuration.xml'), 'w').write(exp_machine_configuration_xml)

        exp_instance_dir = os.path.join(exp_machine_dir, 'exp_instance')
        if not os.path.exists(exp_instance_dir):
            os.mkdir(exp_instance_dir)

        exp_instance_configuration_xml = ("""<?xml version="1.0" encoding="UTF-8"?>\n"""
		"""<servers \n"""
		"""    xmlns="http://www.weblab.deusto.es/configuration" \n"""
		"""    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n"""
		"""    xsi:schemaLocation="instance_configuration.xsd"\n"""
		""">\n"""
		"""    <user>weblab</user>\n"""
		"""\n"""
		"""    <server>experiment1</server>\n"""
		"""</servers>\n""")

        open(os.path.join(exp_instance_dir, 'configuration.xml'), 'w').write(exp_instance_configuration_xml)

        xmlrpc_server_dir = os.path.join(exp_instance_dir, 'experiment1')

    
    machine_dir = os.path.join(directory, 'core_machine')
    if not os.path.exists(machine_dir):
        os.mkdir(machine_dir)

    machine_configuration_xml = ("""<?xml version="1.0" encoding="UTF-8"?>"""
    """<instances
        xmlns="http://www.weblab.deusto.es/configuration" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="machine_configuration.xsd"
    >

    <runner file="run.py"/>

    <configuration file="machine_config.py"/>

    """)
    for core_n in range(1, options[Creation.CORES] + 1):
        machine_configuration_xml += "<instance>core_server%s</instance>\n    " % core_n

    machine_configuration_xml += "\n"
    if not options[Creation.INLINE_LAB_SERV]:
        for n in range(1, options[Creation.LAB_COPIES] + 1):
            machine_configuration_xml += "    <instance>laboratory%s</instance>\n\n" % n
    machine_configuration_xml += "</instances>\n"

    local_scheduling  = ""

    experiment_counter = 0
    laboratory_experiments  = {}
    laboratory_experiment_instances  = {}

    for n in range(options[Creation.LAB_COPIES]):
        laboratory_experiments[n] = ""
        laboratory_experiment_instances[n] = {}

    for n in xrange(1, options[Creation.DUMMY_COPIES] + 1):
        local_experiments = "            'exp%(n)s|%(dummy)s|%(dummy_category)s'        : 'dummy%(n)s@dummy',\n" % { 'dummy' : options[Creation.DUMMY_NAME], 'dummy_category' : options[Creation.DUMMY_CATEGORY_NAME], 'n' : n }
        lab_id = experiment_counter % options[Creation.LAB_COPIES]
        laboratory_experiments[lab_id] += local_experiments
        if 'dummy' not in laboratory_experiment_instances[lab_id]:
            laboratory_experiment_instances[lab_id]['dummy'] = []
        laboratory_experiment_instances[lab_id]['dummy'].append(n)
        experiment_counter += 1
    local_scheduling  += "        'dummy'            : ('PRIORITY_QUEUE', {}),\n"

    if options[Creation.VISIR_SERVER]:
        for n in xrange(1, options[Creation.VISIR_SLOTS] + 1):
            local_experiments = "            'exp%(n)s|%(name)s|Visir experiments'        : 'visir%(n)s@visir',\n" % { 'n' : n, 'name' : options[Creation.VISIR_EXPERIMENT_NAME] }
            lab_id = experiment_counter % options[Creation.LAB_COPIES]
            laboratory_experiments[lab_id] += local_experiments
            if 'visir' not in laboratory_experiment_instances[lab_id]:
                laboratory_experiment_instances[lab_id]['visir'] = []
            laboratory_experiment_instances[lab_id]['visir'].append(n)
            experiment_counter += 1
        local_scheduling  += "        'visir'            : ('PRIORITY_QUEUE', {}),\n"

    if options[Creation.LOGIC_SERVER]:
        local_experiments = "            'exp1|ud-logic|PIC experiments'        : 'logic@logic',\n"
        lab_id = experiment_counter % options[Creation.LAB_COPIES]
        laboratory_experiments[lab_id] += local_experiments
        laboratory_experiment_instances[lab_id]['logic'] = 1
        experiment_counter += 1
        local_scheduling  += "        'logic'            : ('PRIORITY_QUEUE', {}),\n"
        
    if options[Creation.VM_SERVER]:
        local_experiments = "            'exp1|%(name)s|VM experiments'        : 'vm@vm',\n" % { 'name' : options[Creation.VM_EXPERIMENT_NAME] }
        lab_id = experiment_counter % options[Creation.LAB_COPIES]
        laboratory_experiments[lab_id] += local_experiments
        laboratory_experiment_instances[lab_id]['vm'] = 1
        experiment_counter += 1
        local_scheduling  += "        'vm'            : ('PRIORITY_QUEUE', {}),\n"

    laboratory_servers = ""

    for n in range(1, options[Creation.LAB_COPIES] + 1):
        local_experiments = laboratory_experiments[n - 1]
        laboratory_servers += (
        "    'laboratory%(n)s:%(laboratory_instance_name)s@core_machine' : {\n"
        "%(local_experiments)s"
        "        },\n" % {
                'laboratory_instance_name' : 'core_server1' if options[Creation.INLINE_LAB_SERV] else 'laboratory%s' % n, 
                'local_experiments' : local_experiments, 'n' : n })

    other_core_coordinator_external_servers = ""
    other_scheduling_systems = ""
    if options[Creation.ADD_FEDERATED_LOGIC]:
        other_core_coordinator_external_servers += "    'ud-logic@PIC experiments'          : [ 'logic_external' ],\n"
        other_scheduling_systems                += "        'logic_external'   : weblabdeusto_federation_demo,\n"
    if options[Creation.ADD_FEDERATED_VISIR]:
        other_core_coordinator_external_servers += "    '%s@Visir experiments'           : [ 'visir_external' ],\n" % options[Creation.VISIR_EXPERIMENT_NAME]
        other_scheduling_systems                += "        'visir_external'   : weblabdeusto_federation_demo,\n"
    if options[Creation.ADD_FEDERATED_SUBMARINE]:
        other_core_coordinator_external_servers += "    'submarine@Aquatic experiments'    : [ 'aquatic_external' ],\n"
        other_scheduling_systems                += "        'aquatic_external'   : weblabdeusto_federation_demo,\n"
        

    machine_config_py =("# It must be here to retrieve this information from the dummy\n"
                        "core_universal_identifier       = %(core_universal_identifier)r\n"
                        "core_universal_identifier_human = %(core_universal_identifier_human)r\n"
                        "\n"
                        "db_engine          = %(db_engine)r\n"
                        "db_host            = %(db_host)r\n"
                        "db_port            = %(db_port)r # None for default\n"
                        "db_database        = %(db_name)r\n"
                        "weblab_db_username = %(db_user)r\n"
                        "weblab_db_password = %(db_password)r\n"
                        "\n"
                        "debug_mode   = True\n"
                        "\n"
                        "#########################\n"
                        "# General configuration #\n"
                        "#########################\n"
                        "\n"
                        "server_hostaddress = %(server_hostaddress)r\n"
                        "server_admin       = %(server_admin)r\n"
                        "\n"
                        "################################\n"
                        "# Admin Notifier configuration #\n"
                        "################################\n"
                        "\n"
                        "mail_notification_enabled = False\n"
                        "\n"
                        "##########################\n"
                        "# Sessions configuration #\n"
                        "##########################\n"
                        "\n"
                        "core_session_type = %(session_storage)r\n"
                        "\n"
                        "%(session_db)ssession_sqlalchemy_engine   = %(session_db_engine)r\n"
                        "%(session_db)ssession_sqlalchemy_host     = %(session_db_host)r\n"
                        "%(session_db)ssession_sqlalchemy_username = %(session_db_user)r\n"
                        "%(session_db)ssession_sqlalchemy_password = %(session_db_passwd)r\n"
                        "\n"
                        "%(session_db)ssession_lock_sqlalchemy_engine   = %(session_db_engine)r\n"
                        "%(session_db)ssession_lock_sqlalchemy_host     = %(session_db_host)r\n"
                        "%(session_db)ssession_lock_sqlalchemy_username = %(session_db_user)r\n"
                        "%(session_db)ssession_lock_sqlalchemy_password = %(session_db_passwd)r\n"
                        "\n"
                        "%(session_redis)ssession_redis_host = %(session_redis_host)r\n"
                        "%(session_redis)ssession_redis_port = %(session_redis_port)r\n"
                        "%(session_redis)score_session_pool_id = %(session_redis_db)r\n"
                        "%(session_redis)score_alive_users_session_pool_id = %(session_redis_db)r\n"
                        "\n"
                        "##############################\n"
                        "# Core generic configuration #\n"
                        "##############################\n"
                        "core_store_students_programs      = False\n"
                        "core_store_students_programs_path = 'files_stored'\n"
                        "core_experiment_poll_time         = %(poll_time)r # seconds\n"
                        "\n"
                        "core_server_url = %(server_url)r\n"
                        "\n"
                        "############################\n"
                        "# Scheduling configuration #\n"
                        "############################\n"
                        "\n"
                        "core_coordination_impl = %(core_coordinator_engine)r\n"
                        "\n"
                        "%(coord_redis)scoordinator_redis_db       = %(core_coordinator_redis_db)r\n"
                        "%(coord_redis)scoordinator_redis_password = %(core_coordinator_redis_password)r\n"
                        "%(coord_redis)scoordinator_redis_port     = %(core_coordinator_redis_port)r\n"
                        "\n"
                        "%(coord_db)score_coordinator_db_name      = %(core_coordinator_db_name)r\n"
                        "%(coord_db)score_coordinator_db_engine    = %(core_coordinator_db_engine)r\n"
                        "%(coord_db)score_coordinator_db_host      = %(core_coordinator_db_host)r\n"
                        "%(coord_db)score_coordinator_db_username  = %(core_coordinator_db_username)r\n"
                        "%(coord_db)score_coordinator_db_password  = %(core_coordinator_db_password)r\n"
                        "\n"
                        "core_coordinator_laboratory_servers = {\n"
                        "%(laboratory_servers)s\n"
                        "}\n"
                        "\n"
                        "core_coordinator_external_servers = {\n"
                        "    'external-robot-movement@Robot experiments'   : [ 'robot_external' ],\n"
                        "%(other_core_coordinator_external_servers)s"
                        "}\n"
                        "\n"
                        "weblabdeusto_federation_demo = ('EXTERNAL_WEBLAB_DEUSTO', {\n"
                        "                                    'baseurl' : 'https://www.weblab.deusto.es/weblab/',\n"
                        "                                    'login_baseurl' : 'https://www.weblab.deusto.es/weblab/',\n"
                        "                                    'username' : 'weblabfed',\n"
                        "                                    'password' : 'password',\n"
                        "                                    'experiments_map' : {'external-robot-movement@Robot experiments' : 'robot-movement@Robot experiments'}\n"
                        "                            })\n"
                        "\n"
                        "core_scheduling_systems = {\n"
                        "%(local_scheduling)s"
                        "        'robot_external'   : weblabdeusto_federation_demo,\n"
                        "%(other_scheduling_systems)s"
                        "    }\n"
                        "\n") % {
        'core_universal_identifier'               : str(uuid.uuid4()),
        'core_universal_identifier_human'         : options[Creation.SYSTEM_IDENTIFIER] or 'Generic system; not identified',
        'db_engine'                               : options[Creation.DB_ENGINE],
        'db_host'                                 : options[Creation.DB_HOST],
        'db_port'                                 : options[Creation.DB_PORT],
        'db_name'                                 : options[Creation.DB_NAME],
        'db_user'                                 : options[Creation.DB_USER],
        'db_password'                             : options[Creation.DB_PASSWD],
        'server_hostaddress'                      : options[Creation.SERVER_HOST],
        'server_admin'                            : options[Creation.ADMIN_MAIL],
        'server_url'                              : server_url,
        'poll_time'                               : options[Creation.POLL_TIME],
        'laboratory_servers'                      : laboratory_servers,
        'local_scheduling'                        : local_scheduling,
        'other_scheduling_systems'                : other_scheduling_systems,
        'other_core_coordinator_external_servers' : other_core_coordinator_external_servers,
        'session_storage'                         : session_storage,

        'session_db_engine'                       : options[Creation.SESSION_DB_ENGINE],
        'session_db_host'                         : options[Creation.SESSION_DB_HOST],
        'session_db_port'                         : options[Creation.SESSION_DB_PORT],
        'session_db_name'                         : options[Creation.SESSION_DB_NAME],
        'session_db_user'                         : options[Creation.SESSION_DB_USER],
        'session_db_passwd'                       : options[Creation.SESSION_DB_PASSWD],

        'session_redis_host'                      : options[Creation.SESSION_REDIS_HOST],
        'session_redis_port'                      : options[Creation.SESSION_REDIS_PORT],
        'session_redis_db'                        : options[Creation.SESSION_REDIS_DB],

        'core_coordinator_engine'                 : coord_engine,

        'core_coordinator_redis_db'               : options[Creation.COORD_REDIS_DB],
        'core_coordinator_redis_password'         : options[Creation.COORD_REDIS_PASSWD],
        'core_coordinator_redis_port'             : options[Creation.COORD_REDIS_PORT],

        'core_coordinator_db_username'            : options[Creation.COORD_DB_USER],
        'core_coordinator_db_password'            : options[Creation.COORD_DB_PASSWD],
        'core_coordinator_db_name'                : options[Creation.COORD_DB_NAME],
        'core_coordinator_db_engine'              : options[Creation.COORD_DB_ENGINE],
        'core_coordinator_db_host'                : options[Creation.COORD_DB_HOST],
        'core_coordinator_db_port'                : options[Creation.COORD_DB_PORT],

        'coord_db'                                : '' if options[Creation.COORD_ENGINE] == 'sql' else '# ',
        'coord_redis'                             : '' if options[Creation.COORD_ENGINE] == 'redis' else '# ',
        'session_db'                              : '' if session_storage == 'sqlalchemy' else '# ',
        'session_redis'                           : '' if session_storage == 'redis' else '# ',
    }


    open(os.path.join(machine_dir, 'configuration.xml'), 'w').write(machine_configuration_xml)
    open(os.path.join(machine_dir, 'machine_config.py'), 'w').write(machine_config_py)

    ports = {
        'core'  : [],
        'login' : [],
    }

    current_port = options[Creation.START_PORTS]
    creation_results[CreationResult.START_PORT] = current_port

    latest_core_server_directory = None
    for core_number in range(1, options[Creation.CORES] + 1):
        core_instance_dir = os.path.join(machine_dir, 'core_server%s' % core_number)
        latest_core_server_directory = core_instance_dir
        if not os.path.exists(core_instance_dir):
            os.mkdir(core_instance_dir)
       
        instance_configuration_xml = (
        """<?xml version="1.0" encoding="UTF-8"?>"""
		"""<servers \n"""
		"""    xmlns="http://www.weblab.deusto.es/configuration" \n"""
		"""    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n"""
		"""    xsi:schemaLocation="instance_configuration.xsd"\n"""
		""">\n"""
		"""    <user>weblab</user>\n"""
		"""\n"""
		"""    <server>login</server>\n"""
		"""    <server>core</server>\n""")

        if options[Creation.INLINE_LAB_SERV]:
            for n in range(1, options[Creation.LAB_COPIES] + 1):
                instance_configuration_xml += """    <server>laboratory%s</server>\n""" % n
            if not options[Creation.XMLRPC_EXPERIMENT]:
                for n in xrange(1, options[Creation.DUMMY_COPIES] + 1):
                    instance_configuration_xml += """    <server>experiment%s</server>\n""" % n
            if options[Creation.VISIR_SERVER]:
                instance_configuration_xml += """    <server>visir</server>\n"""
            if options[Creation.LOGIC_SERVER]:
                instance_configuration_xml += """    <server>logic</server>\n"""
            if options[Creation.VM_SERVER]:
                instance_configuration_xml += """     <server>vm</server>\n"""
           
            
        instance_configuration_xml += (
        """\n"""
		"""</servers>\n""")

        open(os.path.join(core_instance_dir, 'configuration.xml'), 'w').write(instance_configuration_xml)

        core_dir = os.path.join(core_instance_dir, 'core')
        if not os.path.exists(core_dir):
            os.mkdir(core_dir)

        login_dir = os.path.join(core_instance_dir, 'login')
        if not os.path.exists(login_dir):
            os.mkdir(login_dir)


        open(os.path.join(login_dir, 'configuration.xml'), 'w').write(
        """<?xml version="1.0" encoding="UTF-8"?>"""
		"""<server\n"""
		"""    xmlns="http://www.weblab.deusto.es/configuration" \n"""
		"""    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n"""
		"""    xsi:schemaLocation="http://www.weblab.deusto.es/configuration server_configuration.xsd"\n"""
		""">\n"""
		"""\n"""
		"""    <configuration file="server_config.py" />\n"""
		"""\n"""
		"""    <type>weblab.data.server_type::Login</type>\n"""
		"""    <methods>weblab.methods::Login</methods>\n"""
		"""\n"""
		"""    <implementation>weblab.login.server.LoginServer</implementation>\n"""
		"""\n"""
		"""    <protocols>\n"""
		"""        <protocol name="Direct">\n"""
		"""            <coordinations>\n"""
		"""                <coordination></coordination>\n"""
		"""            </coordinations>\n"""
		"""            <creation></creation>\n"""
		"""        </protocol>\n"""
		"""    </protocols>\n"""
		"""</server>\n""")

        login_config = {
            'soap'   : current_port + 0,
            'xmlrpc' : current_port + 1,
            'json'   : current_port + 2,
            'web'    : current_port + 3,
            'route'  : 'route%s' % core_number,
        }
        ports['login'].append(login_config)

        core_config = {
            'soap'   : current_port + 4,
            'xmlrpc' : current_port + 5,
            'json'   : current_port + 6,
            'web'    : current_port + 7,
            'admin'  : current_port + 8,
            'route'  : 'route%s' % core_number,
            'clean'  : core_number == 1
        }
        ports['core'].append(core_config)

        core_port = current_port + 9

        current_port += 10

        open(os.path.join(login_dir, 'server_config.py'), 'w').write((
        "login_facade_server_route = %(route)r\n"
		"login_facade_soap_port    = %(soap)r\n"
		"login_facade_xmlrpc_port  = %(xmlrpc)r\n"
		"login_facade_json_port    = %(json)r\n"
		"login_web_facade_port     = %(web)r\n") % login_config)

        open(os.path.join(core_dir, 'configuration.xml'), 'w').write(
        """<?xml version="1.0" encoding="UTF-8"?>"""
		"""<server\n"""
		"""    xmlns="http://www.weblab.deusto.es/configuration" \n"""
		"""    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n"""
		"""    xsi:schemaLocation="http://www.weblab.deusto.es/configuration server_configuration.xsd"\n"""
		""">\n"""
		"""\n"""
		"""    <configuration file="server_config.py" />\n"""
		"""\n"""
		"""    <type>weblab.data.server_type::UserProcessing</type>\n"""
		"""    <methods>weblab.methods::UserProcessing</methods>\n"""
		"""\n"""
		"""    <implementation>weblab.core.server.UserProcessingServer</implementation>\n"""
		"""\n"""
		"""    <!-- <restriction>something else</restriction> -->\n"""
		"""\n"""
		"""    <protocols>\n"""
		"""        <!-- This server supports both Direct calls, as SOAP calls -->\n"""
		"""        <protocol name="Direct">\n"""
		"""            <coordinations>\n"""
		"""                <coordination></coordination>\n"""
		"""            </coordinations>\n"""
		"""            <creation></creation>\n"""
		"""        </protocol>\n"""
		"""        <protocol name="SOAP">\n"""
		"""            <coordinations>\n"""
		"""                <coordination>\n"""
		"""                    <parameter name="address" value="127.0.0.1:%(port)s@NETWORK" />\n"""
		"""                </coordination>\n"""
		"""            </coordinations>\n"""
		"""            <creation>\n"""
		"""                <parameter name="address" value=""     />\n"""
		"""                <parameter name="port"    value="%(port)s" />\n"""
		"""            </creation>\n"""
		"""        </protocol>\n"""
		"""    </protocols>\n"""
		"""</server>\n""" % { 'port' : core_port })

        open(os.path.join(core_dir, 'server_config.py'), 'w').write((
        "core_coordinator_clean   = %(clean)r\n"
        "core_facade_server_route = %(route)r\n"
		"core_facade_soap_port    = %(soap)r\n"
		"core_facade_xmlrpc_port  = %(xmlrpc)r\n"
		"core_facade_json_port    = %(json)r\n"
		"core_web_facade_port     = %(web)r\n"
        "admin_facade_json_port   = %(admin)r\n") % core_config)

    for n in range(1, options[Creation.LAB_COPIES] + 1):
        laboratory_instance_name = 'core_server1' if options[Creation.INLINE_LAB_SERV] else 'laboratory%s' % n
        experiments_in_lab = laboratory_experiment_instances[n - 1]

        if options[Creation.INLINE_LAB_SERV]:
            lab_instance_dir = latest_core_server_directory
        else:
            lab_instance_dir = os.path.join(machine_dir, 'laboratory%s' % n)
            if not os.path.exists(lab_instance_dir):
                os.mkdir(lab_instance_dir)

            lab_instance_configuration_xml = (
                """<?xml version="1.0" encoding="UTF-8"?>\n"""
                """<servers \n"""
                """    xmlns="http://www.weblab.deusto.es/configuration" \n"""
                """    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n"""
                """    xsi:schemaLocation="instance_configuration.xsd"\n"""
                """>\n"""
                """    <user>weblab</user>\n"""
                """\n"""
                """    <server>laboratory%s</server>\n""" % n
                )

            if not options[Creation.XMLRPC_EXPERIMENT]:
                for dummy_id in experiments_in_lab.get('dummy', []):
                    lab_instance_configuration_xml += """    <server>experiment%s</server>\n""" % dummy_id

            if len(experiments_in_lab.get('visir', [])) > 0:
                lab_instance_configuration_xml += """    <server>visir</server>\n"""

            if 'logic' in experiments_in_lab:
                lab_instance_configuration_xml += """    <server>logic</server>\n"""
				
            if 'vm' in experiments_in_lab:
                lab_instance_configuration_xml += """     <server>vm</server>\n"""

            lab_instance_configuration_xml += """</servers>\n"""

            open(os.path.join(lab_instance_dir, 'configuration.xml'), 'w').write( lab_instance_configuration_xml )

        lab_dir = os.path.join(lab_instance_dir, 'laboratory%s' % n)
        if not os.path.exists(lab_dir):
            os.mkdir(lab_dir)

        port1 = current_port
        current_port += 1
        port2 = current_port
        open(os.path.join(lab_dir, 'configuration.xml'), 'w').write((
            """<?xml version="1.0" encoding="UTF-8"?>\n"""
            """<server\n"""
            """    xmlns="http://www.weblab.deusto.es/configuration" \n"""
            """    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n"""
            """    xsi:schemaLocation="http://www.weblab.deusto.es/configuration server_configuration.xsd"\n"""
            """>\n"""
            """\n"""
            """    <configuration file="server_config.py" />\n"""
            """\n"""
            """    <type>weblab.data.server_type::Laboratory</type>\n"""
            """    <methods>weblab.methods::Laboratory</methods>\n"""
            """\n"""
            """    <implementation>weblab.lab.server.LaboratoryServer</implementation>\n"""
            """\n"""
            """    <protocols>\n"""
            """        <protocol name="Direct">\n"""
            """            <coordinations>\n"""
            """                <coordination></coordination>\n"""
            """            </coordinations>\n"""
            """            <creation></creation>\n"""
            """        </protocol>\n"""
            """        <protocol name="SOAP">\n"""
            """            <coordinations>\n"""
            """                <coordination>\n"""
            """                    <parameter name="address" value="127.0.0.1:%(port)s@NETWORK" />\n"""
            """                </coordination>\n"""
            """            </coordinations>\n"""
            """            <creation>\n"""
            """                <parameter name="address" value=""     />\n"""
            """                <parameter name="port"    value="%(port)s" />\n"""
            """            </creation>\n"""
            """        </protocol>\n"""
            """        <protocol name="XMLRPC">\n"""
            """            <coordinations>\n"""
            """                <coordination>\n"""
            """                    <parameter name="address" value="127.0.0.1:%(port2)s@NETWORK" />\n"""
            """                </coordination>\n"""
            """            </coordinations>\n"""
            """            <creation>\n"""
            """                <parameter name="address" value=""     />\n"""
            """                <parameter name="port"    value="%(port2)s" />\n"""
            """            </creation>\n"""
            """        </protocol>\n"""
            """    </protocols>\n"""
            """</server>\n""") % {'port' : port1, 'port2' : port2})
        current_port += 1

        laboratory_config_py = (
            """##################################\n"""
            """# Laboratory Server configuration #\n"""
            """##################################\n"""
            """\n"""
            """laboratory_assigned_experiments = {\n"""
        )

        for dummy_id in experiments_in_lab.get('dummy', []):
            lab_config_args = { 'dummy' : options[Creation.DUMMY_NAME], 'dummy_category_name' : options[Creation.DUMMY_CATEGORY_NAME], 'n' : dummy_id }

            if options[Creation.XMLRPC_EXPERIMENT]:
                lab_config_args['instance'] = 'exp_instance'
                lab_config_args['machine']  = 'exp_machine'
            else:
                lab_config_args['instance'] = laboratory_instance_name
                lab_config_args['machine']  = 'core_machine'

            laboratory_config_py += (
                """        'exp%(n)s:%(dummy)s@%(dummy_category_name)s' : {\n"""
                """                'coord_address' : 'experiment%(n)s:%(instance)s@%(machine)s',\n"""
                """                'checkers' : ()\n"""
                """            },\n"""
            ) % lab_config_args

        for visir_id in experiments_in_lab.get('visir', []):
            laboratory_config_py += (
                """        'exp%(n)s:%(visir_name)s@Visir experiments' : {\n"""
                """                'coord_address' : 'visir:%(instance)s@core_machine',\n"""
                """                'checkers' : ()\n"""
                """            },\n"""
            ) % { 'instance' : laboratory_instance_name, 
                  'visir_name' : options[Creation.VISIR_EXPERIMENT_NAME], 'n' : visir_id }
            
        if 'vm' in experiments_in_lab:
            laboratory_config_py += (
                """        'exp1:%(name)s@VM experiments' : {\n"""
                """                'coord_address' : 'vm:%(instance)s@core_machine',\n"""
                """                'checkers' : ()\n"""
                """            },\n"""
            ) % { 'instance' : laboratory_instance_name,
                  'name' : options[Creation.VM_EXPERIMENT_NAME] }

        if 'logic' in experiments_in_lab:
            laboratory_config_py += (
                """        'exp1:ud-logic@PIC experiments' : {\n"""
                """                'coord_address' : 'logic:%(instance)s@core_machine',\n"""
                """                'checkers' : ()\n"""
                """            },\n"""
            ) % { 'instance' : laboratory_instance_name }

        laboratory_config_py += """    }\n"""

        open(os.path.join(lab_dir, 'server_config.py'), 'w').write(laboratory_config_py)

        for dummy_id in experiments_in_lab.get('dummy', []):
            if options[Creation.XMLRPC_EXPERIMENT]:
                experiment_dir = xmlrpc_server_dir
            else:
                experiment_dir = os.path.join(lab_instance_dir, 'experiment%s' % dummy_id)

            if not os.path.exists(experiment_dir):
                os.mkdir(experiment_dir)

            experiment_configuration = (
                """<?xml version="1.0" encoding="UTF-8"?>\n"""
                """<server\n"""
                """    xmlns="http://www.weblab.deusto.es/configuration" \n"""
                """    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n"""
                """    xsi:schemaLocation="http://www.weblab.deusto.es/configuration server_configuration.xsd"\n"""
                """>\n"""
                """\n"""
                """    <configuration file="server_config.py" />\n"""
                """\n"""
                """    <type>weblab.data.server_type::Experiment</type>\n"""
                """    <methods>weblab.methods::Experiment</methods>\n"""
                """\n"""
                """    <implementation>experiments.dummy.DummyExperiment</implementation>\n"""
                """\n"""
                """    <restriction>%(dummy)s@%(dummy_category_name)s</restriction>\n"""
                """\n"""
                """    <protocols>\n"""
                """        <protocol name="Direct">\n"""
                """            <coordinations>\n"""
                """                <coordination></coordination>\n"""
                """            </coordinations>\n"""
                """            <creation></creation>\n"""
                """        </protocol>\n""") % { 'dummy' : options[Creation.DUMMY_NAME], 'dummy_category_name' : options[Creation.DUMMY_CATEGORY_NAME] } 

            if options[Creation.XMLRPC_EXPERIMENT]:
                experiment_configuration += (
                """        <protocol name="XMLRPC">\n"""
                """            <coordinations>\n"""
                """                <coordination>\n"""
                """                    <parameter name="address" value="127.0.0.1:%(port)s@NETWORK" />\n"""
                """                </coordination>\n"""
                """            </coordinations>\n"""
                """            <creation>\n"""
                """                <parameter name="address" value="127.0.0.1"     />\n"""
                """                <parameter name="port"    value="%(port)s" />\n"""
                """            </creation>\n"""
                """        </protocol>\n"""
                ) % {'port' : options[Creation.XMLRPC_EXPERIMENT_PORT] }

            experiment_configuration += (
                """    </protocols>\n"""
                """</server>\n""")

            open(os.path.join(experiment_dir, 'configuration.xml'), 'w').write(experiment_configuration)

            open(os.path.join(experiment_dir, 'server_config.py'), 'w').write(
                "dummy_verbose = True\n")


        if len(experiments_in_lab.get('visir', [])) > 0:
            visir_dir = os.path.join(lab_instance_dir, 'visir')
            if not os.path.exists(visir_dir):
                os.mkdir(visir_dir)

            open(os.path.join(visir_dir, 'configuration.xml'), 'w').write((
                """<?xml version="1.0" encoding="UTF-8"?>\n"""
                """<server\n"""
                """    xmlns="http://www.weblab.deusto.es/configuration" \n"""
                """    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n"""
                """    xsi:schemaLocation="http://www.weblab.deusto.es/configuration server_configuration.xsd"\n"""
                """>\n"""
                """\n"""
                """    <configuration file="server_config.py" />\n"""
                """\n"""
                """    <type>weblab.data.server_type::Experiment</type>\n"""
                """    <methods>weblab.methods::Experiment</methods>\n"""
                """\n"""
                """    <implementation>experiments.visir.VisirExperiment</implementation>\n"""
                """\n"""
                """    <protocols>\n"""
                """        <protocol name="Direct">\n"""
                """            <coordinations>\n"""
                """                <coordination></coordination>\n"""
                """            </coordinations>\n"""
                """            <creation></creation>\n"""
                """        </protocol>\n"""
                """    </protocols>\n"""
                """</server>\n"""))

            if options[Creation.VISIR_MEASUREMENT_SERVER] is not None:
                if not ':' in options[Creation.VISIR_MEASUREMENT_SERVER] or options[Creation.VISIR_MEASUREMENT_SERVER].startswith(('http://','https://')) or '/' in options[Creation.VISIR_MEASUREMENT_SERVER].split(':')[1]:
                    print >> stderr, "VISIR measurement server invalid format. Expected: server:port Change the configuration file"
                visir_measurement_server = options[Creation.VISIR_MEASUREMENT_SERVER]
            else:
                result = urlparse.urlparse(options[Creation.VISIR_BASE_URL])
                visir_measurement_server = result.netloc.split(':')[0] + ':8080'

            if options[Creation.VISIR_USE_PHP]:
                visir_php = ("""vt_use_visir_php = True\n"""
                """vt_base_url = "%(visir_base_url)s"\n"""
                """vt_login_url = "%(visir_base_url)sindex.php?sel=login_check"\n"""
                """vt_login_email = "%(visir_login)s"\n"""
                """vt_login_password = "%(visir_password)s"\n""" % {
                    'visir_base_url' : options[Creation.VISIR_BASE_URL],
                    'visir_login'    : options[Creation.VISIR_LOGIN],
                    'visir_password' : options[Creation.VISIR_PASSWORD],
                })
            else:
                visir_php = """vt_use_visir_php = False\n"""
               

            open(os.path.join(visir_dir, 'server_config.py'), 'w').write((
                """vt_measure_server_addr = "%(visir_measurement_server)s"\n"""
                """vt_measure_server_target = "/measureserver"\n"""
                """\n"""
                + visir_php +
                """\n"""
                """# You can also specify a directory where different circuits will be loaded, such as:\n"""
                """#\n"""
                """# vt_circuits_dir = "/home/weblab/Dropbox/VISIR-Circuits/"\n"""
                """#\n"""
                """#\n"""
                """# You can also define your own library.xml in this configuration file by uncommenting:\n"""
                """#\n"""
                """# vt_library = \"\"\"\n"""
                """# <!DOCTYPE components PUBLIC "-//Open labs//DTD COMPONENTS 1.0//EN" "http://openlabs.bth.se/DTDs/components-1.0.dtd">\n"""
                """# <components>\n"""
                """#    <component type="R" value="1.5M" pins="2">\n"""
                """#        <rotations>\n"""
                """#            <rotation ox="-27" oy ="-6" image="r_1.5M.png" rot="0">\n"""
                """#                <pins><pin x="-26" y="0" /><pin x="26"  y="0" /></pins>\n"""
                """#            </rotation>\n"""
                """#            <rotation ox="-7" oy ="-27" image="r_1.5M.png" rot="90">\n"""
                """#                <pins><pin x="0" y="-26" /><pin x="0" y="26" /></pins>\n"""
                """#            </rotation>\n"""
                """#        </rotations>\n"""
                """#    </component>\n"""
                """#    <!-- More components -->\n"""
                """#\n"""
                """# </components>\n"""
                """# \"\"\"\n"""
                """#\n"""
                """\n""") % {'visir_measurement_server' : visir_measurement_server })
        
        if 'vm' in experiments_in_lab:
            vm_dir = os.path.join(lab_instance_dir, 'vm')
            if not os.path.exists(vm_dir):
                os.mkdir(vm_dir)
                
            open(os.path.join(vm_dir, 'configuration.xml'), 'w').write((
                """<?xml version="1.0" encoding="UTF-8"?>\n"""
                """<server\n"""
                """    xmlns="http://www.weblab.deusto.es/configuration" \n"""
                """    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n"""
                """    xsi:schemaLocation="http://www.weblab.deusto.es/configuration server_configuration.xsd"\n"""
                """>\n"""
                """\n"""
                """    <configuration file="server_config.py" />\n"""
                """\n"""
                """    <type>weblab.data.server_type::Experiment</type>\n"""
                """    <methods>weblab.methods::Experiment</methods>\n"""
                """\n"""
                """    <implementation>experiments.vm.server.VMExperiment</implementation>\n"""
                """\n"""
                """    <protocols>\n"""
                """        <protocol name="Direct">\n"""
                """            <coordinations>\n"""
                """                <coordination></coordination>\n"""
                """            </coordinations>\n"""
                """            <creation></creation>\n"""
                """        </protocol>\n"""
                """    </protocols>\n"""
                """</server>\n"""))
            
            # Load and fill the config file template
            template = load_template("vm_server_config.py.template")
            cfgfile = template % { "vm_storage_dir" : options[Creation.VM_STORAGE_DIR], 
                                  "vbox_vm_name" : options[Creation.VBOX_VM_NAME], 
                                  "vbox_base_snapshot" : options[Creation.VBOX_BASE_SNAPSHOT],
                                  "vm_url" : options[Creation.VM_URL],
                                  "http_query_user_manager_url" : options[Creation.HTTP_QUERY_USER_MANAGER_URL],
                                  "vm_estimated_load_time" : options[Creation.VM_ESTIMATED_LOAD_TIME] }
            
            open(os.path.join(vm_dir, 'server_config.py'), 'w').write(
                cfgfile
            )

        if 'logic' in experiments_in_lab:
            logic_dir = os.path.join(lab_instance_dir, 'logic')
            if not os.path.exists(logic_dir):
                os.mkdir(logic_dir)

            open(os.path.join(logic_dir, 'configuration.xml'), 'w').write((
                """<?xml version="1.0" encoding="UTF-8"?>\n"""
                """<server\n"""
                """    xmlns="http://www.weblab.deusto.es/configuration" \n"""
                """    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n"""
                """    xsi:schemaLocation="http://www.weblab.deusto.es/configuration server_configuration.xsd"\n"""
                """>\n"""
                """\n"""
                """    <configuration file="server_config.py" />\n"""
                """\n"""
                """    <type>weblab.data.server_type::Experiment</type>\n"""
                """    <methods>weblab.methods::Experiment</methods>\n"""
                """\n"""
                """    <implementation>experiments.logic.server.LogicExperiment</implementation>\n"""
                """\n"""
                """    <protocols>\n"""
                """        <protocol name="Direct">\n"""
                """            <coordinations>\n"""
                """                <coordination></coordination>\n"""
                """            </coordinations>\n"""
                """            <creation></creation>\n"""
                """        </protocol>\n"""
                """    </protocols>\n"""
                """</server>\n"""))

            open(os.path.join(logic_dir, 'server_config.py'), 'w').write(
            """logic_webcam_url = ""\n"""
            """\n"""
            )


    files_stored_dir = os.path.join(directory, 'files_stored')
    if not os.path.exists(files_stored_dir):
        os.mkdir(files_stored_dir)

    if verbose: print >> stdout, "[done]"

    ###########################################
    # 
    # Generate logs directory and config
    # 

    if verbose: print >> stdout, "Creating logs directories and configuration files...",; stdout.flush()

    logs_dir = os.path.join(directory, 'logs')
    if not os.path.exists(logs_dir):
        os.mkdir(logs_dir)

    logs_config_dir = os.path.join(logs_dir, 'config')
    if not os.path.exists(logs_config_dir):
        os.mkdir(logs_config_dir)

    # TODO: use the generation module instead of hardcoding it here

    server_names = []
    for core_number in range(1, options[Creation.CORES] + 1):
        server_names.append('server%s' % core_number)

    if not options[Creation.INLINE_LAB_SERV]:
        for n in range(1, options[Creation.LAB_COPIES] + 1):
            server_names.append('laboratory%s' % n)
    if options[Creation.XMLRPC_EXPERIMENT] or not options[Creation.INLINE_LAB_SERV]:
        server_names.append('experiment')

    if options[Creation.XMLRPC_EXPERIMENT]:
        server_names.append('exp_instance')

    for server_name in server_names:
        logging_file = (
            """# \n"""
            """# logging module file generated by generate_logging_file.py\n"""
            """# \n"""
            """# You should change the script configuration instead of\n"""
            """# this file directly.\n"""
            """# \n"""
            """# Call it like: \n"""
            """#   Generator( \n"""
            """#       {'weblab.core.coordinator': ('WARNING', False), 'weblab.login': ('INFO', True), 'weblab.login.database': ('WARNING', False), 'weblab.lab': ('INFO', True), 'weblab.facade': ('INFO', True), 'weblab.core.facade': ('WARNING', False), 'weblab': ('WARNING', True), 'weblab.core.database': ('WARNING', False), 'weblab.login.facade': ('WARNING', False), 'voodoo': ('WARNING', True), 'weblab.core': ('INFO', True)}, \n"""
            """#       logs/sample_, \n"""
            """#       logs.txt, \n"""
            """#       52428800, \n"""
            """#       1099511627776, \n"""
            """#       False  \n"""
            """#   )\n"""
            """# \n"""
            """\n"""
            """[loggers]\n"""
            """keys=root,weblab_core_coordinator,weblab_login,weblab_login_database,weblab.lab,weblab_facade,weblab_core_facade,weblab,weblab_core_database,weblab_login_facade,voodoo,weblab_core\n"""
            """\n"""
            """[handlers]\n"""
            """keys=root_handler,weblab_login_handler,weblab.lab_handler,weblab_facade_handler,weblab_handler,voodoo_handler,weblab_core_handler\n"""
            """\n"""
            """[formatters]\n"""
            """keys=simpleFormatter\n"""
            """\n"""
            """[logger_root]\n"""
            """level=NOTSET\n"""
            """handlers=root_handler\n"""
            """propagate=0\n"""
            """parent=\n"""
            """channel=\n"""
            """\n"""
            """[logger_voodoo]\n"""
            """level=WARNING\n"""
            """handlers=voodoo_handler\n"""
            """qualname=voodoo\n"""
            """propagate=0\n"""
            """parent=root\n"""
            """channel=voodoo\n"""
            """\n"""
            """[logger_weblab]\n"""
            """level=WARNING\n"""
            """handlers=weblab_handler\n"""
            """qualname=weblab\n"""
            """propagate=0\n"""
            """parent=root\n"""
            """channel=weblab\n"""
            """\n"""
            """[logger_weblab_facade]\n"""
            """level=INFO\n"""
            """handlers=weblab_facade_handler\n"""
            """qualname=weblab.facade\n"""
            """propagate=0\n"""
            """parent=weblab\n"""
            """channel=weblab_facade\n"""
            """\n"""
            """[logger_weblab.lab]\n"""
            """level=INFO\n"""
            """handlers=weblab.lab_handler\n"""
            """qualname=weblab.lab\n"""
            """propagate=0\n"""
            """parent=weblab\n"""
            """channel=weblab.lab\n"""
            """\n"""
            """[logger_weblab_core]\n"""
            """level=INFO\n"""
            """handlers=weblab_core_handler\n"""
            """qualname=weblab.core\n"""
            """propagate=0\n"""
            """parent=weblab\n"""
            """channel=weblab_core\n"""
            """\n"""
            """[logger_weblab_core_facade]\n"""
            """level=WARNING\n"""
            """handlers=weblab_core_handler\n"""
            """qualname=weblab.core.facade\n"""
            """propagate=1\n"""
            """parent=weblab_core\n"""
            """channel=weblab_core_facade\n"""
            """\n"""
            """[logger_weblab_core_coordinator]\n"""
            """level=WARNING\n"""
            """handlers=weblab_core_handler\n"""
            """qualname=weblab.core.coordinator\n"""
            """propagate=1\n"""
            """parent=weblab_core\n"""
            """channel=weblab_core_coordinator\n"""
            """\n"""
            """[logger_weblab_core_database]\n"""
            """level=WARNING\n"""
            """handlers=weblab_core_handler\n"""
            """qualname=weblab.core.database\n"""
            """propagate=1\n"""
            """parent=weblab_core\n"""
            """channel=weblab_core_database\n"""
            """\n"""
            """[logger_weblab_login]\n"""
            """level=INFO\n"""
            """handlers=weblab_login_handler\n"""
            """qualname=weblab.login\n"""
            """propagate=0\n"""
            """parent=weblab\n"""
            """channel=weblab_login\n"""
            """\n"""
            """[logger_weblab_login_facade]\n"""
            """level=WARNING\n"""
            """handlers=weblab_login_handler\n"""
            """qualname=weblab.login.facade\n"""
            """propagate=1\n"""
            """parent=weblab_login\n"""
            """channel=weblab_login_facade\n"""
            """\n"""
            """[logger_weblab_login_database]\n"""
            """level=WARNING\n"""
            """handlers=weblab_login_handler\n"""
            """qualname=weblab.login.database\n"""
            """propagate=1\n"""
            """parent=weblab_login\n"""
            """channel=weblab_login_database\n"""
            """\n"""
            """[handler_root_handler]\n"""
            """class=handlers.RotatingFileHandler\n"""
            """formatter=simpleFormatter\n"""
            """args=('logs/sample__root_logs.%(server_number)s.txt','a',52428800,20971)\n"""
            """\n"""
            """[handler_weblab_login_handler]\n"""
            """class=handlers.RotatingFileHandler\n"""
            """formatter=simpleFormatter\n"""
            """args=('logs/sample__weblab_login_logs.%(server_number)s.txt','a',52428800,20971)\n"""
            """\n"""
            """[handler_weblab.lab_handler]\n"""
            """class=handlers.RotatingFileHandler\n"""
            """formatter=simpleFormatter\n"""
            """args=('logs/sample__weblab.lab_logs.%(server_number)s.txt','a',52428800,20971)\n"""
            """\n"""
            """[handler_weblab_facade_handler]\n"""
            """class=handlers.RotatingFileHandler\n"""
            """formatter=simpleFormatter\n"""
            """args=('logs/sample__weblab_facade_logs.%(server_number)s.txt','a',52428800,20971)\n"""
            """\n"""
            """[handler_weblab_handler]\n"""
            """class=handlers.RotatingFileHandler\n"""
            """formatter=simpleFormatter\n"""
            """args=('logs/sample__weblab_logs.%(server_number)s.txt','a',52428800,20971)\n"""
            """\n"""
            """[handler_voodoo_handler]\n"""
            """class=handlers.RotatingFileHandler\n"""
            """formatter=simpleFormatter\n"""
            """args=('logs/sample__voodoo_logs.%(server_number)s.txt','a',52428800,20971)\n"""
            """\n"""
            """[handler_weblab_core_handler]\n"""
            """class=handlers.RotatingFileHandler\n"""
            """formatter=simpleFormatter\n"""
            """args=('logs/sample__weblab_core_logs.%(server_number)s.txt','a',52428800,20971)\n"""
            """\n"""
            """[formatter_simpleFormatter]\n"""
            """format=%(asctime)s - %(name)s - %(levelname)s - %(message)s\n"""
            """datefmt=\n"""
            """class=logging.Formatter\n""") % {
                'server_number' : server_name,
                'asctime'       : '%(asctime)s',
                'name'          : '%(name)s',
                'levelname'     : '%(levelname)s',
                'message'       : '%(message)s',
            }
        open(os.path.join(logs_config_dir, 'logging.configuration.%s.txt' % server_name), 'w').write(logging_file)


    if verbose: print >> stdout, "[done]"

    ###########################################
    # 
    # Generate launch script
    # 

    if verbose: print >> stdout, "Creating launch file...",; stdout.flush()

    launch_script = (
        """#!/usr/bin/env python\n"""
        """#-*-*- encoding: utf-8 -*-*-\n"""
        """try:\n"""
        """    import signal\n"""
        """    \n"""
        """    import voodoo.gen.loader.Launcher as Launcher\n"""
        """    \n"""
        """    def before_shutdown():\n"""
        """        print "Stopping servers..."\n"""
        """    \n""")

    debugging_ports = []

    if options[Creation.INLINE_LAB_SERV]:
        debugging_core_port = current_port
        debugging_ports.append(debugging_core_port)
        current_port += 1

        launch_script += (
        """    launcher = Launcher.Launcher(\n"""
        """                '.',\n"""
        """                'core_machine',\n"""
        """                'core_server1',\n"""
        """                (\n"""
        """                    Launcher.SignalWait(signal.SIGTERM),\n"""
        """                    Launcher.SignalWait(signal.SIGINT),\n"""
        """                    Launcher.RawInputWait("Press <enter> or send a sigterm or a sigint to finish\\n")\n"""
        """                ),\n"""
        """                "logs/config/logging.configuration.server1.txt",\n"""
        """                before_shutdown,\n"""
        """                (\n"""
        """                     Launcher.FileNotifier("_file_notifier", "server started"),\n"""
        """                )\n"""
        """             )\n\n"""
        """    import voodoo.rt_debugger as rt_debugger\n"""
        """    rt_debugger.launch_debugger(%s)\n""") % debugging_core_port
    else:
        launch_script += (
        """    launcher = Launcher.MachineLauncher(\n"""
        """                '.',\n"""
        """                'core_machine',\n"""
        """                (\n"""
        """                    Launcher.SignalWait(signal.SIGTERM),\n"""
        """                    Launcher.SignalWait(signal.SIGINT),\n"""
        """                    Launcher.RawInputWait("Press <enter> or send a sigterm or a sigint to finish\\n")\n"""
        """                ),\n"""
        """                {\n""")

        for core_number in range(1, options[Creation.CORES] + 1):
            launch_script += """                    "core_server%s"     : "logs%sconfig%slogging.configuration.server%s.txt",\n""" % (core_number, os.sep, os.sep, core_number)
    
        for n in range(1, options[Creation.LAB_COPIES] + 1):
            launch_script += ("""                    "laboratory%s" : "logs%sconfig%slogging.configuration.laboratory%s.txt",\n""" % (n, os.sep, os.sep, n))

        launch_script += (
        """                },\n"""
        """                before_shutdown,\n"""
        """                (\n"""
        """                     Launcher.FileNotifier("_file_notifier", "server started"),\n"""
        """                ),\n"""
        """                pid_file = 'weblab.pid',\n""")
        waiting_port = current_port
        current_port += 1
        launch_script += """                waiting_port = %r,\n""" % waiting_port
        launch_script += """                debugger_ports = { \n"""
        for core_number in range(1, options[Creation.CORES] + 1):
            debugging_core_port = current_port
            debugging_ports.append(debugging_core_port)
            current_port += 1
            launch_script += """                     'core_server%s' : %s, \n""" % (core_number, debugging_core_port)
        launch_script += ("""                }\n"""
            """            )\n""")


    httpd_dir = os.path.join(directory, 'httpd')
    local_simple_server_conf_path = os.path.join('httpd', 'simple_server_config.py')
    simple_server_conf_path = os.path.join(httpd_dir, 'simple_server_config.py')

    http_server_port = options[Creation.HTTP_SERVER_PORT]
    if http_server_port is not None:
        launch_script += ("""\n"""
            """    from weblab.comm.proxy_server import start as start_proxy\n"""
            """    execfile(%r)\n"""
            """    start_proxy(%s, PATHS)\n"""
            """\n""") % (local_simple_server_conf_path, http_server_port)

    launch_script += ("""\n"""
        """    launcher.launch()\n"""
        """except:\n"""
        """    import traceback\n"""
        """    traceback.print_exc()\n"""
        """    raise\n"""
    )
    
    debugging_config = "# SERVERS is used by the WebLab Monitor to gather information from these ports.\n# If you open them, you'll see a Python shell.\n"
    debugging_config += "SERVERS = [\n"
    for debugging_port in debugging_ports:
        debugging_config += "    ('127.0.0.1','%s'),\n" % debugging_port
    debugging_config += "]\n\n"
    debugging_config += "BASE_URL = %r\n\n" % base_url
    debugging_config += "# PORTS is used by the WebLab Bot to know what\n# ports it should wait prior to start using\n# the simulated clients.\n"
    debugging_config += "PORTS = {\n"
    for protocol in ('soap','xmlrpc','json'):
        protocol_configuration = []
        for core_configuration in ports['core']:
            core_protocol_configuration = core_configuration.get(protocol, None)
            if core_protocol_configuration:
                protocol_configuration.append(core_protocol_configuration)
        debugging_config += """    %r : %r, \n""" % (protocol, protocol_configuration)

        protocol_configuration = []
        for login_configuration in ports['login']:
            login_protocol_configuration = login_configuration.get(protocol, None)
            if login_protocol_configuration:
                protocol_configuration.append(login_protocol_configuration)
        debugging_config += """    %r : %r, \n""" % (protocol + '_login', protocol_configuration)
    debugging_config += "}\n"


    if options[Creation.XMLRPC_EXPERIMENT]:
        # XML-RPC runner
        xmlrpc_launch_script = (
            """#!/usr/bin/env python\n"""
            """#-*-*- encoding: utf-8 -*-*-\n"""
            """try:\n"""
            """    import signal\n"""
            """    \n"""
            """    import voodoo.gen.loader.Launcher as Launcher\n"""
            """    \n"""
            """    def before_shutdown():\n"""
            """        print "Stopping servers..."\n"""
            """    \n""")

        xmlrpc_launch_script += (
        """    launcher = Launcher.MachineLauncher(\n"""
        """                '.',\n"""
        """                'exp_machine',\n"""
        """                (\n"""
        """                    Launcher.SignalWait(signal.SIGTERM),\n"""
        """                    Launcher.SignalWait(signal.SIGINT),\n"""
        """                    Launcher.RawInputWait("Press <enter> or send a sigterm or a sigint to finish\\n")\n"""
        """                ),\n"""
        """                {\n""")

        xmlrpc_launch_script += """                    "exp_instance" : "logs%sconfig%slogging.configuration.exp_instance.txt",\n""" % (os.sep,os.sep)

        xmlrpc_launch_script += (
        """                },\n"""
        """                before_shutdown,\n"""
        """                (\n"""
        """                     Launcher.FileNotifier("_file_notifier", "server started"),\n"""
        """                ),\n"""
        """                pid_file = 'weblab_xmlrpc.pid',\n""")
        waiting_port = current_port
        current_port += 1
        xmlrpc_launch_script += """                waiting_port = %r,\n""" % waiting_port
        xmlrpc_launch_script += ("""            )\n"""
            """\n"""
            """    launcher.launch()\n"""
            """except:\n"""
            """    import traceback\n"""
            """    traceback.print_exc()\n"""
            """    raise\n"""
        )

    open(os.path.join(directory, 'debugging.py'), 'w').write( debugging_config )
    open(os.path.join(directory, 'run.py'), 'w').write( launch_script )
    os.chmod(os.path.join(directory, 'run.py'), stat.S_IRWXU)

    if options[Creation.XMLRPC_EXPERIMENT]:
        open(os.path.join(directory, 'run-xmlrpc.py'), 'w').write( xmlrpc_launch_script )
        os.chmod(os.path.join(directory, 'run-xmlrpc.py'), stat.S_IRWXU)

    if verbose: print >> stdout, "[done]"

    ###########################################
    # 
    # Generate apache configuration file
    # 

    if verbose: print >> stdout, "Creating apache configuration files...",; stdout.flush()

    if not os.path.exists(httpd_dir):
        os.mkdir(httpd_dir)

    client_dir = os.path.join(directory, 'client')
    if not os.path.exists(client_dir):
        os.mkdir(client_dir)

    client_images_dir = os.path.join(client_dir, 'images')
    if not os.path.exists(client_images_dir):
        os.mkdir(client_images_dir)

    images_dir = '%(directory)s/client/images/'

    proxy_paths = [
        ('%(root)s$',                    'redirect:%(root)s/weblab/client'),
        ('%(root)s/$',                   'redirect:%(root)s/weblab/client'),
        ('%(root)s/weblab/$',            'redirect:%(root)s/weblab/client'),
        ('%(root)s/weblab/client$',      'redirect:%(root)s/weblab/client/index.html'),

        ('%(root)s/weblab/client/weblabclientlab/configuration.js',      'file:%(directory)s/client/configuration.js'),
        ('%(root)s/weblab/client/weblabclientadmin/configuration.js',    'file:%(directory)s/client/configuration.js'),

        ('%(root)s/weblab/client/weblabclientlab//img%(root-img)s/',     'file:%s' % images_dir),
        ('%(root)s/weblab/client/weblabclientadmin//img%(root-img)s/',   'file:%s' % images_dir),

        ('%(root)s/weblab/client',      'file:%(war_path)s'),
    ]

    apache_conf = (
        "\n"
        """<LocationMatch (.*)nocache\.js$>\n"""
        """   Header Set Cache-Control "max-age=0, no-store"\n"""
        """</LocationMatch>\n"""
        """\n"""
        """<LocationMatch (.*)configuration\.js$>\n"""
        """   Header Set Cache-Control "max-age=0, no-store"\n"""
        """</LocationMatch>\n"""
        """<Files *.cache.*>\n"""
        """   Header Set Cache-Control "max-age=2592000"\n"""
        """</Files>\n"""
        """\n"""
        """# Apache redirects the regular paths to the particular directories \n"""
        """RedirectMatch ^%(root)s$ %(root)s/weblab/client\n"""
        """RedirectMatch ^%(root)s/$ %(root)s/weblab/client\n"""
        """RedirectMatch ^%(root)s/weblab/$ %(root)s/weblab/client\n"""
        """RedirectMatch ^%(root)s/weblab/client/$ %(root)s/weblab/client/index.html\n"""
        """\n"""
        """Alias %(root)s/weblab/client/weblabclientlab/configuration.js      %(directory)s/client/configuration.js\n"""
        """Alias %(root)s/weblab/client/weblabclientadmin/configuration.js %(directory)s/client/configuration.js\n"""
        """\n"""
        """Alias %(root)s/weblab/client/weblabclientlab//img%(root-img)s/         %(directory)s/client/images/\n"""
        """Alias %(root)s/weblab/client/weblabclientadmin//img%(root-img)s/    %(directory)s/client/images/\n"""
        """\n"""        
        """Alias %(root)s/weblab/client                                    %(war_path)s\n"""
        """Alias %(root)s/weblab/                                          %(webserver_path)s\n"""
        """\n"""
        """<Location %(root)s/weblab/>\n"""
        """    Order allow,deny\n"""
        """    Allow from all\n"""
        """</Location>\n"""
        """\n"""
        """<Directory "%(directory)s">\n"""
        """        Options Indexes\n"""
        """        Order allow,deny\n"""
        """        Allow from all\n"""
        """</Directory>\n"""
        """\n"""        
        """<Directory "%(war_path)s">\n"""
        """        Options Indexes\n"""
        """        Order allow,deny\n"""
        """        Allow from all\n"""
        """</Directory>\n"""
        """\n"""        
        """<Directory "%(webserver_path)s">\n"""
        """        Options Indexes\n"""
        """        Order allow,deny\n"""
        """        Allow from all\n"""
        """</Directory>\n"""
        """\n"""        
        """# Apache redirects the requests retrieved to the particular server, using a stickysession if the sessions are based on memory\n"""
        """ProxyVia On\n"""
        """\n"""
        """ProxyPass                       %(root)s/weblab/soap/                 balancer://%(root-no-slash)s_weblab_cluster_soap/           stickysession=weblabsessionid lbmethod=bybusyness\n"""
        """ProxyPassReverse                %(root)s/weblab/soap/                 balancer://%(root-no-slash)s_weblab_cluster_soap/           stickysession=weblabsessionid\n"""
        """ProxyPass                       %(root)s/weblab/json/                 balancer://%(root-no-slash)s_weblab_cluster_json/           stickysession=weblabsessionid lbmethod=bybusyness\n"""
        """ProxyPassReverse                %(root)s/weblab/json/                 balancer://%(root-no-slash)s_weblab_cluster_json/           stickysession=weblabsessionid\n"""
        """ProxyPass                       %(root)s/weblab/xmlrpc/               balancer://%(root-no-slash)s_weblab_cluster_xmlrpc/         stickysession=weblabsessionid lbmethod=bybusyness\n"""
        """ProxyPassReverse                %(root)s/weblab/xmlrpc/               balancer://%(root-no-slash)s_weblab_cluster_xmlrpc/         stickysession=weblabsessionid\n"""
        """ProxyPass                       %(root)s/weblab/web/                  balancer://%(root-no-slash)s_weblab_cluster_web/            stickysession=weblabsessionid lbmethod=bybusyness\n"""
        """ProxyPassReverse                %(root)s/weblab/web/                  balancer://%(root-no-slash)s_weblab_cluster_web/            stickysession=weblabsessionid\n"""
        """ProxyPass                       %(root)s/weblab/login/soap/           balancer://%(root-no-slash)s_weblab_cluster_login_soap/     stickysession=loginweblabsessionid lbmethod=bybusyness\n"""
        """ProxyPassReverse                %(root)s/weblab/login/soap/           balancer://%(root-no-slash)s_weblab_cluster_login_soap/     stickysession=loginweblabsessionid\n"""
        """ProxyPass                       %(root)s/weblab/login/json/           balancer://%(root-no-slash)s_weblab_cluster_login_json/     stickysession=loginweblabsessionid lbmethod=bybusyness\n"""
        """ProxyPassReverse                %(root)s/weblab/login/json/           balancer://%(root-no-slash)s_weblab_cluster_login_json/     stickysession=loginweblabsessionid\n"""
        """ProxyPass                       %(root)s/weblab/login/xmlrpc/         balancer://%(root-no-slash)s_weblab_cluster_login_xmlrpc/   stickysession=loginweblabsessionid lbmethod=bybusyness\n"""
        """ProxyPassReverse                %(root)s/weblab/login/xmlrpc/         balancer://%(root-no-slash)s_weblab_cluster_login_xmlrpc/   stickysession=loginweblabsessionid\n"""
        """ProxyPass                       %(root)s/weblab/login/web/            balancer://%(root-no-slash)s_weblab_cluster_login_web/      stickysession=loginweblabsessionid lbmethod=bybusyness\n"""
        """ProxyPassReverse                %(root)s/weblab/login/web/            balancer://%(root-no-slash)s_weblab_cluster_login_web/      stickysession=loginweblabsessionid\n"""
        """ProxyPass                       %(root)s/weblab/administration/       balancer://%(root-no-slash)s_weblab_cluster_administration/ stickysession=weblabsessionid lbmethod=bybusyness\n"""
        """ProxyPassReverse                %(root)s/weblab/administration/       balancer://%(root-no-slash)s_weblab_cluster_administration/ stickysession=weblabsessionid\n"""
        "\n")


    apache_conf += "\n"
    apache_conf += "<Proxy balancer://%(root-no-slash)s_weblab_cluster_soap>\n"
    
    proxy_path = "proxy-sessions:weblabsessionid:"
    for core_configuration in ports['core']:
        d = { 'port' : core_configuration['soap'], 'route' : core_configuration['route'], 'root' : '%(root)s' }
        apache_conf += "    BalancerMember http://localhost:%(port)s/weblab/soap route=%(route)s\n" % d 
        proxy_path += '%(route)s=http://localhost:%(port)s/weblab/soap,' % d
    proxy_paths.append(('%(root)s/weblab/soap/',  proxy_path))
    
    apache_conf += "</Proxy>\n"
    apache_conf += "\n"
    
    apache_conf += """<Proxy balancer://%(root-no-slash)s_weblab_cluster_json>\n"""

    proxy_path = "proxy-sessions:weblabsessionid:"
    for core_configuration in ports['core']:
        d = { 'port' : core_configuration['json'], 'route' : core_configuration['route'], 'root' : '%(root)s' }
        apache_conf += """    BalancerMember http://localhost:%(port)s/weblab/json route=%(route)s\n""" % d
        proxy_path += '%(route)s=http://localhost:%(port)s/weblab/json,' % d
    proxy_paths.append(('%(root)s/weblab/json/', proxy_path))

    apache_conf += """</Proxy>\n"""
    apache_conf += """\n"""

    apache_conf += """<Proxy balancer://%(root-no-slash)s_weblab_cluster_xmlrpc>\n"""

    proxy_path = "proxy-sessions:weblabsessionid:"
    for core_configuration in ports['core']:
        d = { 'port' : core_configuration['xmlrpc'], 'route' : core_configuration['route'], 'root' : '%(root)s' }
        apache_conf += """    BalancerMember http://localhost:%(port)s/weblab/xmlrpc route=%(route)s\n""" % d
        proxy_path += '%(route)s=http://localhost:%(port)s/weblab/xmlrpc,' % d
    proxy_paths.append(('%(root)s/weblab/xmlrpc/', proxy_path))

    apache_conf += """</Proxy>\n"""
    apache_conf += """\n"""
    apache_conf += """<Proxy balancer://%(root-no-slash)s_weblab_cluster_web>\n"""

    proxy_path = "proxy-sessions:weblabsessionid:"
    for core_configuration in ports['core']:
        d = { 'port' : core_configuration['web'], 'route' : core_configuration['route'], 'root' : '%(root)s' }
        apache_conf += """    BalancerMember http://localhost:%(port)s/weblab/web route=%(route)s\n""" % d 
        proxy_path += '%(route)s=http://localhost:%(port)s/weblab/web/,' % d
    proxy_paths.append(('%(root)s/weblab/web/', proxy_path))

    apache_conf += """</Proxy>\n"""
    apache_conf += """\n"""
    apache_conf += """<Proxy balancer://%(root-no-slash)s_weblab_cluster_administration>\n"""

    proxy_path = "proxy-sessions:weblabsessionid:"
    for core_configuration in ports['core']:
        d = { 'port' : core_configuration['admin'], 'route' : core_configuration['route'], 'root' : '%(root)s' }
        apache_conf += """    BalancerMember http://localhost:%(port)s/weblab/administration route=%(route)s\n""" % d
        proxy_path += '%(route)s=http://localhost:%(port)s/weblab/administration,' % d
    proxy_paths.append(('%(root)s/weblab/administration', proxy_path))

    apache_conf += """</Proxy>\n"""
    apache_conf += """\n"""

    apache_conf += """<Proxy balancer://%(root-no-slash)s_weblab_cluster_login_soap>\n"""

    proxy_path = "proxy-sessions:loginweblabsessionid:"
    for core_configuration in ports['login']:
        d = { 'port' : core_configuration['soap'], 'route' : core_configuration['route'], 'root' : '%(root)s' }
        apache_conf += """    BalancerMember http://localhost:%(port)s/weblab/login/soap route=%(route)s \n""" % d
        proxy_path += '%(route)s=http://localhost:%(port)s/weblab/login/soap,' % d
    proxy_paths.append(('%(root)s/weblab/login/soap/', proxy_path))

    apache_conf += """</Proxy>\n"""
    apache_conf += """\n"""
    apache_conf += """<Proxy balancer://%(root-no-slash)s_weblab_cluster_login_json>\n"""

    proxy_path = "proxy-sessions:loginweblabsessionid:"
    for core_configuration in ports['login']:
        d = { 'port' : core_configuration['json'], 'route' : core_configuration['route'], 'root' : '%(root)s' }
        apache_conf += """    BalancerMember http://localhost:%(port)s/weblab/login/json route=%(route)s\n""" % d
        proxy_path += '%(route)s=http://localhost:%(port)s/weblab/login/json,' % d
    proxy_paths.append(('%(root)s/weblab/login/json/', proxy_path))

    apache_conf += """</Proxy>\n"""
    apache_conf += """\n"""
    apache_conf += """<Proxy balancer://%(root-no-slash)s_weblab_cluster_login_xmlrpc>\n"""

    proxy_path = "proxy-sessions:loginweblabsessionid:"
    for core_configuration in ports['login']:
        d = { 'port' : core_configuration['xmlrpc'], 'route' : core_configuration['route'], 'root' : '%(root)s' }
        apache_conf += """    BalancerMember http://localhost:%(port)s/weblab/login/xmlrpc route=%(route)s\n""" % d
        proxy_path += '%(route)s=http://localhost:%(port)s/weblab/login/xmlrpc,' % d
    proxy_paths.append(('%(root)s/weblab/login/xmlrpc/', proxy_path))

    apache_conf += """</Proxy>\n"""
    apache_conf += """\n"""
    apache_conf += """<Proxy balancer://%(root-no-slash)s_weblab_cluster_login_web>\n"""

    proxy_path = "proxy-sessions:loginweblabsessionid:"
    for core_configuration in ports['login']:
        d = { 'port' : core_configuration['web'], 'route' : core_configuration['route'], 'root' : '%(root)s' }
        apache_conf += """    BalancerMember http://localhost:%(port)s/weblab/login/web route=%(route)s\n""" % d
        proxy_path += '%(route)s=http://localhost:%(port)s/weblab/login/web,' % d
    proxy_paths.append(('%(root)s/weblab/login/web/', proxy_path))

    apache_conf += """</Proxy>\n"""
    apache_conf += """\n"""
    
    proxy_paths.append(('%(root)s/weblab/',            'file:%(webserver_path)s'))
    proxy_paths.append(('',                            'redirect:%(root)s/weblab/client/index.html'))

    if base_url in ('','/'):
        apache_root    = ''
    else:
        apache_root    = base_url
    
    apache_img_dir = '/client/images'

    apache_root_without_slash = apache_root[1:] if apache_root.startswith('/') else apache_root

    server_conf_dict = { 'root' : apache_root,  'root-no-slash' : apache_root_without_slash.replace('/','_'),
                'root-img' : apache_img_dir, 'directory' : os.path.abspath(directory).replace('\\','/'), 
                'war_path' : data_filename('war').replace('\\','/'), 'webserver_path' : data_filename('webserver').replace('\\','/') }

    apache_conf = apache_conf % server_conf_dict
    proxy_paths = eval(repr(proxy_paths) % server_conf_dict)
    proxy_paths_str = "PATHS = [ \n"
    for proxy_path in proxy_paths:
        proxy_paths_str += "    %s,\n" % repr(proxy_path)
    proxy_paths_str += "]\n"

    open(simple_server_conf_path, 'w').write( proxy_paths_str )

    apache_conf_path = os.path.join(httpd_dir, 'apache_weblab_generic.conf')
    open(apache_conf_path, 'w').write( apache_conf )

    creation_results[CreationResult.APACHE_FILE] = apache_conf_path

    if sys.platform.find('win') == 0:
        apache_windows_conf = """# At least in Debian based distributions as Debian itself
        # or Ubuntu, this can be done with the a2enmod command:
        # 
        #   root@plunder:~# a2enmod proxy
        #   root@plunder:~# a2enmod proxy_balancer_module
        #   root@plunder:~# a2enmod proxy_http_module
        #   root@plunder:~# a2enmod headers
        #   root@plunder:~# /etc/init.d/apache2 force-reload
        #  
        # However, in Microsoft Windows or other distributions, this 
        # might become slightly more difficult. To make it easy, you
        # can uncomment the following lines in Microsoft Windows if
        # using XAMPP as installer, or if you are under Mac OS X:
        # 
        <IfModule !mod_headers.c>
            LoadModule headers_module modules/mod_headers.so
        </IfModule>
        <IfModule !mod_proxy.c>
            LoadModule proxy_module modules/mod_proxy.so
        </IfModule>
        <IfModule !mod_proxy_balancer.c>
            LoadModule proxy_balancer_module modules/mod_proxy_balancer.so
        </IfModule>
        <IfModule !mod_proxy_http.c>
            LoadModule proxy_http_module modules/mod_proxy_http.so
        </IfModule>
        <IfModule !mod_lbmethod_byrequests>
        LoadModule lbmethod_byrequests_module modules/mod_lbmethod_byrequests.so
        </IfModule>
        <IfModule !mod_lbmethod_bybusyness>
        LoadModule lbmethod_bybusyness_module modules/mod_lbmethod_bybusyness.so
        </IfModule>
        <IfModule !mod_slotmem_shm>
        LoadModule slotmem_shm_module modules/mod_slotmem_shm.so
        </IfModule>
        """
        apache_windows_conf_path = os.path.join(httpd_dir, 'apache_weblab_windows.conf')
        open(apache_windows_conf_path, 'w').write( apache_windows_conf )

    if verbose: print >> stdout, "[done]"

    ###########################################
    # 
    #     Generate configuration.js files
    #
    configuration_js = {}

    lines = open(data_filename(os.path.join('war','weblabclientlab','configuration.js'))).readlines()
    new_lines = uncomment_json(lines)
    configuration_js_data = json.loads(''.join(new_lines))
    configuration_js['experiments']                    = configuration_js_data['experiments']

    dummy_list = list(configuration_js['experiments']['dummy'])
    found      = False
    for element in dummy_list:
        if element['experiment.name'] == options[Creation.DUMMY_NAME]:
            found = True
    if not found:
        dummy_list.append({'experiment.name' : options[Creation.DUMMY_NAME], 'experiment.category' : options[Creation.DUMMY_CATEGORY_NAME] })
    configuration_js['experiments']['dummy']           = dummy_list
    configuration_js['development']                    = False
    configuration_js['demo.available']                 = False
    configuration_js['sound.enabled']                  = False
    configuration_js['admin.email']                    = 'weblab@deusto.es'
    configuration_js['experiments.default_picture']    = '/img/experiments/default.jpg'

    extension = original_logo_path.split('.')[-1]
    if not len(extension) in (3,4):
        extension = 'jpg'

    configuration_js['host.entity.image.login']        = '/img/client/images/logo.%s' % extension
    configuration_js['host.entity.image']              = '/img/client/images/logo.%s' % extension
    configuration_js['host.entity.image.mobile']       = '/img/client/images/logo-mobile.%s' % extension

    if base_url != '' and base_url != '/':
        configuration_js['base.location']                  = base_url
    else:
        configuration_js['base.location']                  = ''
    

    logo_path        = '%s%s%s' % (directory, apache_img_dir, configuration_js['host.entity.image'].split('/images',1)[1])
    logo_mobile_path = '%s%s%s' % (directory, apache_img_dir, configuration_js['host.entity.image.mobile'].split('/images',1)[1])

    creation_results[CreationResult.IMG_FILE]        = logo_path
    creation_results[CreationResult.IMG_MOBILE_FILE] = logo_mobile_path

    if PIL_AVAILABLE:
        try:
            resize_image(original_logo_path, 250, 120, logo_path)
            resize_image(original_logo_path, 100,  50, logo_mobile_path)
        except Exception as e:
            print >> stderr, "Error resizing images (%s). Original images will be used." % e
            processed = False
        else:
            processed = True
    else:
        processed = False
        print >> stderr, "PIL (pip install pillow) not installed. Not resizing images."

    if not processed:
        logo_contents = open(original_logo_path, 'rb').read()
        logo_mobile_contents = logo_contents
        open(logo_path, 'wb').write(logo_contents)
        open(logo_mobile_path, 'wb').write(logo_mobile_contents)

    configuration_js['host.entity.link']               = options[Creation.ENTITY_LINK]
    configuration_js['facebook.like.box.visible']      = False
    configuration_js['create.account.visible']         = False
    json.dump(configuration_js, open(os.path.join(client_dir, 'configuration.js'), 'w'), indent = True)

    print >> stdout, ""
    print >> stdout, "Congratulations!"
    print >> stdout, "WebLab-Deusto system created"
    print >> stdout, ""
    if http_server_port is None:
        apache_httpd_path = r'your apache httpd.conf ( typically /etc/apache2/httpd.conf or C:\xampp\apache\conf\ )'
        if os.path.exists("/etc/apache2/conf.d"):
            apache_httpd_path = 'a new file that you must create called /etc/apache/conf.d/weblab'
        elif os.path.exists("/etc/apache2/httpd.conf"):
            apache_httpd_path = '/etc/apache2/httpd.conf'
        elif os.path.exists('C:\\xampp\\apache\\conf\\httpd.conf'):
            apache_httpd_path = 'C:\\xampp\\apache\\conf\\httpd.conf'

        print >> stdout, r"Append the following to", apache_httpd_path
        print >> stdout, ""
        print >> stdout, "    Include \"%s\"" % os.path.abspath(apache_conf_path).replace('\\','/')
        if sys.platform.find('win') == 0:
            print >> stdout, "    Include \"%s\"" % os.path.abspath(apache_windows_conf_path).replace('\\','/')
        else:
            print >> stdout, ""
            print >> stdout, "And enable the modules proxy proxy_balancer proxy_http headers."
            print >> stdout, "For instance, in Ubuntu you can run: "
            print >> stdout, ""
            print >> stdout, "    $ sudo a2enmod proxy proxy_balancer proxy_http headers"
        print >> stdout, ""
        print >> stdout, "Then restart apache. If you don't have apache don't worry, delete %s and " % directory
        print >> stdout, "run the creation script again but passing %s=8000 (or any free port)." % CreationFlags.HTTP_SERVER_PORT
        print >> stdout, ""
        print >> stdout, "Then run:"
    else:
        print >> stdout, "Run:"
    print >> stdout, ""
    print >> stdout, "     %s start %s" % (os.path.basename(sys.argv[0]), directory)
    print >> stdout, ""
    print >> stdout, "to start the WebLab-Deusto system. From that point, you'll be able to access: "
    print >> stdout, ""
    if http_server_port is not None:
        print >> stdout, "   http://localhost:%s/" % http_server_port
        print >> stdout, ""
        print >> stdout, "Or in production if you later want to deploy it in Apache:"
        print >> stdout, ""
    print >> stdout, "     %s " % server_url
    print >> stdout, ""
    print >> stdout, "And log in as '%s' using '%s' as password." % (options[Creation.ADMIN_USER], options[Creation.ADMIN_PASSWORD])
    print >> stdout, ""
    print >> stdout, "You should also configure the images directory with two images called:"
    print >> stdout, ""
    print >> stdout, "     %s and %s" % (logo_path, logo_mobile_path)
    print >> stdout, ""
    print >> stdout, "You can also add users, permissions, etc. from the web interface."
    print >> stdout, ""
    print >> stdout, "Enjoy!"
    print >> stdout, ""

    creation_results[CreationResult.END_PORT] = current_port
    return creation_results


