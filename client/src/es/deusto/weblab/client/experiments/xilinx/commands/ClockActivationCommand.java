/*
* Copyright (C) 2005 onwards University of Deusto
* All rights reserved.
*
* This software is licensed as described in the file COPYING, which
* you should have received as part of this distribution.
*
* This software consists of contributions made by many individuals, 
* listed below:
*
* Author: Pablo Orduña <pablo@ordunya.com>
*
*/ 
package es.deusto.weblab.client.experiments.xilinx.commands;

import es.deusto.weblab.client.dto.experiments.Command;

public class ClockActivationCommand extends Command{
	
	private final int n;
	
	public ClockActivationCommand(int n){
		this.n = n;
	}
	
	@Override
	public String getCommandString() {
		return "ClockActivation on " + this.n;
	}
}
