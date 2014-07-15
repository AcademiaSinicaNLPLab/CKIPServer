#!/usr/bin/python

import sys, json, re, os
import ConfigParser

def getInt(variable, data):
    return int(data)

def getSize(variable, data):
    m=re.match('([0-9]+) *([mMkK]?)$', data)
    if m:
	if len(m.group(2))==0:
	    return int(data)
	elif m.group(2) in "kK":
	    return int(m.group(1))*1024
	elif m.group(2) in "mM":
	    return int(m.group(1))*1024*1024

    print "ERROR: unknown value '%s' for variable '%s'"%(data, variable)
    sys.exit(1)

def getString(variable, data):
    return data

def getExistFile(variable, data):
    if os.path.isfile(data):
	return data
    print "ERROR: file '%s' is not exist for variable '%s'."%(data, variable)
    sys.exit(1)

def getExistDir(variable, data):
    if os.path.isdir(data):
	return data
    print "ERROR: file '%s' is not exist for variable '%s'."%(data, variable)
    sys.exit(1)

def getFile(variable, data):
    return data
    

class ServerConfig:
    system_vars={
        "port":			(1501,   getInt),
	"ini":			("",     getExistFile),
	"max_children": 	(4, 	 getInt),
	"max_file_size": 	(10*2**20,  getSize),
	"password": 		("",     getExistFile),
	"user": 		("root", getString),
	"group": 		("root", getString),
	"log_file": 		("",     getFile),
	"log_level": 		("INFO", getString),
	"log_format": 		("", getString),
	"pid_file": 		("",     getFile),
	"data_pool": 		("",     getExistDir),
	"timeout": 		(120,    getInt)
	}
    def __init__(self, config, section):
	self.section=section
	for (option, value) in ServerConfig.system_vars.items():
	    if config.has_option(section, option):
		string=config.get(section, option)
		self.__dict__[option]=value[1](option, string)
	    else:
		self.__dict__[option]=value[0]

    def __str__(self):
	return json.dumps(self.__dict__, ensure_ascii=False, indent=4)
  
def ParseConfig(config_file):
    config=ConfigParser.RawConfigParser()
    config.read([config_file])
    servers=[]
    for section in config.sections():
	obj=ServerConfig(config, section)
	servers.append(obj)
    return servers

if __name__=="__main__":
    L=ParseConfig(sys.argv[1])
    for server in L:
	print server
