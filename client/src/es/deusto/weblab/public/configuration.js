{
	// IMPORTANT
	//
	// Internet Explorer can't parse dictionaries as:
	//  {
	//        'foo' : 'bar',
	//  }
	// 
	// Due to the last ',' after 'bar'. Same for lists
	//   [
	//      1,
	//      2,
	//      //3
	//   ]
	// Would produce an error since there is a ',' and then a ']'.
	// 
	// "weblab.service.fileupload.post.url" : "/weblab/fileUpload.php", 
	"development"                    : true, // To see the latest features, although they might not be working
	"demo.available"                 : true,
	"sound.enabled"					 : false,
	"admin.email"                    : "contact@eduvance.in",
	"google.analytics.tracking.code" : "UA-12576838-6",
	"experiments.default_picture"	 : "/img/experiments/default.jpg",
	"host.entity.image.login"        : "/img/udeusto-logo.jpg",
	"host.entity.image"              : "/img/udeusto-logo-main.jpg",
	"host.entity.image.mobile"       : "/img/udeusto-logo-mobile.jpg",
	"host.entity.link"               : "http://www.eduvance.in/",
    "facebook.like.box.visible"      : false,
	"experiments" : { 
	                "dummy" : [
	                           {
	                        	   "experiment.name"     : "dummy",
	                        	   "experiment.category" : "Dummy experiments"
	                           }
	                       ],
	                "fpga" : [
	                           {
	                        	   "experiment.name"     : "fpga1",
	                        	   "experiment.category" : "fpga experiments"
	                           },
	                           {
	                        	   "experiment.name"     : "fpga2",
	                        	   "experiment.category" : "fpga experiments"
	                           },
	                           {
	                        	   "experiment.name"     : "fpga3",
	                        	   "experiment.category" : "fpga experiments"
	                           },
	                           {
	                        	   "experiment.name"     : "fpga4",
	                        	   "experiment.category" : "fpga experiments"
	                           },
	                           {
	                        	   "experiment.name"     : "fpga5",
	                        	   "experiment.category" : "fpga experiments"
	                           }
	                       ],
	                "mbed" : [
	                           {
	                        	   "experiment.name"     : "mbed1",
	                        	   "experiment.category" : "ARM experiments"
	                           },
	                           {
	                        	   "experiment.name"     : "mbed2",
	                        	   "experiment.category" : "ARM experiments"
	                           },
	                           {
	                        	   "experiment.name"     : "mbed3",
	                        	   "experiment.category" : "ARM experiments"
	                           },
	                           {
	                        	   "experiment.name"     : "mbed4",
	                        	   "experiment.category" : "ARM experiments"
	                           },
	                           {
	                        	   "experiment.name"     : "mbed5",
	                        	   "experiment.category" : "ARM experiments"
	                           }
	                       ],
	                "arduino" : [
	                           {
	                        	   "experiment.name"     : "arduino1",
	                        	   "experiment.category" : "Basic experiments"
	                           },
	                           {
	                        	   "experiment.name"     : "arduino2",
	                        	   "experiment.category" : "Basic experiments"
	                           },
	                           {
	                        	   "experiment.name"     : "arduino3",
	                        	   "experiment.category" : "Basic experiments"
	                           },
	                           {
	                        	   "experiment.name"     : "arduino4",
	                        	   "experiment.category" : "Basic experiments"
	                           },
	                           {
	                        	   "experiment.name"     : "arduino5",
	                        	   "experiment.category" : "Basic experiments"
	                           }
	                       ]
		}
}
