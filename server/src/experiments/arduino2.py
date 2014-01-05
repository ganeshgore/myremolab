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

import weblab.configuration_doc as configuration_doc
import weblab.experiment.experiment as Experiment

from voodoo.override import Override
import time
import os
import subprocess
import serial
import re
import glob

class Arduino2Experiment(Experiment.Experiment):
    def __init__(self, coord_address, locator, cfg_manager, *args, **kwargs):
        super(Arduino2Experiment, self).__init__(*args, **kwargs)
        self.cfg_manager = cfg_manager
        self.verbose           = cfg_manager.get_value('arduino_verbose', True)
        self.server_identifier = cfg_manager.get_doc_value(configuration_doc.CORE_UNIVERSAL_IDENTIFIER_HUMAN)

    @Override(Experiment.Experiment)
    def do_get_api(self):
        return "1"

    @Override(Experiment.Experiment)
    def do_start_experiment(self, *args, **kwargs):
        if self.verbose:
            print "Arduino 1 Experiment started"

    @Override(Experiment.Experiment)
    def do_send_command_to_device(self, command):
        if self.verbose:
            print "Received command: %s" % command

        if command == 'server_info':
            return self.server_identifier
        
        init_dir = os.getcwd()
        print "Initail Dirs" + init_dir
        
        dev = "/dev/ttyUSB0" 
        try:
            if (command == 'build'):
                os.chdir('ExperimentData/Arduino/Set01')
                proc = subprocess.Popen(["ino","build"], stdout=subprocess.PIPE)
                for line in iter(proc.stdout.readline, b''):
                    print ">>" , line 
                os.chdir(init_dir)
            elif (command == 'upload2board'):
                os.chdir('ExperimentData/Arduino/Set01')
                proc = subprocess.Popen(["ino","upload"], stdout=subprocess.PIPE)
                for line in iter(proc.stdout.readline, b''):
                    print ">>" , line
                os.chdir(init_dir)
            elif 'Change' in command:
                print "Sending Now"
                swtype = re.search("Change(.+?) (.+?) (.+?)", command).group(1)
                status = re.search("Change(.+?) (.+?) (.+?)", command).group(2)
                butNo =  re.search("Change(.+?) (.+?) (.+?)", command).group(3)
                print "swtype ", swtype ," | Status ", status ," | butNo " , butNo
                cmd2send = "G+I+"+('SW' if swtype == 'Switch' else 'PSW') + butNo + "+" + ('1' if status == 'on' else '0');
                print "Sent Command ", cmd2send
                try:
                    ser = serial.Serial(dev,9600,timeout=1)                
                    ser.write(str(cmd2send) + chr(0x0D))
                    reponse = ser.readline()
                    if(reponse == '' ):
                        print "Error No response from Device"
                    else:
                        print reponse
                    print "Closing port"
                    ser.close()
                except:
                    print "Device is not available at " + dev  
            elif (command == 'ResetOP'):
                print "Resetting OUTPUT device"
                try:
                    ser = serial.Serial(dev,9600,timeout=1)                
                    ser.write("G+RESET+OP" + chr(0x0D))
                    reponse = ser.readline()
                    if(reponse == '' ):
                        print "Error No response from Device"
                    else:
                        print reponse
                    print "Closing port"
                    ser.close()
                except:
                    print "Device is not available at " + dev                
            elif (command == 'ResetBoard'):
                print "Resetting OUTPUT device"
                try:
                    ser = serial.Serial(dev,9600,timeout=1)                
                    ser.write("G+RESET+BO" + chr(0x0D))
                    reponse = ser.readline()
                    if(reponse == '' ):
                        print "Error No response from Device"
                    else:
                        print reponse
                    print "Closing port"
                    ser.close()
                except:
                    print "Device is not available at " + dev
            elif 'Select' in command:
                print "Sending Now"
                selectdev = re.search("Select(.+?$)", command).group(1)
                print "Device ", selectdev
                cmd2send = "G+O+" + selectdev + "+1";
                print "Sent Command ", cmd2send
                try:
                    ser = serial.Serial(dev,9600,timeout=1)                
                    ser.write(str(cmd2send) + chr(0x0D))
                    reponse = ser.readline()
                    if(reponse == '' ):
                        print "Error No response from Device"
                    else:
                        print reponse
                    print "Closing port"
                    ser.close()
                except Exception as e: 
                    print "Device Error " + str(e)
            else: 
                print "Command Not Fount"
            
        except Exception as e: 
            print e
        return "Received command: %s" % command

    @Override(Experiment.Experiment)
    def do_send_file_to_device(self, content, file_info):
        if self.verbose:
            print "Received file with len: %s and file_info: %s" % (len(content), file_info)
        init_dir = os.getcwd()
        os.chdir('ExperimentData/Arduino/Set01/src')
        print "Saving sketch in " , str(os.getcwd())
        myFile = open('sketch.ino', 'w')
        myFile.write(content.decode(encoding='base64',errors='strict'))
        myFile.close()
        os.chdir(init_dir)
        return "Received file with len: %s and file_info: %s" % (len(content), file_info)

    @Override(Experiment.Experiment)
    def do_dispose(self):
        if self.verbose:
            print "dispose"


