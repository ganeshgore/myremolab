#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2009 University of Deusto
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# This software consists of contributions made by many individuals, 
# listed below:
#
# Author: Jaime Irurzun <jaime.irurzun@gmail.com>
# 

from abc import ABCMeta, abstractmethod
from voodoo.override import Override

import subprocess        
import serial
import os

class UdXilinxProgrammer(object):

    __metaclass__ = ABCMeta
    
    def __init__(self, cfg_manager):
        super(UdXilinxProgrammer, self).__init__()
        self._cfg_manager = cfg_manager

    @staticmethod
    def create(cfg_manager):
        return PICProgrammer(cfg_manager)
    
    @abstractmethod
    def program(self, file_name):
        pass


class PICProgrammer(UdXilinxProgrammer):
    
    def __init__(self, cfg_manager):
        super(PICProgrammer, self).__init__(cfg_manager)
    
    @Override(UdXilinxProgrammer)
    def program(self, file_name):
        proc = subprocess.Popen(["/opt/pk2cmd/pk2cmdv1-20Linux2-6/pk2cmd","-PPIC18F45K20","-F%s" % file_name,"-M","-R"], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        code = proc.wait()
        stdout = proc.stdout.read()
        stderr = proc.stderr.read()
        print stdout
        print stderr
        if code != 0:
            raise Exception("Error programming device: %s; %s" % (stdout, stderr))


class ArduinoProgrammer:    
    def __init__(self, cfg_manager):
        #super(ArduinoProgrammer, self).__init__()
        self._cfg_manager = cfg_manager
        self.ArduinoCodeDir   = self._cfg_manager.get_value("ArduinoCodeDir", "ExperimentData/Arduino/Set01")
        self.arduino_port = self._cfg_manager.get_value("Arduino_Port", "/dev/usb0")
        init_dir = os.getcwd()
        os.chdir(self.ArduinoCodeDir)
        f=open("ino.ini",'w')
        f.write("[build] \n\
                board-model = atmega8 \n\
                [upload] \n\
                board-model = atmega8 \n\
                serial-port = %s \n\
                [serial] \n\
                serial-port = %s" %(self.arduino_port,self.arduino_port) )
        f.close()
        print "File Writing Completed"
        os.chdir(init_dir)
        
    @abstractmethod
    def checkdevice(self):
        return 1
        
    @abstractmethod
    def build(self):
        init_dir = os.getcwd()
        os.chdir(self.ArduinoCodeDir)
        print "Trying to build arduino in path get CWD - ", os.getcwd()
        proc = subprocess.Popen(["ino","build"], stdout=subprocess.PIPE)
        for line in iter(proc.stdout.readline, b''):
            print ">>" , line 
        os.chdir(init_dir)   
    
    @abstractmethod
    def upload(self):
        init_dir = os.getcwd()
        self.ArduinoCodeDir   = self._cfg_manager.get_value("ArduinoCodeDir", "ExperimentData/Arduino/Set01")
        os.chdir(self.ArduinoCodeDir)
        proc = subprocess.Popen(["ino","upload"], stdout=subprocess.PIPE)
        for line in iter(proc.stdout.readline, b''):
            print ">>" , line 
        os.chdir(init_dir)          

class ArduinoBaseBoard:    
    def __init__(self, cfg_manager):
        #super(ArduinoBaseBoard, self).__init__()
        self._cfg_manager = cfg_manager
        self.arduinobaseboard_port   = self._cfg_manager.get_value("ArduinoBaseBoard_Port", "/dev/usb1")

    @abstractmethod
    def checkdevice(self):
        return 1  
        
    @abstractmethod
    def sendcommand(self, cmd2send):
        try:
            ser = serial.Serial(self.arduinobaseboard_port,9600,timeout=1)                
            ser.write(str(cmd2send) + chr(0x0D))
            reponse = ser.readline()
            if(reponse == '' ):
                print "Error No response from Device"
                status = False
            else:
                print reponse, " - Command Sent Successfully"
                status = True
            ser.close()
        except Exception as e: 
            print "Device Error " + str(e)
            status = False
        return status 
                

          
