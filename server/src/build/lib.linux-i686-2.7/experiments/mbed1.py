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

from programmers import ArduinoProgrammer
from programmers import ArduinoBaseBoard

from voodoo.override import Override
import time
import os
import subprocess
import serial
import re
import glob

STATE_BUSY = "Not_ready"
STATE_PROGRAMMING = "Uploading Code to Arduino"
STATE_READY = "Ready"
STATE_FAILED = "Failed"

class Mbed1Experiment(Experiment.Experiment):
    def __init__(self, coord_address, locator, cfg_manager, *args, **kwargs):
        super(Mbed1Experiment, self).__init__(*args, **kwargs)
        self.cfg_manager = cfg_manager
        self.verbose           = cfg_manager.get_value('arduino_verbose', True)
        self.server_identifier = cfg_manager.get_doc_value(configuration_doc.CORE_UNIVERSAL_IDENTIFIER_HUMAN)
        self._current_state = STATE_BUSY
        self.arduino_port       = cfg_manager.get_value("Arduino_Port", "/dev/usb0")
        self.arduinobaseboard_port = cfg_manager.get_value("ArduinoBaseBoard_Port", "/dev/usb1")
        self.ArduinoCodeDir   = self.cfg_manager.get_value("ArduinoCodeDir", "ExperimentData/Arduino/Set01")
        self._ArduinoProgrammer    = ArduinoProgrammer(cfg_manager)
        self._ArduinoBaseBoard     = ArduinoBaseBoard(cfg_manager)
        self.ArduinoStreamUrl = self.cfg_manager.get_value("ArduinoStreamUrl", "/weblab/arduino/arduino1/video.mjpeg")
        if self.verbose:
            print ("arduino_port - %s | ArduinoCodeDir -%s | arduinobaseboard_port %s"%(self.arduino_port,self.ArduinoCodeDir,self.arduinobaseboard_port) )
            
            
    @Override(Experiment.Experiment)
    def do_get_api(self):
        return "1"

    @Override(Experiment.Experiment)
    def do_start_experiment(self, *args, **kwargs):
        print "Experiment started"
        if not (self._ArduinoProgrammer.checkdevice()):
            retstring =  "failed to load Experiment >> Arduino not found on port " , self.arduino_port
        if not (self._ArduinoBaseBoard.checkdevice()):
            retstring = "failed to load Experiment >> Base Board not found on port " , self.arduinobaseboard_port
        
        if (self._ArduinoBaseBoard.sendcommand("G+START+BO")):
            retstring = "Starting Arduino"
        else: 
            retstring = "Error in Starting Arduino" 
            self._current_state = STATE_FAILED
            
        if self.verbose:
            print "Arduino 1 Experiment started + " , retstring 

    @Override(Experiment.Experiment)
    def do_send_command_to_device(self, command):
        if self.verbose:
            print "- - - - - - - - - - - - - - - - - %s- - - - - - - - - - - - - - - - - - "%command

        if command == 'server_info':
            return self.server_identifier
        
        init_dir = os.getcwd()
        
        
        dev = "/dev/ttyUSB0" 
        try:
            #- - - - - - - - - - - - - - - - Build Command - - - - - - - - - - - - - - - - -
            if (command == 'build'):
                if (self._ArduinoProgrammer.build()):
                    retstring = "Build Successful"
                else:
                    retstring = "build Error"  
                    self._current_state = "Build Failed"
            #- - - - - - - - - - - - - - - - Upload2Board Command - - - - - - - - - - - - - - - - -
            elif (command == 'upload2board'):
                if (self._ArduinoProgrammer.upload()):
                    retstring = "Upload Successful"
                else:
                    retstring = "Upload Error"  
                    self._current_state = "Code Upload Failed"  
            #- - - - - - - - - - - - - - - - RestOP Command - - - - - - - - - - - - - - - - -
            elif (command == 'ResetOP'):
                if (self._ArduinoBaseBoard.sendcommand("G+RESET+OP")):
                    retstring = "Outpur Devices Reset"
                else: 
                    retstring = "Error in Outpur Devices Reset" 
                    self._current_state = STATE_FAILED                
            #- - - - - - - - - - - - - - - - Reset Board Command - - - - - - - - - - - - - - - - -
            elif (command == 'ResetBoard'):
                if (self._ArduinoBaseBoard.sendcommand("G+RESET+BO")):
                    retstring = "Arduino Board Reset"
                else: 
                    retstring = "Error in Arduino Board Reset" 
                    self._current_state = STATE_FAILED
            #- - - - - - - - - - - - - - - - Switch and Pulse Switch Command - - - - - - - - - - - - - - - - -
            elif 'Change' in command:
                print "Sending Now"
                swtype = re.search("Change(.+?) (.+?) (.+?)", command).group(1)
                status = re.search("Change(.+?) (.+?) (.+?)", command).group(2)
                butNo =  re.search("Change(.+?) (.+?) (.+?)", command).group(3)
                print "swtype ", swtype ," | Status ", status ," | butNo " , butNo
                cmd2send = "G+I+"+('SW' if swtype == 'Switch' else 'PSW') + butNo + "+" + ('1' if status == 'on' else '0');
                print "Sent Command ", cmd2send
                if (self._ArduinoBaseBoard.sendcommand(cmd2send)):
                    retstring = ("%s%d turned %s"%(swtype,butNo,status))
                else: 
                    retstring = "Error in Sending Command to Board"
                    self._current_state = STATE_FAILED
            #- - - - - - - - - - - - - - - - Device Selection Command - - - - - - - - - - - - - - - - -       
            elif 'Select' in command:
                print "Sending Now"
                selectdev = re.search("Select(.+?$)", command).group(1)
                print "Device ", selectdev
                cmd2send = "G+O+" + selectdev + "+1";
                print "Sent Command ", cmd2send
                if (self._ArduinoBaseBoard.sendcommand(cmd2send)):
                    retstring = ("Selecting output device %s"%(selectdev))
                else: 
                    retstring = "Error in selecting Output Device"
                    self._current_state = STATE_FAILED
            #- - - - - - - - - - - - - - - - Device Selection Command - - - - - - - - - - - - - - - - -       
            elif 'WEBCAMURL' in command:
                print "Returning WEBCAMURL -" , self.ArduinoStreamUrl
                return "Returning WEBCAMURL -" , self.ArduinoStreamUrl            
                     
            #- - - - - - - - - - - - - - - - Status reporting Command - - - - - - - - - - - - - - - - -
            elif (command == 'STAT'):
                retstring =  self._current_state
            else: 
                retstring = "Command Not Fount"
            
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
        if (self._ArduinoBaseBoard.sendcommand("G+RESET+OP")):
            retstring = "Outpur Devices Reset"
        else: 
            retstring = "Error in Outpur Devices Reset" 
            self._current_state = STATE_FAILED
            
        if (self._ArduinoBaseBoard.sendcommand("G+STOP+BO")):
            retstring = "Stopping Arduino"
        else: 
            retstring = "Error in Stoping Arduino" 
            self._current_state = STATE_FAILED
        if self.verbose:
            print "dispose"


