/**
 * 
 */
package es.deusto.weblab.client.ui.widgets;

import java.util.Iterator;
import java.util.List;
import java.util.Vector;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Widget;



/**
 * @author ganesh
 *
 */
public class WlKeypad extends Composite {

	private static TwoButtUiBinder uiBinder = GWT.create(TwoButtUiBinder.class);
	
	private IWlKeyPadUsed buttonUsed = null;
	
	public String key = null;
	public static final int    DEFAULT_TIME = 1000; //milliseconds
	
	@UiField VerticalPanel mykeypad;
	
	private final List<UtilTimer> currentTimers = new Vector<UtilTimer>();
	private int time;
	
	interface TwoButtUiBinder extends UiBinder<Widget, WlKeypad> {
	}

	/**
	 * Because this class has a default constructor, it can
	 * be used as a binder template. In other words, it can be used in other
	 * *.ui.xml files as follows:
	 * <ui:UiBinder xmlns:ui="urn:ui:com.google.gwt.uibinder"
	 *   xmlns:g="urn:import:**user's package**">
	 *  <g:**UserClassName**>Hello!</g:**UserClassName>
	 * </ui:UiBinder>
	 * Note that depending on the widget that is used, it may be necessary to
	 * implement HasHTML instead of HasText.
	 */
	public WlKeypad() {
		initWidget(uiBinder.createAndBindUi(this));
		prepareKeypad();
		this.time = WlKeypad.DEFAULT_TIME;
	}
	
	private void prepareKeypad(){	
		
		for(int j=0; j<this.mykeypad.getWidgetCount(); j++){
			final HorizontalPanel MyHor = (HorizontalPanel) this.mykeypad.getWidget(j);
			for(int i=0; i<MyHor.getWidgetCount(); i++){
				final Button butt = (Button) MyHor.getWidget(i);
					butt.addClickHandler(new ClickHandler(){					
					
					@Override
					public void onClick(ClickEvent event) {
						// TODO Auto-generated method stub
						//Window.alert("Hello! Running From Widget Code for" + butt.getTitle());
						WlKeypad.this.key = butt.getTitle();
						WlKeypad.this.buttonPressed();
						//buttonUsed.onPressed();
						//this.boardController.sendCommand("keypad", this.getResponseCommandCallback());				
						}
			
		});
	}
	}
	
	}
	
	protected void buttonPressed(){
		WlKeypad.this.buttonUsed.onPressed();
		
		final UtilTimer timer = new UtilTimer(){
			@Override
			public void realRun(){
				if(WlKeypad.this.buttonUsed != null) {
					WlKeypad.this.buttonUsed.onReleased();
					//AudioManager.getInstance().playBest("snd/button");
				}
			}
		};
		timer.schedule(this.time);
		this.addTimer(timer);
	}
	
	public interface IWlKeyPadUsed{
		public void onPressed();
		public void onReleased();
	}
	

	public WlKeypad(String firstName) {
		initWidget(uiBinder.createAndBindUi(this));
		// Can access @UiField after calling createAndBindUi
	}


	public void setText(String text) {
		//keypadlb.setText(text);
	}
	
	//Creates method in widget to link
	public void addButtonListener(IWlKeyPadUsed buttonUsed){
		this.buttonUsed = buttonUsed;
	}

	/**
	 * Gets invoked when the default constructor is called
	 * and a string is provided in the ui.xml file.
	 */
	public String getText() {
		//return keypadlb.getText();
		return "keypad";
	}
	
	private void addTimer(UtilTimer timer){
		this.cleanOldTimers();
		this.currentTimers.add(timer);
	}
	
	private void cleanOldTimers(){
		final Iterator<UtilTimer> it = this.currentTimers.iterator();
		while(it.hasNext()){
			final UtilTimer t = it.next();
			if(t.hasBeenRun())
				it.remove();
		}
	}
	
	private void cancelTimers(){
		final Iterator<UtilTimer> it = this.currentTimers.iterator();
		while(it.hasNext()){
			final UtilTimer t = it.next();
			t.cancel();
		}
		this.currentTimers.clear();
	}
	
	/*
	 * The Timer class provided by GWT does not tell us whether
	 * the method has been already called or not.
	 */
	private abstract class UtilTimer extends Timer{
		
		private boolean bhasBeenRun = false;
		
		public abstract void realRun();
		
		@Override
		public void run(){
			this.bhasBeenRun = true;
			this.realRun();
		}
		
		public boolean hasBeenRun(){
			return this.bhasBeenRun;
		}
	}


}
