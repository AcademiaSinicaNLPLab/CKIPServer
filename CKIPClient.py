#!/usr/bin/python
#-*- encoding: latin-1 -*-

import socket
import sys
import string
import re


class CkipSrv:
    def __init__(self,user,passwd,server="localhost", port=1501):
	self.opt={}
	self.opt['user']=user
	self.opt['passwd']=passwd
	self.server = server
	self.port = port
	self.errmsg=""
	self.errno=None

    def process(self,text, request_form):
	self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	self.sock.connect((self.server, self.port))
	sockOut= self.sock.makefile("wb")
	sockIn = self.sock.makefile('rb')
	self.sock.close()
	self.opt['text'] = text
	request=request_form%self.opt
        sockOut.write(request)
	sockOut.close()
	data=""
	while 1:
	    response = sockIn.readline()
	    if "</wordsegmentation>" in response: 
	        data+=response
	        break
	    data+=response
	sockIn.close()

	return data

    def segStr(self, in_data, options={}):
        request_form='<?xml version="1.0" encoding="%s"?>' %(options['encoding'])
	request_form+='<wordsegmentation version="0.1">'
	if options['pos']:
	    request_form+='<option showcategory="1" />'
	else:
	    request_form+='<option showcategory="0" />'

	if options['uwe']:
	    request_form+='<option UnknownWordExtraction="1" />'
	else:
	    request_form+='<option UnknownWordExtraction="0" />'

	request_form+='<authentication username="%(user)s" password="%(passwd)s" />'
	request_form+='<text><![CDATA[%(text)s]]></text>'
	request_form+='</wordsegmentation>\n'

        response=self.process(in_data, request_form)

	if not ('<processstatus code="0">' in response):
	    m=re.search(r'<processstatus code=(.*)>(.*)</processstatus>',response)
	    if m:
		sys.stderr.write("ERROR(%s):%s\n"%(m.group(1),m.group(2)))
		sys.exit(1)
	    
	if options['xml']:
	    return response

        L=re.findall(r"<sentence>.*?</sentence>",response)
	output=""
	for line in L:
	    output+=line[10:-11]+"\n"

	return output

    def segFile(self, input, output=None, options={}):
	if input==None:
	    fi=sys.stdin
	else:
	    fi = open(input,"r")
        if output==None:
	    fo=sys.stdout
        else:
	    fo=open(output,"w")

	line_no=0
	L=[]
	for line in fi:
	    L.append(line)
	    line_no+=1
	    if line_no % options['divide']==0:
		data=string.join(L,"")
                response=self.segStr(data, options)
		fo.write(response)
		L=[]

	if len(L)>0:
	    data=string.join(L,"")
            response=self.segStr(data, options)
	    fo.write(response)

	if output!=None:
	    fo.close()
	fi.close()


def usage():
    import os
    print """
USAGE: %s [OPTIONS] input [output]
OPTIONS:
    -h, --help			輸出 USAGE 訊息
    -d, --divide=num		將要斷詞的檔切分成比較小的句數，然後分批斷詞。
				因為 Server 針對每一個檔案有斷詞時間的限制，如
				果單一檔案太大，Server 會自動中斷該檔的斷詞。所
				以如果檔案超過一定的大小，就會被自動切分。
				(預設值為1000)
    -e, --encoding=code		輸入及輸出的編碼，預設為 UTF-8   
    -S, --server=host 		指定提供斷詞服務的 IP 位址
    -P, --port=num		指定提供斷詞服務的 port
    -u, --unknown-word=0,1	指定是否要組合 unknown word，預設為 1
    -x, --xml			直接輸出從 server 收取的資料
""" %(os.path.basename(sys.argv[0]))

def main():
    import getopt
    options={}
    options['divide']=1000
    options['encoding']="UTF-8"
    options['pos']=True
    options['server']='localhost'
    options['port']=1501
    options['uwe']=True
    options['xml']=False
    try:
	opts, args = getopt.getopt(sys.argv[1:], 'hd:e:p:P:s:S:u:x', [
		"help", "divide=", "encoding=", "pos=", "separator=","port=","server=", "unknown-word=","xml"
	    ])
    except getopt.GetoptError, err:
	print str(err)
	usage()
	sys.exit()

    for o, a in opts:
	if o in ("-h","--help"):
	    usage()
	    sys.exit(1)
	elif o in ("-e","--encoding"):
	    options['encoding']=a
	elif o in ("-l", "--line-mode"):
	    if a=="0" or a.lower()=="false":
		options['linemode']=False
	    else:
		options['linemode']=True
	elif o in ("-p","--pos"):
	    if a=="0" or a.lower()=="false":
		options['pos']=False
	    else:
		options['pos']=True
	elif o in ("-s","--separator"):
	    options['separator']=a
	elif o in ("-P","--port"):
	    options['port']=int(a)
	elif o in ("-S","--server"):
	    options['server']=a
	elif o in ("-x","--xml"):
	    options['xml']=True
	elif o in ("-u","--unknown-word"):
	    if a=="0" or a.lower()=="false":
		options['uwe']=False
	    else:
		options['uwe']=True
	elif o in ("-d","--divide"):
	    options['divide']=int(a);
	else:
	    assert False, "undefined option"

    output=None
    input=None
    if len(args)==0:
	pass
    if len(args)==1:
	input=args[0]
    elif len(args)==2:
	input=args[0]
	output=args[1]
    else:
	usage()
	sys.exit(1)

    srv = CkipSrv("wordseg","1234",server=options['server'], port=options['port'])
    srv.segFile(input, output, options)
    


if __name__ == "__main__":
    main()


