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
package es.deusto.weblab.client.ui.exceptions.themes;

public class ThemeNotFoundException extends ThemeException {
	private static final long serialVersionUID = -7575207146232442585L;

	public ThemeNotFoundException() {
	}

	public ThemeNotFoundException(String arg0) {
		super(arg0);
	}

	public ThemeNotFoundException(Throwable arg0) {
		super(arg0);
	}

	public ThemeNotFoundException(String arg0, Throwable arg1) {
		super(arg0, arg1);
	}

}
