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
import secure_str

DOUBAN_HOME=os.path.expanduser('~/.douban.fm/')
SAVE_MP3_DIR=os.path.expanduser('~/.douban.fm/mp3/')
ALBUM_PIC_DIR=os.path.expanduser('~/.douban.fm/album_pic')
CONF_FILE_PATH=os.path.join(DOUBAN_HOME, '.conf')
LIKED_LIST_FILE_PATH=os.path.join(DOUBAN_HOME, '.liked')


CACHE_MAX_SIZE=2 * 1024 * 1024 * 1024 # 2G

class DOUBAN(object):
    def __init__(self):
        self.account = ''
        self.password = ''
        self.islogined = False
        self.volume = 30
        self.max_volume = 100

        self.player = mplayer.MPLAYER(volume=self.volume)
        self.playing_clip = None
        self.playing_song = None # song_inf dict
        self.song_list = []
        self.channel_list = []
        self.current_channel = 0
        self.history = []
        self.user_record={}
        self.check_song_list_t = None
        self.check_song_end_t = None
        self.check_cache_t = None
        self.fm = None

        self.like = False
        self.liked_list = []
        self.banned_list = []

        self.cache_max_size = CACHE_MAX_SIZE
        self.cache_dir = SAVE_MP3_DIR
        self.local_dir = SAVE_MP3_DIR
        self.tmp_dir   = "/tmp/.douban.mp3/"
        self.playing_file_path = None

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
            self.cache_dir = self.cf_info['client']['cache_dir']
            self.local_dir = self.cf_info['client']['local_dir']
            self.tmp_dir   = self.cf_info['client']['tmp_dir']

        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        if not os.path.exists(self.local_dir):
            os.makedirs(self.local_dir)
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        ## todo
        if not os.path.exists(ALBUM_PIC_DIR):
            os.makedirs(ALBUM_PIC_DIR)

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
            verification_code = raw_input('pls input verify code:')
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
        #print self.playing_song
        try:
            self.mp3_play(self.playing_song)
        except Exception ,e:
            print str(e)
            print "Cannot play this song.."
            print self.playing_song
            sys.exit(1)

        del self.song_list[0]
        self.set_playing_ui()

    def get_mp3_file(self, song_info):
        if not song_info:
            song_info = self.playing_song
        mp3_file_name = song_info['sid']+'.mp3'
        try:
            #title  = song_info['title'].decode('utf8')
            title  = song_info['title']
        except Exception, e:
            print str(e)
            print "cannot get title, skip local"
            title = mp3_file_name

        try:
            local_file_list = os.listdir(self.local_dir)
        except Exception, e:
            print str(e)
            local_file_list = []

        for name in local_file_list:
            file_path = os.path.join(self.local_dir, name)
            if os.path.isfile(file_path):
                try:
                    title = title.replace(' ', '_')
                    if name.startswith(title) and (name.lower().endswith('mp3') or name.lower().endswith('flac')):
                        return file_path
                    title = title.replace('_', ' ')
                    if name.startswith(title) and (name.lower().endswith('mp3') or name.lower().endswith('flac')):
                        return file_path

                except Exception, e:
                    print title
                    print str(e)
                    print name
                    continue

        mp3_file_path=os.path.join(self.cache_dir, mp3_file_name)
        if os.path.isfile(mp3_file_path):
            return mp3_file_path

        mp3_file_path=os.path.join(self.tmp_dir, mp3_file_name)
        if os.path.isfile(mp3_file_path):
            return mp3_file_path

        try:
            conn = urllib2.urlopen(song_info['url'])
        except:
            print "urllib2 get except:", song_info['url']
            return False
        fw=open(mp3_file_path, 'wb') # save to tmp_dir
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
            self.volume = value
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
        album_link = 'http://music.douban.com' + self.playing_song['album'].decode('utf8')
        like        = self.playing_song['like']
        like_human = ''
        if like == 1:
            self.like = True
            #like_human = '红心'
            like_human = '\033[1;31m    ♥\033[m'
        pic_url = self.playing_song['picture'].decode('utf8')
        print "volume: %d"% self.volume
        print "current_channel: %d"% self.current_channel,
        if not self.channel_list:
            self.get_channel_list()
        for channel in self.channel_list:
            if channel['channel_id'] == self.current_channel:
                print channel['name']

        try:
            print "\nPlaying:",
            print "歌名:",title, '歌手:',artist, "专辑:", albumtitle, like_human
            if self.playing_file_path:
                print "mp3_file_path:%s"% self.playing_file_path
            print album_link
        except:
            pass

        # next
        try:
            n_title  = self.song_list[0]['title'].decode('utf8')
            n_artist = self.song_list[0]['artist'].decode('utf8')
            n_albumtitle = self.song_list[0]['albumtitle'].decode('utf8')
            print "\nNext is: 歌名:",n_title, '歌手:',n_artist, "专辑:", n_albumtitle
        except Exception, e:
            print str(e)
            print "cannot display next song info"
        print_help_msg()

        return


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
        print mp3_file_path
        if not mp3_file_path:
            raise "cannot get mp3 file %s"% song_info
        isload = self.player.load_file(mp3_file_path)
        if isload != 200:
            raise "cannot load this song!"
        self.playing_clip=self.player
        self.playing_clip.play()
        self.set_volume(self.volume)
        self.playing_file_path = mp3_file_path
        #self.set_playing_ui()

    def check_song_list(self):
        while True:
            time.sleep(10)
            if len(self.song_list) <= 1 :
                self.song_list = self.fm.get_song_list(self.current_channel, self.history)
            if len(self.song_list) >= 1:
                #print "pre get mp3 file %s"% self.song_list[0]['url']
                self.get_mp3_file(self.song_list[0])

    def check_song_end(self):
        while True:
            time.sleep(1)
            try:
                if not self.playing_clip.is_alive() and self.playing_clip.status == 'stop':
                    self.play_next()
            except:
                time.sleep(0.5)
                continue


    def quit(self):
        if self.check_song_end_t :
            self.check_song_end_t.kill()
        if self.check_song_list_t :
            self.check_song_list_t.kill()
        if self.check_cache_t:
            self.check_cache_t.kill()

        if self.playing_clip:
            self.playing_clip.quit()

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
        if os.path.isdir(self.tmp_dir):
            filename_list = os.listdir(self.tmp_dir)
            for filename in filename_list:
                file_path = os.path.join(self.tmp_dir, filename)
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
    def change_channel(self, c, isgonow=False):
        c = int( c )
        self.current_channel = c
        if isgonow:
            self.song_list = []
            self.play_next()

    def open_album_url(self):
        if self.playing_song:
            album_link = u'http://music.douban.com' + self.playing_song['album'].decode('utf8')

    def save_2_cache(self):
        if self.playing_file_path:
            if not self.playing_file_path.startswith(self.tmp_dir):
                return 401
            if os.path.isfile( self.playing_file_path ):
                fname = os.path.basename( self.playing_file_path )
                cache_path = os.path.join( self.cache_dir, fname )
                if os.path.isfile( cache_path ):
                    return 202
                import shutil
                try:
                    shutil.copy2(self.playing_file_path, cache_path )
                except Exception, e:
                    print str(e)
                    print "cannot copy to cache dir"
                    return 500
                return 200
        else:
            return 402



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
        self.cf_info = { 'douban':{'username':'', 'password':''},
                'client':{'max_cache_size':CACHE_MAX_SIZE, 'tmp_dir':'/tmp/.doubanfm/', 'local_mp3_dir':SAVE_MP3_DIR, 'cache_dir':SAVE_MP3_DIR},
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
    print " -------------- 'p' for pause/unpase  -----------------------"
    print " -------------- 'c' for change channel ----------------------"
    print " -------------- 'b' for ban the song  -----------------------"
    print " -------------- 'l' for like the song  ----------------------"
    print " -------------- 's' for save the song to cache dir  ---------"
    print " -------------- 'v' for set volume  -------------------------"
    print " -------------- 'q' for quit this program      --------------"
    print " -------------- 'i' for info (playing && this help) ---------"
    print " -------------- 'h' for Help (this HelpMessage)--------------"

if __name__ == "__main__":
    fm = DOUBAN()
    fm.login()
    while not fm.islogined :
        print "try againt to login..."
        fm.login()
    print "logined sucessed!"

    while 1:
        time.sleep(0.1)
        try:
            command = raw_input('>>>')
        except:
            fm.quit()
            break
        if command == 'n':
            fm.play_next()
        elif command == 'p':
            fm.play_pause()
        elif command == 's':
            iscp = fm.save_2_cache()
            if iscp == 200:
                print "ok"
            elif iscp == 401:
                print "is not a tmp file, might be cache file or local file, donot need save to cache dir"
            elif iscp == 402:
                print "tmp file not exist!"
            elif iscp == 500:
                print "failed, unkonwn error when cping"
        elif command == 'b':
            fm.ban_song()
        elif command == 'l':
            fm.like_unlike()
        elif command == 'c':
            print "change channel"
            if not fm.channel_list:
                fm.get_channel_list()
            for channel in fm.channel_list:
                print channel['name'], channel['channel_id']
            c=int(raw_input('pls input the channel id:'))
            isgonow=int(raw_input('is go this channel immediately? 1:0 :'))
            fm.change_channel(c, isgonow)

        elif command == 'q':
            print "quit"
            fm.quit()
            break
        elif command == 'v':
            v = int(raw_input('pls input the volume(0-100)%d:'% fm.volume))
            if v<0 or v > 100:
                print "must 0 < INPUT <100"
                continue
            fm.set_volume(v)
        elif command == 'h':
            print_help_msg()
        elif command == 'i':
            fm.set_playing_ui()
        else:
            pass



