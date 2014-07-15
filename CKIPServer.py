#!/usr/bin/python
#-*- encoding: UTF-8 -*-


import SocketServer
import socket
import string
import time
import logging
import sys, os, getopt
import signal
import pwd, grp
from xml.sax import SAXParseException
from ctypes import *
from config import *

#sys.path.append(os.environ['HOME']+"/WordSeg")
sys.path.append('/tools/wordseg')

from daemon import Daemon
from PyWordSeg import *
from XMLParser import *
from Password import Password

options=None

levelmap={
        "DEBUG": 	logging.DEBUG,
	"INFO": 	logging.INFO,
	"WARNING": 	logging.WARNING,
	"ERROR":	logging.ERROR,
	"CRITICAL":	logging.CRITICAL,
}

outputTemplate="""\
<?xml version="1.0" encoding="UTF-8"?>
<wordsegmentation version="0.1">
%(PROCESSSTATUS)s
<result>
%(RESULT)s
</result>
</wordsegmentation>
"""

class WordSegXML(PyWordSeg, XMLParser):
    def __init__(self, inifile, passfile=None):
        PyWordSeg.__init__(self, inifile)
	XMLParser.__init__(self)
	if passfile:
	    self.password=Password(passfile)
	    self.auth=True
	else:
	    self.auth=False

    def authenticate(self):
        if self.auth==False:
	    return True
        info=self.getUserInfo()
	ret=self.password.check(info['username'], info['password'])
	return ret

    def ProcessXML(self, inbuf_xml):
        parse_ok=self.parseString(inbuf_xml)

	if not parse_ok:
	    return (2,'xml format error.')

	if self.authenticate()==False:
	    return (3,'user or password error.')

	textL=self.getText().strip("\r\n").split("\n")
	outL=self.ApplyList(textL)
	outXML=self.XMLStringListWrap(outL,"UTF-8")
	return (1, outXML)

class ServiceHandler(SocketServer.StreamRequestHandler):
    def timeout_handle(self, signum, frame):
        raise IOError, "client not responding"

    def generateXMLFileNames(self):
	sn=time.strftime("%Y/%m/%d")
	self.inputDir="%s/%s"%(self.server.dataPool,sn)
	self.xmlfile="%s/%s_%s_src.xml"%(
	    self.inputDir,
	    self.client_address[0],
	    self.client_address[1]
	)
	self.xmltagfile="%s/%s_%s_tag.xml"%(
	    self.inputDir,
	    self.client_address[0],
	    self.client_address[1]
	)
	self.xmluwefile="%s/%s_%s_uwe.xml"%(
	    self.inputDir,
	    self.client_address[0],
	    self.client_address[1]
	)

    def receiveInputFile(self):
	signal.signal(signal.SIGALRM, self.timeout_handle)
	signal.alarm(self.server.timeout)

	exceedFlag=False
	finished=False
	timeoutFlag=False

	self.receivedData=""
	try:
            while 1:
	        line = self.rfile.readline()
	        if not line:
	            finished=True
	            break

	        self.receivedData+=line
	        if "</wordsegmentation>" in line.lower():
	            finished=True
	            break
	        if len(self.receivedData) > self.server.max_file_size:
		    exceedFlag=True
		    break

	except IOError:
	    timeoutFlag=True

	if exceedFlag:
	    self.sendErrorMessage(2,"XML format error: exceed limited file size")
	    return 0

	elif timeoutFlag:
	    self.sendErrorMessage(2,"Connection timeout.")
	    return 0

	elif not finished: 
	    self.sendErrorMessage(2,"XML format error.")
	    return 0

	return len(self.receivedData)

    def sendErrorMessage(self, code, message):
        msg={
	    "RESULT":"",
	    "PROCESSSTATUS":'<processstatus code="%s">%s</processstatus>'%(
	                     code, message)
	}
	out=outputTemplate%(msg)
	out=re.sub('[\r\n]','',out)
	self.wfile.write(out)

    def sendProcessedData(self, processedData):
	length=len(processedData)
	data=re.sub('[\r\n]','',processedData)
	self.wfile.write(data)
	return length

    def handle(self):
	self.server.logger.info("connected from %s."%(self.client_address[0]))
	ret=self.receiveInputFile()
	if not ret:
	    return False

	self.server.logger.info("receive data:%s"%(ret))

	# 接下來由 XMLParser 接手，
	try:
	    self.server.logger.debug("processing ...")
            (ret, processedData)=self.server.wordseg.ProcessXML(self.receivedData)
	    self.server.logger.debug("finished.")
	except SAXParseException:
	    ret=2
	except IOError:
	    ret=4
	except:
	    ret=5


	if ret==1:
	    outsize=self.sendProcessedData(processedData)
	    self.server.logger.info("send data:%s"%(outsize))
	elif ret==2:
	    self.sendErrorMessage(2,"XML format error.")
	    self.server.logger.debug("XML format error."%())
	elif ret==3:
	    self.sendErrorMessage(3,"Authentication failed.")
	    self.server.logger.debug("Authentication failed.")
	elif ret==4:
	    self.sendErrorMessage(4,"Processing timeout.")
	    self.server.logger.debug("processing timeout.")
	else:
	    self.sendErrorMessage(5,"Service internal error.")
	    self.server.logger.debug("Service internal error.")

	self.server.logger.info("service finished.")

	return True


class CKIPServer(SocketServer.ForkingTCPServer):
    allow_reuse_address=True  # 讓 daemon 可以關閉後立即開啟
    max_children=4 	      # 允許斷詞程式同時執行的最大數目
        
    def __init__(self, handler_class=ServiceHandler):
        self.logger = logging.getLogger('daemon:')
	self.logger.info('Starting Ckipat Server')
	self.port=options.port
	self.max_children=options.max_children
	CKIPServer.max_children=self.max_children
	self.log_file=options.log_file
	self.log_level=options.log_level
	self.log_format=options.log_format
	self.max_file_size=options.max_file_size
	self.inifile=options.ini

	self.logger.info(str(options))
	server_address=("", self.port)

        # Create WordSegXML object
        self.wordseg=WordSegXML(self.inifile, options.password)


	SocketServer.ForkingTCPServer.__init__(self, 
	        server_address, handler_class)

	return


class MyDaemon(Daemon):
    def run(self):
        if options.log_file==None or options.log_file=="None":
            logging.basicConfig(
	        level=levelmap[options.log_level], 
                format=options.log_format
            )
        else:
            logging.basicConfig(
	        level=levelmap[options.log_level], 
	        filename=options.log_file,
                format=options.log_format
            )

        # Create the server and start serving
        serv = CKIPServer(ServiceHandler)
        serv.serve_forever()

def usage():
    print """

Usage: CKIPServer.py [OPTIONS] [start|stop|restart]
    -h 		: Print this help message.
    -c filename	: Set the config file.
    """


def main():
    global options
    config_file=""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:", [
	    "help", "config="
	])

    except getopt.GetoptError, err:
        print str(err)
	usage()
	sys.exit(2)

    for o, a in opts:
	if o == "-h":
	    usage()
	    sys.exit(1)

	elif o in ("-c", "--config"):
	    config_file = a

	else:
	    assert False, "unknown option %s" %(o)

    # check config file
    if not os.path.isfile(config_file):
        print "ERROR: Config file %s is not found!" %(config_file)
        usage()
        sys.exit(2)

    options=ParseConfig(config_file)[0]

    uid=pwd.getpwnam(options.user)
    gid=grp.getgrnam(options.group)
    daemon = MyDaemon(options.pid_file, uid=uid.pw_uid, gid=gid.gr_gid)

    if len(args) >0:
        if 'start'==args[0]:
            daemon.start()
        elif 'stop'== args[0]:
            daemon.stop()
        elif 'restart' == args[0]:
            daemon.restart()
        elif 'debug' == args[0]:
	    opt_debug=True
	    options.log_file=None
            daemon.debug()
        else:
            print "Unknown command"
	    sys.exit(2)
        sys.exit(0)
    else:
        print usage()
	sys.exit(2)

if __name__=="__main__":
    main()



