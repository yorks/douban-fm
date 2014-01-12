#!/usr/bin/env python2
#-*- coding: utf8 -*-
# Author: stuyorks@gmail.com

import lib_douban_fm
import sys
import threading
import time
import urllib2
import urllib
import os
import ConfigParser


sys.path.append('/home/yorks/python/lib/python2.5/site-packages')
#import mp3player
#import audio_player
import mplayer
import images_rc
import secure_str

DOUBAN_HOME=os.path.expanduser('~/.douban.fm/')
SAVE_MP3_DIR=os.path.expanduser('~/.douban.fm/mp3/')
ALBUM_PIC_DIR=os.path.expanduser('~/.douban.fm/album_pic')
CONF_FILE_PATH=os.path.join(DOUBAN_HOME, '.conf')
LIKED_LIST_FILE_PATH=os.path.join(DOUBAN_HOME, '.liked')

if not os.path.exists(SAVE_MP3_DIR):
    os.makedirs(SAVE_MP3_DIR)
if not os.path.exists(ALBUM_PIC_DIR):
    os.makedirs(ALBUM_PIC_DIR)

CACHE_MAX_SIZE=2 * 1024 * 1024 * 1024 # 2G

class DOUBAN(object):
    def __init__(self):
        self.account = ''
        self.password = ''
        self.islogined = False

        self.player = mplayer.MPLAYER()
        self.playing_clip = None
        self.playing_song = None # song_inf dict
        self.song_list = []
        self.channel_list = []
        self.current_channel = -3
        self.history = []
        self.user_record={}
        self.check_song_list_t = None
        self.check_song_end_t = None
        self.check_cache_t = None
        self.max_volume = 100
        self.fm = None

        self.like = False
        self.liked_list = []
        self.banned_list = []

        self.cache_max_size = CACHE_MAX_SIZE

        self.conf = CONFIG()
        self.cf_info = self.conf.get_cf_info()
        #print self.cf_info
        self.parse_conf()
        #print self.liked_list
        #self.conf.set_option('douban','username', 'stuyorks@gmail.com')

    def parse_conf(self):
        if os.path.isfile(CONF_FILE_PATH):
            account = self.cf_info['douban']['username']
            password = self.cf_info['douban']['password']
            if password:
                try:
                    password = secure_str.decode( password )
                except:
                    password = ''
                    print "Error cf file format(pw)"
            try:
                self.cache_max_size = float( self.cf_info['client']['max_cache_size'] )
            except:
                self.cache_max_size = CACHE_MAX_SIZE
                print "Error cf file format(cms)"
            #print account, password
            self.account = account
            self.password = password
        if os.path.isfile(LIKED_LIST_FILE_PATH):
            fp = open(LIKED_LIST_FILE_PATH, 'r')
            content = fp.read()
            fp.close()
            self.liked_list = content.split(r'|')


    def login(self):
        if not self.password:
            self.account = raw_input('account:')
            self.password = raw_input('password:')

        if not self.fm:
            self.fm = lib_douban_fm.DOUBAN_FM()
        if self.fm.captcha_id:
            verification_code = raw_input('code')
            is_login = self.fm.login( self.account, self.password, verification_code )
        else:
            is_login = self.fm.login(self.account, self.password)
        if is_login.startswith(r'http://'):
            captcha_id = self.fm.get_verification_img()
            if captcha_id:
                return 0

            else:
                print "cannot get code"
                return 0


        if is_login and not is_login.startswith(r'http://'):
            self.islogined = True

            self.play_pause()
        else:
            return 0
    def get_channel_list(self):
        self.channel_list = self.fm.get_channel_list()

    def play_pause(self):
        """ play_pause   PAUSE / UNPAUSE / PLAY(first login) """
        if self.playing_clip: # PAUSE / UNPAUSE
            status = self.playing_clip.get_status()
            if not status == 'playing' and status != 'pause':
                self.play_next()
            elif status == 'pause':
                self.playing_clip.unpause()
            elif status == 'playing':
                self.playing_clip.pause()
            else:
                pass
        else: # PLAY(first login)
            self.__play__()
            time.sleep(0.5)
            self.check_song_list_t = MY_THREAD(self.check_song_list,())
            self.check_song_list_t.setDaemon(True)
            self.check_song_list_t.start()
            time.sleep(0.5)
            self.check_song_end_t = MY_THREAD(self.check_song_end,())
            self.check_song_end_t.setDaemon(True)
            self.check_song_end_t.start()
            time.sleep(0.5)
            self.check_cache_t = MY_THREAD(self.loop_check_cache,())
            self.check_cache_t.setDaemon(True)
            self.check_cache_t.start()

    def play_next(self):
        if not self.playing_clip :
            pass
        else:
            if self.playing_clip.status=='playing' or self.playing_clip.status=='pause':
                """ 点击next按钮 """
                self.playing_clip.stop()
                sid_p = "%s:s"% self.playing_song['sid']
                self.history.append(sid_p)
                if len(self.history) > 20 :
                    del self.history[0]
            else:
                """ 一首歌播放完，自动播放下首歌 """
                sid_p = "%s:p"% self.playing_song['sid']
                if sid_p not in self.history: self.history.append(sid_p)
                if len(self.history) > 20 :
                    del self.history[0]
            self.playing_clip = None
        self.__play__()

    def __play__(self):
        while not self.song_list: # cannot get song_list, always try to get...
            self.song_list = self.fm.get_song_list(self.current_channel, self.history)
        self.playing_song = self.song_list[0]
        print self.playing_song
        try:
            self.mp3_play(self.playing_song)
        except:
            print "Cannot play this song.."
            sys.exit(1)

        del self.song_list[0]
        self.set_playing_ui()

    def get_mp3_file(self, song_info):
        if not song_info:
            song_info = self.playing_song
        mp3_file_name = song_info['sid']+'.mp3'
        mp3_file_path=os.path.join(SAVE_MP3_DIR, mp3_file_name)
        if os.path.isfile(mp3_file_path):
            return mp3_file_path
        try:
            conn = urllib2.urlopen(song_info['url'])
        except:
            print "urllib2 get except:", song_info['url']
            return False
        fw=open(mp3_file_path, 'wb')
        fw.write(conn.read())
        fw.close()
        conn.close()
        if not os.path.isfile(mp3_file_path):
            print "not file", mp3_file_path
            return False
        if os.path.getsize(mp3_file_path) == 0:
            try:
                os.unlink(mp3_file_path)
            except:
                pass
            return False
        return mp3_file_path

    def need_2_next(self):
        if self.playing_clip:
            #if self.playing_clip.is_playing() or self.playing_clip.is_paused():
            if self.playing_clip.get_status() != 'ended':
                pass
            #elif not self.playing_clip.is_playing() and not self.playing_clip.is_paused():
            #    print "this song end!"
            #    pass
            else:
                try:
                    self.fm.report_song_end(self.playing_song['sid'])
                except:
                    print "report song end......\033[1;31mfail\033[m!!!"

                sid_p = "%s:p"% self.playing_song['sid']
                if sid_p not in self.history: self.history.append(sid_p)
                if len(self.history) > 20 :
                    del self.history[0]

                self.play_next()

        else:
            pass

    def skip_next(self):
        pass

    def set_volume(self, value):
        if self.playing_clip:
            self.playing_clip.set_volume(value)
        else:
            pass

    def like_unlike(self):
        if not self.like:
            self.fm.like_song(self.playing_song['sid'])
            self.like = True
            if self.playing_song['sid'] not in self.liked_list:
                self.liked_list.append( self.playing_song['sid'] )
        else:
            self.fm.unlike_song(self.playing_song['sid'])
            self.like = False
            if self.playing_song['sid'] in self.liked_list:
                self.liked_list.remove( self.playing_song['sid'] )

    def set_playing_ui(self):
        #print self.playing_song

        sid    = self.playing_song['sid'].decode('utf8')
        ssid    = self.playing_song['ssid'].decode('utf8')
        title  = self.playing_song['title'].decode('utf8')
        artist = self.playing_song['artist'].decode('utf8')
        albumtitle = self.playing_song['albumtitle'].decode('utf8')
        public_time = self.playing_song['public_time'].decode('utf8')
        like        = self.playing_song['like']
        like_human = ''
        if like == 1:
            like_human = '红心'
        pic_url = self.playing_song['picture'].decode('utf8')
        try:
            print sid, title, artist, like_human
        except:
            pass

        album_link = 'http://music.douban.com' + self.playing_song['album'].decode('utf8')
        google_song_link = 'http://www.google.cn/music/search?q='+ title

        s_song_url=u'http://douban.fm/?start=%sg%sg0&cid=0'% (sid, ssid)
        try:
            s_title = urllib.quote(s_title.encode('utf8'))
        except:
            pass
        s_pic = pic_url.replace('/mpic/', '/lpic/')


    def get_album_pic(self, song_info=""):
        """ get album picture  ->  { file_path | False }
              * song_info: song information dict, {'picture':'', aid:''...}
              # return
                  the album pic file path, if cannot get retrun False
        """
        if not song_info:
            song_info = self.playing_song
        album_id=song_info['aid']
        album_pic_file_name = "%s.jpg"% album_id
        album_pic_file_path = os.path.join( ALBUM_PIC_DIR, album_pic_file_name )
        if os.path.isfile(album_pic_file_path):
            return album_pic_file_path

        url=song_info['picture']
        conn = None
        isget=True
        try:
            conn = urllib2.urlopen(url)
            pic_string = conn.read()
        except:
            isget=False
            print url
        finally:
            if conn:
                conn.close()
        if isget:
            fw = open( album_pic_file_path, 'wb' )
            fw.write(pic_string)
            fw.close()
            return album_pic_file_path
        else:
            return False

    def mp3_play(self, song_info=""):
        if not song_info:
            song_info = self.playing_song
        mp3_file_path=self.get_mp3_file( song_info )
        if not mp3_file_path:
            raise "cannot get mp3 file %s"% song_info
        isload = self.player.load_file(mp3_file_path)
        if isload != 200:
            raise "cannot load this song!"
        self.playing_clip=self.player
        #self.set_volume()
        self.playing_clip.play()
        #self.set_playing_ui()

    def check_song_list(self):
        while True:
            if len(self.song_list) <= 1 :
                self.song_list = self.fm.get_song_list(self.current_channel, self.history)
            if len(self.song_list) >= 1:
                #print "pre get mp3 file %s"% self.song_list[0]['url']
                self.get_mp3_file(self.song_list[0])
            time.sleep(10)

    def check_song_end(self):
        while True:
            time.sleep(1)
            if not self.playing_clip.is_alive() and self.playing_clip.status == 'stop':
                self.play_next()


    def quit(self):
        if self.check_song_end_t :
            self.check_song_end_t.kill()
        if self.check_song_list_t :
            self.check_song_list_t.kill()
        if self.check_cache_t:
            self.check_cache_t.kill()

        if self.playing_clip:
            self.playing_clip.stop()

        if self.fm:
            try:
                self.save_liked_list()
            except:
                pass
        sys.exit()


    def get_cache_info(self):
        """ get mp3 dir cache files size order by mtime """
        cache_info={}
        cache_file_list = []
        total_size = 0L
        if os.path.isdir(SAVE_MP3_DIR):
            filename_list = os.listdir(SAVE_MP3_DIR)
            for filename in filename_list:
                file_path = os.path.join(SAVE_MP3_DIR, filename)
                if os.path.isfile(file_path):
                    file_info = {'path':file_path, 'size':0, 'mtime':0}
                    file_info['size'] = os.path.getsize(file_path)
                    file_info['mtime'] = os.path.getmtime(file_path)
                    if file_info['size'] == 0: # remove size = 0 file
                        try:
                            os.unlink(file_path)
                        except WindowsError:
                            pass
                        continue
                    if filename.replace(r'.mp3', '') in self.banned_list: # remove file in banned_list
                        try:
                            os.unlink(file_path)
                        except WindowsError:
                            pass
                        continue
                    cache_file_list.append(file_info)
                    total_size = total_size + file_info['size']
                    del file_info
        if cache_file_list:
            cache_file_list.sort( key=lambda x:x['mtime'], reverse=True ) # 3333 3332 ... 2222 ... 0

        cache_info['size'] = total_size
        cache_info['file_list'] = cache_file_list
        return cache_info

    def clean_cache(self):
        if self.cache_max_size == 0:
            return
        cache_info = self.get_cache_info()
        delta_size = self.cache_max_size - cache_info['size']
        rev_space = 100 * 1024 * 1024 # 100M
        for cache in cache_info['file_list']:
            if delta_size >= rev_space:
                break
            else:
                if os.path.isfile(cache['path']):
                    try:
                        song_id = os.path.basename( cache['path'] )[:-4]
                    except:
                        continue
                    if song_id in self.liked_list:
                        continue
                    if self.playing_clip and self.playing_clip.file_path == cache['path']:
                        continue
                    print "clean cache:",
                    print cache['path']
                    try:
                        os.unlink(cache['path'])
                    except WindowsError:
                        pass
                    delta_size = delta_size + cache['size']
    def loop_check_cache(self):
        while True:
            self.clean_cache()
            time.sleep( 3600*2 ) # 2 hours

    def save_liked_list(self):
        if self.liked_list:
            content = r'|'.join( [str(i) for i  in self.liked_list] )
            fw = open(LIKED_LIST_FILE_PATH, 'w')
            fw.write(content)
            fw.close()

    def ban_song(self):
        if self.playing_song:
            self.fm.ban_song(self.playing_song['sid'])
            if self.playing_song['sid'] not in self.banned_list:
                self.banned_list.append(self.playing_song['sid'])
            self.play_next()
    def change_channel(self, c):
        c = int( c )
        self.current_channel = c
        self.play_next()

    def open_album_url(self):
        if self.playing_song:
            album_link = u'http://music.douban.com' + self.playing_song['album'].decode('utf8')


class MY_THREAD(threading.Thread):
    def __init__(self, func, args, name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args
        self.over = False

    def run(self):
        apply(self.func, self.args)
        if self.over:
            sys.exit()

    def kill(self):
        self.over = True

class CONFIG(object):
    def __init__(self, file_path=CONF_FILE_PATH):
        self.cf_file_path = file_path
        # default value
        self.cf_info = { 'douban':{'username':'', 'password':''}, 'client':{'max_cache_size':CACHE_MAX_SIZE},
                'shortcut':{'login':'RETURN','quit':'ESC', 'play_pause':'P', 'next':'N', 'like':'L', 'ban':'B', 'setting':'S' } }
        self.need_reload=True
        self.cf = ConfigParser.SafeConfigParser()
        self.fp=None
        self.fp_write=None

        self._init_cf_file()

    def _init_cf_file(self):
        if os.path.isfile(self.cf_file_path):
            try:
                self._read_cf_file()
            except:
                if self.fp:
                    self.fp.close()
                return False
            add_flag=False
            sections = self.cf.sections()
            for section in self.cf_info.keys():
                if section in sections:
                    continue
                self.cf.add_section(section)
                add_flag=True
                for option in self.cf_info[section].keys():
                    value = self.cf_info[section][option]
                    self.cf.set( section, option, str(value) )
            if add_flag:
                self._write_cf_file()
                self.cf.write(self.fp_write)
            if self.fp_write:
                self.fp_write.close()
            if self.fp:
                self.fp.close()
            self.need_reload=True

        else:
            config = ConfigParser.RawConfigParser()
            for section in self.cf_info.keys():
                config.add_section(section)
                for option in self.cf_info[section].keys():
                    value = self.cf_info[section][option]
                    config.set( section, option, str(value) )
            try:
                fw=open(self.cf_file_path, 'wb')
                config.write(fw)
                fw.close()
            except:
                pass
            self.need_reload=True

    def _read_cf_file(self):
        self.fp = open(self.cf_file_path, 'r')
        self.cf.readfp(self.fp)

    def _write_cf_file(self):
        self.fp_write = open(self.cf_file_path, 'w')

    def parse_conf(self):
        try:
            self._read_cf_file()
        except:
            return False

        sections = self.cf.sections()
        for section in sections:
            options = self.cf.options(section)
            for option in options:
                value = self.cf.get(section,option)
                self.cf_info[section][option]=value
        if self.fp:
            self.fp.close()
        self.need_reload=False
        return self.cf_info

    def set_option(self, section, option, value):
        if section not in self.cf_info.keys():
            return False
        try:
            self._read_cf_file()
        except:
            if self.fp:
                self.fp.close()
            return False
        try:
            self.cf.set(section, option, value)
        except:
            return False
        self._write_cf_file()
        self.cf.write(self.fp_write)
        if self.fp_write:
            self.fp_write.close()
        if self.fp:
            self.fp.close()
        self.need_reload=True
        return True


    def get_cf_info(self, force_new=False):
        if force_new or self.need_reload:
            self.parse_conf()

        return self.cf_info


def print_help_msg():
    print "===============Please follow the belove Command=============="
    print
    print " -------------- 'n' for next song  --------------------------"
    print " -------------- 'c' for change channel ----------------------"
    print " -------------- 'b' for ban the song  -----------------------"
    print " -------------- 'l' for like the song  ----------------------"
    print " -------------- 'v' for set volume  -------------------------"
    print " -------------- 'q' for quit this program      --------------"
    print " -------------- 'h' for Help (this HelpMessage)--------------"
    print " -------------- 'a' for About this program ------------------"

if __name__ == "__main__":
    fm = DOUBAN()
    fm.login()
    if not fm.islogined :
        fm.login()

    while 1:
        time.sleep(0.1)
        try:
            command = raw_input('>>>')
        except:
            fm.quit()
            break
        if command == 'n':
            print "next"
            fm.play_next()
        elif command == 's':
            print "skip"
            fm.play_next()
        elif command == 'b':
            print "ban"
            fm.ban_song()
        elif command == 'l':
            print "like"
        elif command == 'c':
            print "change channel"
            fm.get_channel_list()
            for channel in fm.channel_list:
                print channel['name'], channel['channel_id']
            c=int(raw_input('pls input the channel id:'))
            fm.change_channel(c)

        elif command == 'q':
            print "quit"
            fm.quit()
            break
        elif command == 'v':
            v = int(raw_input('pls input the volume(0-100):'))
            fm.set_volume(v)
        elif command == 'h':
            print_help_msg()


