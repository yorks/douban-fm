#!/usr/bin/env python
#-*- coding: utf8 -*-
# Author: stuyorks@gmail.com

import urllib2
import urllib
import httplib
import sys
import os
import random
import re


class DOUBAN_FM(object):
    def __init__(self, debug=False):
        self.bid = None
        self.dbcl2 = None
        self.uid = None
        self.verification_login_url=None
        self.captcha_id = None
        self.debug = debug

        self.channel_list = []
        self.douban_headers={}
        self.fm_headers={}
        self.get_bid()
        self.type_dict={}
        # from http://code.google.com/p/drhac/wiki/Protocol
        self.type_dict['b']='ban'     # 播放以删除终止. 长报告
        self.type_dict['e']='end'     # 返回:'"OK"', 报告歌曲播放完毕, 短报告
        self.type_dict['n']='new'     # 返回新播放列表, 无其余必备参数(uid?). 长报告
        self.type_dict['p']='playing' # 单首歌曲播放开始且播放列表已空时发送, 长报告, 疑似是专门为平淡地获取播放列表而设定的.
        self.type_dict['s']='skip'    # 用户点击”下一首“时即时报告
        self.type_dict['u']='unlike'  # 将sid的歌曲取消喜欢
        self.type_dict['r']='rated'   # 喜欢一首歌时即时报告
        self.params={}
        self.params['type_'] = 'n'
        self.params['channel'] = 1
        self.params['song_id'] = ''
        self.params['history'] = []
        self.params['album'] = ''


    def get_bid(self):
        """
         get bid from index page Cookie
         set bid to self.bid
        """
        url='http://www.douban.com/'
        headers={
                 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
                 'Accept':'text/html, application/xhtml+xml, */*',
                 'Host':'www.douban.com',
                 'Connection':'Keep-Alive',
                 'Accept-Language':'zh-CN',
                 'Cookie':'bid="Etpoyx3j0BA"; ac="1304248680"'
                }
        req = urllib2.Request(url=url, headers=headers)
        conn = urllib2.urlopen(req)
        #print conn.code
        header = str(conn.info())
        if self.debug:
            print header
        #Server: nginx
        #Content-Type: text/html; charset=utf-8
        #Connection: close
        #Content-Length: 89441
        #Expires: Sun, 1 Jan 2006 01:00:00 GMT
        #Pragma: no-cache
        #Cache-Control: must-revalidate, no-cache, private
        #P3P: CP="IDC DSP COR ADM DEVi TAIi PSA PSD IVAi IVDi CONi HIS OUR IND CNT"
        #Set-Cookie: bid="uT+Ovu6cadI"; path=/; domain=.douban.com; expires=Thu, 01-Jan-2012 00:00:00 GMT
        #Set-Cookie: ll="None"; path=/; domain=.douban.com; expires=Thu, 01-Jan-2012 00:00:00 GMT
        #Date: Sat, 14 May 2011 14:35:39 GMT
        try:
            self.bid = header.split(r'Set-Cookie:')[1].split(r'bid="')[1].split('";')[0]
        except:
            self.bid = "Etpoyx3j0BA"
        #print self.bid



    def login(self, account, password, verification_code=""):
        """
          login to douban.com to get cookies and uid
          return uid
        """
        #url='https://www.douban.com/accounts/login'
        if not verification_code:
            data = {'form_email':'%s'% account, 'form_password':'%s'% password}
        else:
            data = {'form_email':'%s'% account,
                    'form_password':'%s'% password,
                    'captcha-solution':'%s'% verification_code,
                    'captcha-id':'%s'% self.captcha_id }
        post_data = urllib.urlencode(data)
        self.douban_headers={
                 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
                 'Accept':'text/html, application/xhtml+xml, */*',
                 'Host':'www.douban.com',
                 'Connection':'Keep-Alive',
                 'Accept-Language':'zh-CN',
                 'Accept-Charset':'GB2312,utf-8;q=0.7,*;q=0.7',
                 #'Content-Type':'application/x-www-form-urlencoded',
                 #'Referer':'http://www.douban.com/',
                 #'Content-Length':'%d'% len(post_data),
                 'Cookie':'bid="%s"; ac="1304248680"; ll="None"'% self.bid
                }
        headers = self.douban_headers
        headers['Content-Length']="%d"% len(post_data)
        headers['Content-Type']="application/x-www-form-urlencoded"
        headers['Referer']="http://www.douban.com/"

        conn = httplib.HTTPSConnection("www.douban.com")
        conn.request("POST", "/accounts/login", post_data, headers)
        res = conn.getresponse()
        conn.close()
        #print res.getheaders()
        #print res.read()
        self.verification_login_url = res.getheader('location')
        #print self.verification_login_url
        if self.verification_login_url.find(r'requirecaptcha') != -1 or self.verification_login_url.find(r'&error=') != -1: # 验证码
            return self.verification_login_url

        all_cookie = res.getheader('Set-Cookie')

        # ue="stuyorks@gmail.com"; domain=.douban.com; expires=Thu, 01-Jan-2012 00:00:00 GMT, as="http://www.douban.com/"; path=/accounts; domain=.douban.com; expires=Sun, 15-May-2011 23:48:58 GMT, dbcl2="36142161:CkedbCHWYgY"; path=/; domain=.douban.com; httponly, sites="deleted"; max-age=0; domain=.douban.com; expires=Thu, 01-Jan-1970 00:00:00 GMT; path=/
        #print res.getheaders()
        #print res.read().decode('utf-8').encode('gbk')
        if all_cookie.find(r'dbcl2="') != -1:
            self.dbcl2 = all_cookie.split(r'dbcl2="')[1].split(r'";')[0]
            self.uid = self.dbcl2.split(r':')[0]
        return self.uid

    def get_verification_img(self, save_path='douban_verification_img.jpg'):
        if self.douban_headers['Content-Type']:
            del self.douban_headers['Content-Type']
        if self.douban_headers['Referer']:
            del self.douban_headers['Referer']
        if self.douban_headers['Content-Length']:
            del self.douban_headers['Content-Length']
        #print self.verification_login_url
        req = urllib2.Request(url=self.verification_login_url, headers=self.douban_headers)
        conn = urllib2.urlopen(req)
        #print conn.code
        verification_page = conn.read()
        conn.close()
        #print verification_page
        fw=open('verification_page.html', 'wb')
        fw.write(verification_page)
        fw.close()
        verification_img_url = re.findall(r'<img id="captcha_image" src="(.*)" alt="captcha" class="captcha_image"/>', verification_page, re.M)[0]
        # <input type="hidden" name="captcha-id" value="uLjvQQy5OfUxjLZ4BwAmo1i1"/>
        self.captcha_id = re.findall(r' name="captcha-id" value="(.*)"/>', verification_page, re.M)[0]
        #print verification_img_url, self.captcha_id
        req = urllib2.Request(url=verification_img_url, headers=self.douban_headers)
        conn = urllib2.urlopen(req)
        #print conn.code
        fw=open(save_path, 'wb')
        fw.write(conn.read())
        fw.close()
        conn.close()
        return self.captcha_id

    def verification_login(self, account, password, verification_code):
        self.login(account, password, verification_code)

    def get_channel_list(self):
        channel_list=[]
        #url='http://douban.fm/'
        url='http://www.douban.com/j/app/radio/channels'
        headers = dict(self.fm_headers)
        conn=None
        res=""
        try:
            req = urllib2.Request(url=url, headers=headers)
            conn=urllib2.urlopen(req)
            res = conn.read()
        except:
            pass
        try:
            res.decode('utf-8')
            #fw=open('douban.fm.log','a')
            #fw.write(res)
            #fw.close()
        except:
            pass
        if conn:
            conn.close()
        if res.find('channels') != -1:
            try:
                #channels = res.split("channels: '")[1].strip().split(r"'")[0].strip()
                #channels = urllib.unquote(channels)
                self.channel_list=eval(res)['channels']
                #self.channel_list = eval(channels)
                i=0
                for channel in self.channel_list:
                    if not channel.has_key('seq_id'):
                        channel['seq_id'] = i
                        i=i+1
            except:
                self.channel_list=[]

        like_seq_id = len(self.channel_list)
        LIKE_CHANNEL={"name": u"Red_Heart", "seq_id": like_seq_id, "abbr_en": "My", "channel_id": -3,"name_en": "Personal Radio"}
        if self.debug:
            print self.uid
        if self.uid: # logined user add red heart channel
            self.channel_list.append(LIKE_CHANNEL)
        if self.debug:
            print self.channel_list
        return self.channel_list

    def get_user_record(self):
        user_record={'played':0, 'liked':0, 'banned':0}
        url = 'http://douban.fm/j/check_loggedin'
        res = self.__request_douban_fm__(params=None, url=url)
        res = res.replace(':false',':False')
        res = res.replace(':true',':True')
        res = res.replace(':null', ':None')
        res_dict = eval(res)
        try:
            user_record['played'] = res_dict['user_info']['play_record']['played']
            user_record['liked']  = res_dict['user_info']['play_record']['liked']
            user_record['banned'] = res_dict['user_info']['play_record']['banned']
            return user_record
        except Exception, e:
            print "get_user_record cannot parse http://douban.fm/j/check_loggedin res."
            print str(e)

        ## if above false, user html code decode.

        if not self.uid:
            return user_record
        url='http://douban.fm/mine?type=played'
        url='http://douban.fm/'
        headers = dict(self.fm_headers)
        if headers['Keep-Alive']:
            del headers['Keep-Alive']
        import socket
        socket.setdefaulttimeout(5)
        req=urllib2.Request(url=url, headers=headers)
        conn=urllib2.urlopen(req)
        res = conn.read()
        conn.close()
        """<ul id="user_play_record">
            <li>
                <a href="/mine?type=played" target="_blank">累积收听<span id="rec_played">25733</span>首</a>
            </li>
            <li>
                <a href="/mine?type=liked" target="_blank">加红心<span id="rec_liked">224</span>首</a>
            </li>
            <li>
                <a href="/mine?type=banned" target="_blank"><span id="rec_banned">20</span>首不再播放</a>
            </li>
            </ul>"""
        try:
            user_record['played']=int(res.split(r'<span id="rec_played">')[1].split(r'</span>')[0])
            user_record['liked']=int(res.split(r'<span id="rec_liked">')[1].split(r'</span>')[0])
            user_record['banned']=int(res.split(r'<span id="rec_banned">')[1].split(r'</span>')[0])
        except:
            print res
        return user_record

    def __request_douban_fm__(self, params, url=None):
        r_str=get_random_num_char(10)
        if not url:
            type_ = params['type_']
            channel = params['channel']
            url='http://douban.fm/j/mine/playlist?type=%s&channel=%d&r=%s&from=mainsite'% (type_, channel, r_str)
            if params['song_id'] :
                url = url + '&sid=%s'% params['song_id']
            if params['history']:
                h = '|'.join(params['history'])
                url = url + '&h=%s'% h

        if self.debug:
            print "requtest_douban:", url
        headers = {
                    'Host':'douban.fm',
                    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
                    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language':'zh-cn,zh;q=0.5',
                    #'Accept-Encoding':'gzip, deflate',
                    'Accept-Charset':'GB2312,utf-8;q=0.7,*;q=0.7',
                    'Keep-Alive':'115',
                    'Connection':'keep-alive',
                    'Cookie':'bid="%s"; ac="1304248680"; ck="bEgb"; dbcl2="%s"'% (self.bid, self.dbcl2)
                  }
        self.fm_headers = headers
        req=urllib2.Request(url=url, headers=headers)
        conn=urllib2.urlopen(req)
        res = conn.read()
        conn.close()
        try:
            res.decode('utf-8')
            if self.debug:
                print res.decode('utf-8')

        except:
            pass
        return res

    def __parse_json_song_list_res__(self, res):
        song_list=[]
        res = res.replace(':false',':False')
        res = res.replace(':true',':True')
        res = res.replace(':null', ':None')
        if self.debug:
            print res
        try:
            json_dict = eval(res)
        except Exception, e:
            print res
            print e
            return []

        result = int(json_dict['r'])
        if result == 0 :
            play_list=json_dict['song']
            for song in play_list:
                song['url'] = song['url'].replace(r'\/', '/')
                song['picture'] = song['picture'].replace(r'\/', '/')
                song['album'] = song['album'].replace(r'\/', '/')
                song['albumtitle'] = song['albumtitle'].replace(r'\/', '/')
                song['artist'] = song['artist'].replace(r'\/', '/')
                song['title'] = song['title'].replace(r'\/', '/')
                if not song.has_key('public_time'):
                    continue
                else:
                    song_list.append(song)
        return song_list
        #url='http://douban.fm/j/mine/playlist?type=n&h=348207:p|1563376:p|961644:p|1563408:p|759698:p|1563322:p|1391856:p|1040692:p|1638836:p|670104:p|676223:p|363720:p|661823:p|1563004:p|761969:p|1383041:p|992505:p|709531:p|1063106:p|1563321:p&channel=1&r=8270e61929'
    def get_song_list(self, channel_id, history=[]):
        song_list = []
        params = dict(self.params)
        params['channel'] = channel_id
        params['history'] = history
        res = self.__request_douban_fm__(params)
        song_list = self.__parse_json_song_list_res__(res)
        return song_list

    def skip_next(self, song_id, channel_id, history=[]):
        params = dict(self.params)
        params['type_'] = 's'
        params['song_id'] = song_id
        params['channel'] = channel_id
        params['history'] = history
        res = self.__request_douban_fm__( params )
        song_list = self.__parse_json_song_list_res__(res)
        return song_list

    def report_song_end(self, song_id):
        params = dict( self.params )
        params['type_'] = 'e'
        params['song_id'] = song_id
        #params['history'] = history
        res = self.__request_douban_fm__( params )

    def like_song(self, song_id):
        params = dict( self.params )
        params['type_'] = 'r'
        params['song_id'] = song_id
        res = self.__request_douban_fm__( params )

    def unlike_song(self, song_id):
        params = dict( self.params )
        params['type_'] = 'u'
        params['song_id'] = song_id
        res = self.__request_douban_fm__( params )

    def ban_song(self, song_id):
        params = dict( self.params )
        params['type_'] = 'b'
        params['song_id'] = song_id
        res = self.__request_douban_fm__( params )

    def unban_song(self, song_id):
        url="http://douban.fm/j/song/%s/undo_ban"% song_id
        #headers = self.fm_headers
        pass


def get_random_num_char(many):
    all_random_element='1234567890abcdefghijklmnopqrstuvwxyz'
    random_num_char=''.join( random.sample(all_random_element, many) )
    return random_num_char

if __name__ == "__main__":
    account='stuyorks@gmail.com'
    password = '5******1'
    douban_fm = DOUBAN_FM()
    douban_fm.login(account, password)
    douban_fm.get_channel_list()
    song_list = douban_fm.get_song_list(0)
    print douban_fm.get_user_record()
    while True:
        if not song_list:
            song_list = douban_fm.get_song_list(0)
        for song in song_list:
            print song
            import commands
            code, output = commands.getstatusoutput("mplayer %s"% song['url'])
            del song_list[song]
