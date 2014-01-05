package es.deusto.weblab.client.experiments.dummy.ui;

import java.util.Vector;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.uibinder.client.UiHandler;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Widget;

import es.deusto.weblab.client.comm.exceptions.CommException;
import es.deusto.weblab.client.configuration.IConfigurationRetriever;
import es.deusto.weblab.client.dto.experiments.ResponseCommand;
import es.deusto.weblab.client.lab.comm.UploadStructure;
import es.deusto.weblab.client.lab.comm.callbacks.IResponseCommandCallback;
import es.deusto.weblab.client.lab.experiments.ExperimentBase;
import es.deusto.weblab.client.lab.experiments.IBoardBaseController;
import es.deusto.weblab.client.lab.experiments.commands.RequestWebcamCommand;
import es.deusto.weblab.client.ui.widgets.IWlActionListener;
import es.deusto.weblab.client.ui.widgets.WlButton.IWlButtonUsed;
import es.deusto.weblab.client.ui.widgets.WlClockActivator;
import es.deusto.weblab.client.ui.widgets.WlSwitch;
import es.deusto.weblab.client.ui.widgets.WlTimedButton;
import es.deusto.weblab.client.ui.widgets.WlTimer;
import es.deusto.weblab.client.ui.widgets.WlTimer.IWlTimerFinishedCallback;
import es.deusto.weblab.client.ui.widgets.WlWaitingLabel;
import es.deusto.weblab.client.ui.widgets.WlWebcam;

import com.google.gwt.user.client.ui.Button;

public class XilinxExperiment extends ExperimentBase{

	
	 /*********************************************************************************************************
	 * UIBINDER RELATED
	 ******************/
	
	interface WlDeustoXilinxBasedBoardUiBinder extends UiBinder<Widget, XilinxExperiment> {
	}

	private static final WlDeustoXilinxBasedBoardUiBinder uiBinder = GWT.create(WlDeustoXilinxBasedBoardUiBinder.class);
	
	private static final String XILINX_DEMO_PROPERTY                  = "is.demo";
	private static final boolean DEFAULT_XILINX_DEMO                  = false;
	
	private static final String XILINX_MULTIRESOURCE_DEMO_PROPERTY   = "is.multiresource.demo";
	private static final boolean DEFAULT_MULTIRESOURCE_XILINX_DEMO   = false;
	
	private static final String XILINX_WEBCAM_IMAGE_URL_PROPERTY      = "webcam.image.url";
	private static final String DEFAULT_XILINX_WEBCAM_IMAGE_URL       = GWT.getModuleBaseURL() + "/img/arduino/webcam.jpg";
	
	private static final String XILINX_WEBCAM_REFRESH_TIME_PROPERTY   = "webcam.refresh.millis";
	private static final int    DEFAULT_XILINX_WEBCAM_REFRESH_TIME    = 400;
	
	public static class Style{
		public static final String TIME_REMAINING         = "wl-time_remaining";
		public static final String CLOCK_ACTIVATION_PANEL = "wl-clock_activation_panel"; 
	}
	
	private static final boolean DEBUG_ENABLED = false;
	
	@UiField public VerticalPanel verticalPanel;
	@UiField VerticalPanel widget;
	@UiField VerticalPanel innerVerticalPanel;
	@UiField HorizontalPanel uploadStructurePanel;
	
	@UiField Label selectProgram;
	
	@UiField HorizontalPanel timerMessagesPanel;
	@UiField WlWaitingLabel messages;

	@UiField HorizontalPanel webcamPanel;
	
	//@UiField(provided=true)
	private UploadStructure uploadStructure;
	
	private WlWebcam webcam;
	
	@UiField(provided = true)
	WlTimer timer;
	@UiField HorizontalPanel controlButtons;
	@UiField HorizontalPanel fileupload;
	
	@UiField HorizontalPanel PushSwRow;
	@UiField HorizontalPanel PulseSwRow;
	
	@UiField Button BuilldButton;
	@UiField Button upload2boardButton;
	@UiField Button uploadFile;
	@UiField TextBox LogWindow;
	@UiField Label UploadStat;
	@UiField VerticalPanel inputchekbx;
	@UiField VerticalPanel outputchekbx;
	
	@UiField Image outputDeviceImage;
	@UiField WlSwitch sw1;
	@UiField WlSwitch sw2;
	@UiField WlSwitch sw3;
	@UiField WlSwitch sw4;
	@UiField WlTimedButton psw1;
	@UiField WlTimedButton psw2;
	@UiField WlTimedButton psw3;
	@UiField WlTimedButton psw4;
	@UiField Button ResetArduino;
	
	
	private static Vector<CheckBox> inputChkBoxVec;
	private static Vector<CheckBox> outputChkBoxVec;

	
	
	//************************************Main Code Starts*************************************************
	
	public XilinxExperiment(IConfigurationRetriever configurationRetriever, IBoardBaseController boardController){
		super(configurationRetriever, boardController);
		
		this.inputChkBoxVec = new Vector<CheckBox>();
		this.outputChkBoxVec = new Vector<CheckBox>();
		
		this.createProvidedWidgets();
		
		XilinxExperiment.uiBinder.createAndBindUi(this);
		
		this.webcamPanel.add(this.webcam.getWidget());
				
		this.disableInteractiveWidgets();
		
		prepareSwitchesRow();
		prepareButtonsRow();
		
	}
	
	//*********************************** Add handlers to buttons **********************************************
	
	@UiHandler("uploadFile")
	void uploadFileClick(ClickEvent e) {
		//this.uploadStructure.getFormPanel().setVisible(false);
		this.boardController.sendFile(this.uploadStructure, this.sendFileCallback);
	}
	
	@UiHandler("BuilldButton")
	void BuilldClick(ClickEvent e) {
		this.boardController.sendCommand("build", this.getResponseCommandCallback());
	}
	
	@UiHandler("upload2boardButton")
	void upload2boardClick(ClickEvent e) {
		this.boardController.sendCommand("upload2board", this.getResponseCommandCallback());
	}
	
	@UiHandler("ResetArduino")
	void ArduinoResetClick(ClickEvent e) {
		this.boardController.sendCommand("ResetBoard", this.getResponseCommandCallback());
	}
	
	//rude way to apply handlers to button please revisit
		
	private void prepareSwitchesRow() {
		
		for(int i = 0; i < this.PushSwRow.getWidgetCount(); ++i){
			final Widget wid = this.PushSwRow.getWidget(i);
			if(wid instanceof WlSwitch) {
				final WlSwitch swi = (WlSwitch)wid;
				// Avoid trying to convert non-numerical titles (which serve
				// as identifiers). Not exactly an elegant way to do it.
				if(swi.getTitle().length() != 1) 
					continue;
				
				final int id = this.PushSwRow.getWidgetCount() - Integer.parseInt(swi.getTitle()) - 1;
				final IWlActionListener actionListener = new SwitchListener(id+2, this.boardController, this.getResponseCommandCallback());
				swi.addActionListener(actionListener);
			}
		}
	}

	private void prepareButtonsRow() {

		for(int i = 0; i < this.PulseSwRow.getWidgetCount(); ++i) {
			final Widget wid = this.PulseSwRow.getWidget(i);
			if(wid instanceof WlTimedButton) {
				final WlTimedButton timedButton = (WlTimedButton)wid;
				
				if(timedButton.getTitle().length() != 1)
					continue;
				
				final int id = Integer.parseInt(timedButton.getTitle());
				final IWlButtonUsed buttonUsed = 
					new ButtonListener(id, this.boardController, this.getResponseCommandCallback());
				timedButton.addButtonListener(buttonUsed);
			}
		}
	}
	
	
	/******************************************************************************
	 * Creates those widgets that are specified in the UiBinder xml
	 * file but which are marked as provided because they can't be
	 * allocated using the default Vector.
	 */
	private void createProvidedWidgets() {
		this.webcam = new WlWebcam(
				this.getWebcamRefreshingTime(),
				this.getWebcamImageUrl()
			);
		
		this.timer = new WlTimer(false);
		
		this.timer.setTimerFinishedCallback(new IWlTimerFinishedCallback(){
			@Override
			public void onFinished() {
				XilinxExperiment.this.boardController.clean();
			}
		});
		
		this.uploadStructure = new UploadStructure();
		this.uploadStructure.setFileInfo("program");
	}
	
	//* * * * * * *  * * * Initialization of Experiment and widgets * * * * * 
	
	@Override
	public void initialize(){
		
		// Doesn't seem to work from UiBinder.
		//Adds Upload widget on experiment window 
		this.fileupload.add(this.uploadStructure.getFormPanel());
			
		XilinxExperiment.this.UploadStat.setText("Verbose");
		this.webcam.setVisible(false);
		
		
		// Component Selection add handlers   (INPUT CHECKBOX)
		for(int i = 0; i < this.inputchekbx.getWidgetCount(); ++i){
			final CheckBox chk = (CheckBox) this.inputchekbx.getWidget(i);
			XilinxExperiment.inputChkBoxVec.add(chk);
			chk.addClickHandler(new ClickHandler() {
			      @Override
				public void onClick(ClickEvent event) {
			    	  this.inputcompselectionevalutor(chk.getName(),chk.getValue());
			      }

			      private void inputcompselectionevalutor(String name, Boolean value) {
			    	  if (name.equals("44mat")){
			    		  XilinxExperiment.ChangeWidgetStat(XilinxExperiment.outputChkBoxVec,"charlcd",!value);
			    		  XilinxExperiment.ChangeWidgetStat(XilinxExperiment.outputChkBoxVec,"7seg",!value);
			    	  }
			    	  else if (name.equals("4pushsw")){
			    		  XilinxExperiment.ChangeWidgetStat(XilinxExperiment.inputChkBoxVec,"4pulsesw",!value);
			    		  XilinxExperiment.ChangeWidgetStat(XilinxExperiment.outputChkBoxVec,"4led",!value);
			    	  }
			    	  else if (name.equals("4pulsesw")){
			    		  XilinxExperiment.ChangeWidgetStat(XilinxExperiment.inputChkBoxVec,"4pushsw",!value);
			    		  XilinxExperiment.ChangeWidgetStat(XilinxExperiment.outputChkBoxVec,"4led",!value);
			    	  }
			    	  else {
			    		  System.out.println("Error : Wrong response from input checkbox selection received " + name);
			    	  }
		
			      }
			 
			    });
		}
		
	// Component Selection add handlers   (OUTPUT CHECKBOX)
		
		for(int i = 0; i < this.outputchekbx.getWidgetCount(); ++i){
			final CheckBox chk = (CheckBox) this.outputchekbx.getWidget(i);
			XilinxExperiment.outputChkBoxVec.add(chk);
			chk.addClickHandler(new ClickHandler() {
			      @Override
				public void onClick(ClickEvent event) {
			    	  this.outputcompselectionevalutor(chk.getName(),chk.getValue());
			      	}

			      	private void outputcompselectionevalutor(String name, Boolean value) {
			      		if (name.equals("4led")){
				    		  XilinxExperiment.ChangeWidgetStat(XilinxExperiment.inputChkBoxVec,"4pulsesw",!value);
				    		  XilinxExperiment.ChangeWidgetStat(XilinxExperiment.inputChkBoxVec,"4pushsw",!value);
				    	  }
				    	  else if (name.equals("7seg")){
				    		  XilinxExperiment.ChangeWidgetStat(XilinxExperiment.inputChkBoxVec,"44mat",!value);
				    		  XilinxExperiment.ChangeWidgetStat(XilinxExperiment.outputChkBoxVec,"charlcd",!value);
				    	  }
				    	  else if (name.equals("charlcd")){
				    		  XilinxExperiment.ChangeWidgetStat(XilinxExperiment.inputChkBoxVec,"44mat",!value);
				    		  XilinxExperiment.ChangeWidgetStat(XilinxExperiment.outputChkBoxVec,"7seg",!value);
				    	  }
				    	  else {
				    		  System.out.println("Error : Wrong response from output checkbox selection received " + name);
				    	  }			  		
			  		}				
			    });
		}
		
	//final IWlActionListener actionListener = new SwitchListener(1, this.boardController, this.getResponseCommandCallback());
	//this.sw1.addActionListener(actionListener);
	}
	

	
	///* * * * * * * * * *  Routine to modify widgets from array * * * * * * * * * *
	private static void ChangeWidgetStat(Vector<CheckBox> outputChkBoxVec,
			String string, boolean value) {
		for(int i=0;i<outputChkBoxVec.size();i++){
			if(outputChkBoxVec.get(i).getName().equals(string)){
				outputChkBoxVec.get(i).setEnabled(value);
			}						
		}					
	}
	
	private Integer getIndexWithName(Vector<CheckBox> outputChkBoxVec,
			String string) {
		for(int i=0;i<outputChkBoxVec.size();i++){
			if(outputChkBoxVec.get(i).getName().equals(string)){
				return i;
			}
		}	
		return -1;
	}
	
	//* * * * * * * * * * * * * * Runs While waiting in queue * * * * * * * *
	@Override
	public void queued(){
	    this.widget.setVisible(false);
	    this.selectProgram.setVisible(false);
	}

	
	
	//* * * * * * * * * * * * * * Runs After Reservation of Experiment * * * * * * * *
	@Override
	public void start(int time, String initialConfiguration){
		
		System.out.println("-----> Starting Experiments");
		
		RequestWebcamCommand.createAndSend(this.boardController, this.webcam, 
				this.messages);
		
	    this.widget.setVisible(true);
	    this.selectProgram.setVisible(false);
	    
		this.loadWidgets();
		this.disableInteractiveWidgets();
		
		XilinxExperiment.this.enableInteractiveWidgets();
		XilinxExperiment.this.messages.setText("Device ready");
		XilinxExperiment.this.messages.stop();
			
		this.uploadStructurePanel.setVisible(false);
		
		
		
	}
	
	
	// **************************** File Sending handler Routine ****************** 
	final IResponseCommandCallback sendFileCallback = new IResponseCommandCallback() {
	    
	    @Override
	    public void onSuccess(ResponseCommand response) {
	    	//XilinxExperiment.this.uploadStructure.getFormPanel().setVisible(true);
	    	XilinxExperiment.this.UploadStat.setText("Ready");
	    }

	    @Override
	    public void onFailure(CommException e) {
	    	
	    	//XilinxExperiment.this.uploadStructure.getFormPanel().setVisible(true);
	    	XilinxExperiment.this.UploadStat.setText("Error");
			XilinxExperiment.this.LogWindow.setText("Error sending file: " + e.getMessage());
		    
	    }
	};	
	
	//***************************** Widgets Related ********************************
	
	private void loadWidgets() {
		
		this.webcam.setVisible(true);
		this.webcam.start();
		
		this.timer.start();
		
		this.messages.setText("Programming device");
		this.messages.start();
		
		this.innerVerticalPanel.setSpacing(20);
		
		// Set input Peripheral image
		if(inputChkBoxVec.get(this.getIndexWithName(inputChkBoxVec,"44mat")).getValue());
		else if(inputChkBoxVec.get(this.getIndexWithName(inputChkBoxVec,"4pushsw")).getValue())
			this.PushSwRow.setVisible(true);
		else if(inputChkBoxVec.get(this.getIndexWithName(inputChkBoxVec,"4pulsesw")).getValue())
			this.PulseSwRow.setVisible(true);
		else
			Window.alert("No Input device Selected");
		
		this.boardController.sendCommand("ResetOP", this.getResponseCommandCallback());
		// Set Output Peripheral image
		if(outputChkBoxVec.get(this.getIndexWithName(outputChkBoxVec,"4led")).getValue()){
			this.outputDeviceImage.setUrl("weblabclientlab/img/arduino/LED.jpg");
			this.boardController.sendCommand("SelectLED", this.getResponseCommandCallback());
		}
		else if(outputChkBoxVec.get(this.getIndexWithName(outputChkBoxVec,"7seg")).getValue()){
			this.outputDeviceImage.setUrl("weblabclientlab/img/arduino/7SEG.jpg");
			this.boardController.sendCommand("SelectSEG", this.getResponseCommandCallback());
		}
		else if(outputChkBoxVec.get(this.getIndexWithName(outputChkBoxVec,"charlcd")).getValue()){
			this.outputDeviceImage.setUrl("weblabclientlab/img/arduino/LCD.jpg");
			this.boardController.sendCommand("SelectLCD", this.getResponseCommandCallback());
		}
		else
			Window.alert("No Output device Selected");
	}
	

	
	private void enableInteractiveWidgets(){
		this.verticalPanel.setVisible(true);		
	}
	
	private void disableInteractiveWidgets(){
		this.verticalPanel.setVisible(false);
	}
	
	
	//********************* WebCam Related Routines *****************************
	@Override
	public void end(){
		if(this.webcam != null){
			this.webcam.dispose();
			this.webcam = null;
		}
		
		if(this.timer != null){
			this.timer.dispose();
			this.timer = null;
		}	
		
		this.messages.stop();
	}
	
	@Override
	public void setTime(int time) {
		this.timer.updateTime(time);
	}
	
	@Override
	public Widget getWidget() {
		return this.widget;
	}
	
	private String getWebcamImageUrl() {
		return this.configurationRetriever.getProperty(
				XilinxExperiment.XILINX_WEBCAM_IMAGE_URL_PROPERTY, 
				XilinxExperiment.DEFAULT_XILINX_WEBCAM_IMAGE_URL
			);
	}

	private int getWebcamRefreshingTime() {
		return this.configurationRetriever.getIntProperty(
				XilinxExperiment.XILINX_WEBCAM_REFRESH_TIME_PROPERTY, 
				XilinxExperiment.DEFAULT_XILINX_WEBCAM_REFRESH_TIME
			);
	}	
	
	
	
	//********************* After every command this routine runs to indicate success and failure of execution ***************
	
	protected IResponseCommandCallback getResponseCommandCallback(){
	    return new IResponseCommandCallback(){
		    @Override
			public void onSuccess(ResponseCommand responseCommand) {
	    		GWT.log("responseCommand: success", null);
		    }

		    @Override
			public void onFailure(CommException e) {
    			GWT.log("responseCommand: failure", null);
    			XilinxExperiment.this.messages.stop();
    			XilinxExperiment.this.messages.setText("Error sending command: " + e.getMessage());
		    }
		};	    
	}
}
