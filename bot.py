#-*- coding: utf-8 -*-
import tweepy
import sys
import json
import setting
import threading
from queue import Queue
import time
from datetime import datetime, timedelta
from connector.ircmessage import IRCMessage


key = setting.twitterkey
auth = tweepy.OAuthHandler(key.consumer_key, key.consumer_secret)
auth.set_access_token(key.access_token, key.access_token_secret)
api = tweepy.API(auth)
screen_name = setting.screen_name
irc_name = setting.irc_name
f = open("log.txt", 'a')

tweetqueue = Queue()

class ircBot(threading.Thread):
    irc = None
    msgQueue = Queue()
    last_id = ''

    def __init__(self):
        super(ircBot, self).__init__()

    def run(self):
        from connector.ircconnector import IRCConnector
        self.irc = IRCConnector(self.msgQueue)
        self.irc.start()
        for c in setting.chan_list:
            self.irc.joinchan(' '.join(c).strip())
        while True:
            packet = self.msgQueue.get()
            if packet['type'] == 'irc':
                message = packet['content']
                if message.msgType == 'INVITE':
                    self.irc.joinchan(message.channel)
                elif message.msgType == 'PRIVMSG':
                    if message.sender.find(irc_name) == 0:
                        if message.msg.find('!트윗 ') == 0:
                            content = message.msg[4:]
                            stat = tweet(content=content)
                            if stat == None: continue
                            tweet_url = "https://twitter.com/" + screen_name + "/status/" + stat.id_str
                            self.irc.sendmsg(message.channel, tweet_url)
                            self.last_id = stat.id_str
                        elif message.msg.find('!연속 ') == 0:
                            content = message.msg[4:]
                            stat = tweet(content=content, reply_id=self.last_id)
                            if stat == None: continue
                            tweet_url = "https://twitter.com/" + screen_name + "/status/" + stat.id_str
                            self.irc.sendmsg(message.channel, tweet_url)
                            self.last_id = stat.id_str

                        
            elif packet['type'] == 'msg':
                pass

def tweet(content="", reply_id = ""):
    stat = None
    try:
        stat = api.update_status(status=content, in_reply_to_status_id=reply_id)
    except tweepy.TweepError as e:
        print(e)
        print(e.response)
        print(e.api_code)
        if e.api_code == 187:
            stat = api.update_status(status=content + '.', in_reply_to_status_id=reply_id)
    except Exception as e:
        print(e)
        print(e.reason)
    return stat

if __name__ == '__main__':
    f.write('log start at '+str(datetime.now())+'\n')
    
    tweet(content=' '.join(sys.argv[1:]))

    bot = ircBot()
    bot.start()
