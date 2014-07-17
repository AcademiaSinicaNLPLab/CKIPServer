# -*- coding: utf-8 -*-
import sys
#sys.path.append('/home/plum/CKIPServer')
from CKIPClient import *
import os, codecs

from functools import wraps
import signal, errno


class TimeoutError(Exception):
    pass


def timeout(seconds=10, error_messages=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            #print "Time out "
            raise TimeoutError(error_messages)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wraps(func)(wrapper)
    return decorator


options = {'divide': 1000,\
           'encoding': 'UTF-8',\
           'port': 1501,\
           'pos': True,\
           'server': 'localhost',\
           'uwe': True,\
           'xml': False}

from sys import stdout

class Tokenizer:
    def __init__(self, opt=options):
        self.srv = CkipSrv("wordseg","1234",server=opt['server'], port=opt['port'])

    @timeout(30)
    def tokenizeStr(self, s):
        try:
            res = self.srv.segStr(s, options)
        except TimeoutError:
            print "Time out"
            return None
        else:
            return res

    def tokenizeFile(self, infile, outfile):
        with codecs.open(infile, 'r', 'utf-8') as f:
            lines = f.read().strip().split('\n')
        
        outf = codecs.open(outfile, 'w', 'utf-8')

        for i, l in enumerate(lines):    
            print str(i) + " " + l.encode('utf-8')
#            stdout.write("\r%d %s" % (i, l.encode('utf-8')))
#            stdout.flush()

            res = self.tokenizeStr(l.encode('utf-8'))
            if res is not None:
                outf.write(res.strip().decode('utf-8') + '\n')
        outf.close()

if __name__ == "__main__":
    tokenizer = Tokenizer()
    #bad sentence
    print tokenizer.tokenizeStr('如果你需要時間好好冷靜的思考.......沒關係......我願意等你.......無論多久我都會等你........等你準備好了.........等你願意見我.......我不會再讓你擔心.......我也會按時吃飯........也會好好照顧自己.......你說的我都答應你........真的.......我說的都是真的.........請你相信 我.......... 小黑豬不會和小白豬分開的......就算有........也只是短暫的')


