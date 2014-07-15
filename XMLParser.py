#!/usr/bin/python
#-*- encoding: UTF-8 -*-

from xml.sax.handler import ContentHandler
from xml.sax.xmlreader import InputSource
import lxml.sax
import xml.sax
import string
import sys
import re


def extractEncodingFromString(input):
    m=re.search("""encoding=['"] *([^'"]+) *['"]""",input)
    if m:
        encode=m.group(1)
    else:
        encode=None # default value
    return encode

def extractEncoding(file):
    f=open(file)
    line=f.readline()
    return extractEncodingFromString(line)
  
class SourceHandler(ContentHandler):
    def __init__(self, data):
	self.inText=False
	self.textL=[]
	self.data=data
	self.data.text=""
	self.data.options={}
	self.data.userinfo={}

    def startElementNS(self, name, qname, attrs):
	if qname=="text":
	    self.inText=True

	elif qname=="option":
	    for (n,k),v in attrs.items():
	        self.data.options[k.lower()]=v

	elif qname=="authentication":
	    for (n,k),v in attrs.items():
	        self.data.userinfo[k]=v

    def endElementNS(self, (ns_uri, local_name), qname):
	if qname=="text":
	    self.inText=False

    def characters(self, ch):
        if self.inText:
	    self.textL.append(ch)

    def endDocument(self):
        self.data.text=string.join(self.textL,"")

class generic:
    def __init__(self):
        pass

class XMLParser:
    def __init__(self):
	self.defaultEncoding="Big5"

    def setDefaultEncoding(self, encoding):
        self.defaultEncoding=encoding

    def parseString(self, text):
	self.data=generic()
	self.data.encoding=extractEncodingFromString(text)
	if self.data.encoding==None:
	    parser=lxml.etree.XMLParser(encoding=self.defaultEncoding)
	else:
	    parser=lxml.etree.XMLParser()

	try:
            self.tree=lxml.etree.fromstring(text, parser)
	except:
	    return False
	    
        self.handler=SourceHandler(self.data)
	lxml.sax.saxify(self.tree, self.handler)
	return True

    def parseFile(self, file):
	self.data=generic()
        self.data.encoding=extractEncoding(file)
	if self.data.encoding==None:
	    parser=lxml.etree.XMLParser(encoding=self.defaultEncoding)
	else:
	    parser=lxml.etree.XMLParser()

	try:
            self.tree=lxml.etree.parse(file, parser)
	except:
	    return False
	    
        self.handler=SourceHandler(self.data)
	lxml.sax.saxify(self.tree, self.handler)
	return True

    def getUserInfo(self):
	return self.data.userinfo

    def getEncoding(self):
	return self.data.encoding

    def getOptions(self):
        return self.data.options

    def getBooleanOption(self, key, default=False):
        value=self.data.options.get(key.lower(),None)
	if value==None:
	    return default

	elif value=="1": 
	    return True

	elif value.lower()=="true":
	    return True

	return False

    def getOption(self, key):
        return self.data.options.get(key.lower(), None)

    def getText(self):
        return self.data.text

    def XMLWrap(self, tagfile, encoding, xmlfile):
        outputXMLHead="""\
<?xml version="1.0" encoding="%s"?>
<wordsegmentation version="0.1">
<processstatus code="0">Success</processstatus>
<result>
"""
	outputXMLTail="""\
</result>
</wordsegmentation>
"""
	outf=open(xmlfile,"w")
        inf=open(tagfile)
	outf.write(outputXMLHead%(encoding))
	for line in inf:
	    line="    <sentence>%s</sentence>\n"%line.strip()
	    outf.write(line)
	outf.write(outputXMLTail)
	inf.close()
	outf.close()

    def XMLStringListWrap(self, List, encoding="UTF-8"):
        outputXMLHead=u"""\
<?xml version="1.0" encoding="%s"?>
<wordsegmentation version="0.1">
<processstatus code="0">Success</processstatus>
<result>
"""
	outputXMLTail=u"""\
</result>
</wordsegmentation>
"""
	outL=[]
	outL.append(outputXMLHead%(encoding))
	for line in List:
	    line=u"    <sentence>%s</sentence>\n"%line.strip()
	    outL.append(line)
	outL.append(outputXMLTail)
	return string.join(outL,"").encode(encoding)


        
if __name__=="__main__":
    a=XMLParser()
    a.parseFile(sys.argv[1])
    print "DEBUG: encoding=%s"%a.getEncoding()
    print "DEBUG: text=%s"%a.getText()
    print "DEBUG: options=%s"%a.getOptions()
    print "DEBUG: userinfo=%s"%a.getUserInfo()

    text="""\
<?xml version="1.0" encoding="UTF-8"?>
<wordsegmentation version="0.1">
<option showcategory="1" />
<authentication username="iis" password="iis" />
<text>台新金控12月3日將召開股東臨時會進行董監改選。</text>
</wordsegmentation>
    """

    a.parseString(text)
    print "DEBUG: encoding=%s"%a.getEncoding()
    print "DEBUG: text=%s"%a.getText()
    print "DEBUG: options=%s"%a.getOptions()
    print "DEBUG: userinfo=%s"%a.getUserInfo()


    L=[u"這是第一句。",u"這是第二句。"]
    print a.XMLStringListWrap(L,"UTF-8")
