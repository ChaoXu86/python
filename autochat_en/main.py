# -*- coding: utf-8 -*-
import itchat, time, re, os, aiml
import sys
from itchat.content import *

#reload(sys)
#sys.setdefaultencoding('utf-8')

os.chdir('./res/alice')

alice=aiml.Kernel()
alice.learn("startup.xml")
alice.respond('LOAD ALICE')

zhPattern = re.compile(u'[\u4e00-\u9fa5]+')

@itchat.msg_register([TEXT])
def text_reply(msg):
    #Text = msg['Text']
    #print Text.decode('utf8')
    #print msg['Text'].decode('utf8')
    match = zhPattern.match(msg['Text'])#.decode('utf8'))

    if match:
        itchat.send(('I am a chat robot, ONLY ENGLISH !'), msg['FromUserName'])
    else:
        itchat.send((alice.respond(msg['Text'])), msg['FromUserName'])

itchat.auto_login(enableCmdQR=2,hotReload=True)
itchat.run(debug=True)

