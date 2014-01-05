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

package es.deusto.weblab.client.lab.experiments;

import es.deusto.weblab.client.configuration.IConfigurationRetriever;
import es.deusto.weblab.client.lab.experiments.exceptions.ExperimentCreatorInstanciationException;


public interface IExperimentCreatorFactory {
	public String getCodeName();
	public ExperimentCreator createExperimentCreator(IConfigurationRetriever configurationRetriever) throws ExperimentCreatorInstanciationException;
}
