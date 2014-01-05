core_store_students_programs      = False
core_store_students_programs_path = 'files_stored'
core_experiment_poll_time         = 350 # seconds

# Ports

core_facade_soap_port   = 20123
core_facade_xmlrpc_port = 29345
core_facade_json_port   = 28345

admin_facade_json_port   = 28545

core_web_facade_port   = 29745
core_facade_server_route = 'provider1-route'

# Will only work in JSON in this config file :-(
core_server_url = 'http://127.0.0.1:%s/weblab/' % core_facade_json_port

# Scheduling

core_coordination_impl = 'redis'
coordinator_redis_db   = 2

core_coordinator_db_name     = 'WebLabCoordination2'
core_coordinator_db_username = 'weblab'
core_coordinator_db_password = 'weblab'

core_coordinator_laboratory_servers = {
    "laboratory:main_instance@provider1_machine" : {
            "exp1|dummy1|Dummy experiments"        : "dummy1@dummy1_local",
            "exp1|dummy3_with_other_name|Dummy experiments"        : "dummy3_with_other_name@dummy3_with_other_name",
        }
}

core_coordinator_external_servers = {
    'dummy1@Dummy experiments'  : [ 'dummy1_external' ],
    'dummy4@Dummy experiments'  : [ 'dummy4' ],
}

_provider2_scheduling_config = ("EXTERNAL_WEBLAB_DEUSTO", {
                                    'baseurl' : 'http://127.0.0.1:38345/weblab/',
                                    'login_baseurl' : 'http://127.0.0.1:38645/weblab/',
                                    'username' : 'provider1',
                                    'password' : 'password',
                            })

core_scheduling_systems = {
        "dummy1_local"           : ("PRIORITY_QUEUE", {}),
        "dummy3_with_other_name" : ("PRIORITY_QUEUE", {}),
        "dummy4"                 : _provider2_scheduling_config,
        "dummy1_external"        : _provider2_scheduling_config,
    }

core_weblabdeusto_federation_retrieval_period = 0.1
