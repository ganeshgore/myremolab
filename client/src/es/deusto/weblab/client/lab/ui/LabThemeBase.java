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
package es.deusto.weblab.client.lab.ui;

import com.google.gwt.user.client.ui.Widget;


public abstract class LabThemeBase implements IUIManager{
	
	public abstract Widget getWidget();
	
	public void onLoaded(){
	}
}
