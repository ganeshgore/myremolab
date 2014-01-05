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

package es.deusto.weblab.client.dto.experiments;


/**
 * Response of a command, such as a send_command or send_file response.
 * Also used to contain the response of an asynchronously executed command.
 */
public class ResponseCommand extends Command {

	private final String commandString;
	
	public ResponseCommand(String commandString) {
		this.commandString = commandString;
	}

	@Override
	public String getCommandString() {
		return this.commandString;
	}

	public boolean isEmpty() {
		return false;
	}
}
