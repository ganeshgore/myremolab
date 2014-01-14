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
    
from programmers import GeneralBaseBoard

from voodoo.override import Override
import time
import os
import subprocess
import serial
import re
import glob

STATE_BUSY = "Not_ready"
STATE_PROGRAMMING = "Uploading Code to fpga"
STATE_READY = "Ready"
STATE_FAILED = "Failed"

class Fpga1Experiment(Experiment.Experiment):
    def __init__(self, coord_address, locator, cfg_manager, *args, **kwargs):
        super(Fpga1Experiment, self).__init__(*args, **kwargs)
        self.cfg_manager            = cfg_manager
        self.verbose                = cfg_manager.get_value('fpga_verbose', True)
        self.server_identifier      = cfg_manager.get_doc_value(configuration_doc.CORE_UNIVERSAL_IDENTIFIER_HUMAN)
        self._current_state         = STATE_BUSY
        self.fpga_serialno          = cfg_manager.get_value("fpga_serialno", "210155443949")
        self.fpgabaseboard_port     = cfg_manager.get_value("fpgaBaseBoard_Port", "/dev/usb0")
        self.fpgaCodeDir            = self.cfg_manager.get_value("fpgaCodeDir", "ExperimentData/fpga/Set01")
        self.fpgaStreamUrl          = self.cfg_manager.get_value("fpgaStreamUrl", "/weblab/fpga/fpga1/video.mjpeg")
		self.FpgaBaseBoard     		= GeneralBaseBoard(self.fpgabaseboard_port)
        if self.verbose:
            print ("fpga_serialno - %s | fpgaCodeDir -%s | fpgabaseboard_port %s"%(self.fpga_serialno,self.fpgaCodeDir,self.fpgabaseboard_port) )
            
            
    @Override(Experiment.Experiment)
    def do_get_api(self):
        return "1"

    @Override(Experiment.Experiment)
    def do_start_experiment(self, *args, **kwargs):
        print "Experiment started"
        if (self._fpgaBaseBoard.sendcommand("G+START+BO")):
            retstring = "Starting fpga"
        else: 
            retstring = "Error in Starting fpga" 
            self._current_state = STATE_FAILED
            
        if self.verbose:
            print "fpga 1 Experiment started + " , retstring 

    @Override(Experiment.Experiment)
    def do_send_command_to_device(self, command):
        if self.verbose:
            print "- - - - - - - - - - - - - - - - - %s- - - - - - - - - - - - - - - - - - "%command

        if command == 'server_info':
            return self.server_identifier
        
        init_dir = os.getcwd() 
        try:
            #- - - - - - - - - - - - - - - - Upload2Board Command - - - - - - - - - - - - - - - - -
            if (command == 'upload2board'):
                if (self._fpgaProgrammer.upload()):
                    retstring = "Upload Successful"
                else:
                    retstring = "Upload Error"  
                    self._current_state = "Code Upload Failed"  
            #- - - - - - - - - - - - - - - - Switch and Pulse Switch Command - - - - - - - - - - - - - - - - -
            elif 'Change' in command:
                print "Sending Now"
                swtype = re.search("Change(.+?) (.+?) (.+?)", command).group(1)
                status = re.search("Change(.+?) (.+?) (.+?)", command).group(2)
                butNo =  re.search("Change(.+?) (.+?) (.+?)", command).group(3)
                print "swtype ", swtype ," | Status ", status ," | butNo " , butNo
                cmd2send = "G+I+"+('SW' if swtype == 'Switch' else 'PSW') + butNo + "+" + ('1' if status == 'on' else '0');
                print "Sent Command ", cmd2send
                if (self._fpgaBaseBoard.sendcommand(cmd2send)):
                    retstring = ("%s%d turned %s"%(swtype,butNo,status))
                else: 
                    retstring = "Error in Sending Command to Board"
                    self._current_state = STATE_FAILED
            #- - - - - - - - - - - - - - - - Device Selection Command - - - - - - - - - - - - - - - - -       
            elif 'WEBCAMURL' in command:
                print "Returning WEBCAMURL -" , self.fpgaStreamUrl
                return "Returning WEBCAMURL -" , self.fpgaStreamUrl            
                     
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
        os.chdir(self.fpgaCodeDir)
        print "Saving bit file in " , str(os.getcwd())
        myFile = open('text.bit', 'w')
        myFile.write(content.decode(encoding='base64',errors='strict'))
        myFile.close()
        os.chdir(init_dir)
        return "Received file with len: %s and file_info: %s" % (len(content), file_info)

    @Override(Experiment.Experiment)
    def do_dispose(self):
        if (self._fpgaBaseBoard.sendcommand("G+RESET+OP")):
            retstring = "Outpur Devices Reset"
        else: 
            retstring = "Error in Outpur Devices Reset" 
            self._current_state = STATE_FAILED
            
        if (self._fpgaBaseBoard.sendcommand("G+STOP+BO")):
            retstring = "Stopping fpga"
        else: 
            retstring = "Error in Stoping fpga" 
            self._current_state = STATE_FAILED
        if self.verbose:
            print "dispose"


