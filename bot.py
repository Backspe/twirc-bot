#-*- coding: utf-8 -*-
import tweepy
import sys
import json
import setting
import threading
from queue import Queue
import time
import re
from datetime import datetime, timedelta
from connector.ircmessage import IRCMessage


key = setting.twitterkey
auth = tweepy.OAuthHandler(key.consumer_key, key.consumer_secret)
auth.set_access_token(key.access_token, key.access_token_secret)
api = tweepy.API(auth)
screen_name = setting.screen_name
irc_name = setting.irc_name



class ircBot(threading.Thread):
    irc = None
    msgQueue = Queue()
    last_id = ''
    footer = ''
    prog = re.compile(r'(\bhttps?://twitter.com/[a-zA-Z0-9_/]+/(\d+)\b)')
    log = open("log.txt", 'a')

    def __init__(self):
        self.log.write('log start at '+str(datetime.now())+'\n')
        super(ircBot, self).__init__()

    def run(self):
        from connector.ircconnector import IRCConnector
        self.irc = IRCConnector(self.msgQueue)
        self.irc.start()
        for c in setting.chan_list:
            self.irc.joinchan(' '.join(c).strip())
        while True:
            packet = self.msgQueue.get()
            if packet['type'] == 'msg':
                pass
            elif packet['type'] == 'irc':
                message = packet['content']
                if message.msgType == 'INVITE':
                    self.irc.joinchan(message.channel)
                elif message.msgType == 'PRIVMSG':
                    if message.sender.find(irc_name) == 0:
                        if message.msg.find('!트윗 ') == 0:
                            content = message.msg[4:] + self.footer
                            stat = tweet(content=content)
                            if stat == None: continue
                            tweet_url = "https://twitter.com/" + screen_name + "/status/" + stat.id_str
                            self.irc.sendmsg(message.channel, tweet_url)
                            self.last_id = stat.id_str
                            self.log.write(message.msg+'\n')
                            self.log.write(tweet_url+'\n')
                            print('send tweet:', tweet_url)
                            continue
                        elif message.msg.find('!연속 ') == 0:
                            content = message.msg[4:] + self.footer
                            stat = tweet(content=content, reply_id=self.last_id)
                            if stat == None: continue
                            tweet_url = "https://twitter.com/" + screen_name + "/status/" + stat.id_str
                            self.irc.sendmsg(message.channel, tweet_url)
                            self.last_id = stat.id_str
                            self.log.write(message.msg+'\n')
                            self.log.write(tweet_url+'\n')
                            print('send tweet:', tweet_url)
                            continue
                        elif message.msg.find('!연속잇기 ') == 0:
                            content = message.msg[len('!연속잇기 '):]
                            self.last_id = content
                            self.irc.sendmsg(message.channel, content)
                            print('connect change:', content)
                        elif message.msg.find('!꼬릿말 ') == 0:
                            content = message.msg[len('!꼬릿말 '):]
                            self.footer = content
                            self.irc.sendmsg(message.channel, "꼬릿말 변경: '" + content + "'")
                            print('footer change:', content)

                    tweet_urls = self.prog.findall(message.msg)
                    for tweet_url, tweet_id in tweet_urls:
                        try:
                            stat = api.get_status(tweet_id)
                            tweet_string = stat.user.name + "(@" + stat.user.screen_name + "): " + stat.text
                            tweet_string = tweet_string.replace('\n', '\\n')
                            self.irc.sendmsg(message.channel, tweet_string)
                            self.log.write(tweet_string+'\n')
                            print('get tweet:', tweet_string)
                        except Exception as e:
                            self.irc.sendmsg(message.channel, "URL ERROR")
                            print('URL ERROR:', e)
                                    

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
    bot = ircBot()
    bot.start()
