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
package es.deusto.weblab.client.experiments.mbed.ui;

import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Label;

import es.deusto.weblab.client.comm.exceptions.CommException;
import es.deusto.weblab.client.configuration.IConfigurationRetriever;
import es.deusto.weblab.client.dto.experiments.ResponseCommand;
import es.deusto.weblab.client.experiments.mbed.ui.BaseExperimentPanel;
import es.deusto.weblab.client.lab.comm.callbacks.IResponseCommandCallback;
import es.deusto.weblab.client.lab.experiments.IBoardBaseController;

public class MbedExperiment extends BaseExperimentPanel {

	public static final String DUMMY_WEBCAM_IMAGE_URL_PROPERTY = "es.deusto.weblab.arduino.webcam.image.url";
	public static final String DEFAULT_DUMMY_WEBCAM_IMAGE_URL       = "http://fpga.weblab.deusto.es/webcam/fpga0/image.jpg";
	
	public static final String DUMMY_WEBCAM_REFRESH_TIME_PROPERTY = "es.deusto.weblab.pld.webcam.refresh.millis";
	public static final int    DEFAULT_DUMMY_WEBCAM_REFRESH_TIME       = 400;
	
	private final Label arduinoMessages;
	
	public MbedExperiment(IConfigurationRetriever configurationRetriever,
			IBoardBaseController boardController) {
		super(configurationRetriever, boardController);
		this.arduinoMessages = new Label("messages here");
	}
	
	@Override
	public void start(int time, String initialConfiguration){
	    super.start(time, initialConfiguration);
	    System.out.println("initial configuration:" + initialConfiguration);
	    this.verticalPanel.add(this.arduinoMessages);
	}

	@Override
	protected IResponseCommandCallback getResponseCommandCallback(){
	    return new IResponseCommandCallback(){

			@Override
			public void onSuccess(ResponseCommand responseCommand) {
			    MbedExperiment.this.processCommandSent(responseCommand);
			}
		
			@Override
			public void onFailure(CommException e) {
				MbedExperiment.this.arduinoMessages.setText("Error raised: " + e.getMessage());
			}
	    };
	}
	
	private void processCommandSent(ResponseCommand responseCommand) {
		if(!responseCommand.isEmpty()){
			if (responseCommand.getCommandString().contains("WEBCAMURL")){				
				MbedExperiment.this.webcam.setUrl(responseCommand.getCommandString().split("'")[3]);	
			}
			else{
				this.arduinoMessages.setText("Response command: " + responseCommand.getCommandString());
				
			}
		}
		else
			this.arduinoMessages.setText("Response command: empty");
		
	}
}
