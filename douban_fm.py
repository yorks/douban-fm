#!/usr/bin/env python2
#-*- coding: utf8 -*-
# Author: stuyorks@gmail.com

from PyQt4 import QtCore, QtGui
from dlg_douban_fm_ui import Ui_Dlg_douban

import lib_douban_fm
import sys
import threading
import time
import urllib2
import os

#import mp3player
import audio_player
import images_rc

DOUBAN_HOME=os.path.expanduser('~/.douban.fm/')
SAVE_MP3_DIR=os.path.expanduser('~/.douban.fm/mp3/')
ALBUM_PIC_DIR=os.path.expanduser('~/.douban.fm/album_pic')
CONF_FILE_PATH=os.path.join(DOUBAN_HOME, '.conf')
LIKED_LIST_FILE_PATH=os.path.join(DOUBAN_HOME, '.liked')

if not os.path.exists(SAVE_MP3_DIR):
    os.makedirs(SAVE_MP3_DIR)
if not os.path.exists(ALBUM_PIC_DIR):
    os.makedirs(ALBUM_PIC_DIR)

CACHE_MAX_SIZE=1 * 1024 * 1024 * 1024 # 1G

class DOUBAN_DLG(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Dlg_douban()
        self.center_ui()
        self.ui.setupUi(self)
        #self.setWindowTitle(u'douban.fm   v1.0')

        self.account = ''
        self.password = ''

        self.player = audio_player.AUDIO_PLAYER()
        self.playing_clip = None
        self.playing_song = None # song_inf dict
        self.song_list = []
        self.channel_list = []
        self.history = []
        self.user_record={}
        self.check_song_list_t = None
        self.check_song_end_t = None
        self.check_cache_t = None
        self.max_volume = 65535
        self.fm = None

        self.like = False
        self.liked_list = []
        self.banned_list = []

        self.parse_conf()
        #print self.liked_list

        self.ui.label_singer.setText(u' ')
        self.ui.label_song_name.setText(u' ')
        self.ui.label_album_name.setText(u' ')
        self.ui.label_public_time.setText(u' ')
        self.ui.label_album_detail.setText(u' ')
        self.ui.label_save_song.setText(u' ')
        self.ui.label_google_song.setText(u' ')
        self.current_channel = 0

        self.ui.pB_like_unlike.setText(u'Like')
        self.ui.pB_play_pause.setText(u'Play')
        self.ui.pB_play_pause.setEnabled(False)
        self.ui.pB_next.setEnabled(False)
        self.ui.pB_like_unlike.setEnabled(False)
        self.ui.verticalSlider_volume.setMaximum(self.max_volume)
        self.ui.verticalSlider_volume.setValue( self.max_volume * 0.8 )
        self.ui.label_album_detail.setOpenExternalLinks(True)
        self.ui.label_save_song.setOpenExternalLinks(True)
        self.ui.label_google_song.setOpenExternalLinks(True)
        self.ui.label_save_song.setVisible(False)
        self.ui.label_google_song.setVisible(False)
        self.ui.lineEdit_v_code.setVisible(False)
        self.ui.label_v_code_pic.setVisible(False)
        self.ui.label_status.setVisible(False)
        #self.ui.groupBox.setVisible(False)

        QtCore.QObject.connect( self.ui.pB_login, QtCore.SIGNAL("clicked()"), self.login )
        QtCore.QObject.connect( self.ui.pB_play_pause, QtCore.SIGNAL("clicked()"), self.play_pause )
        QtCore.QObject.connect( self.ui.pB_next, QtCore.SIGNAL("clicked()"), self.play_next )
        QtCore.QObject.connect( self.ui.pB_like_unlike, QtCore.SIGNAL("clicked()"), self.like_unlike)
        QtCore.QObject.connect( self.ui.verticalSlider_volume, QtCore.SIGNAL("sliderReleased()"), self.set_volume)
        QtCore.QObject.connect( self.ui.cB_channel, QtCore.SIGNAL("currentIndexChanged(int)"), self.set_current_channel )

        QtCore.QObject.connect( self, QtCore.SIGNAL("new_play()"), self.set_playing_ui ) # 开始播放下一首歌曲时
        QtCore.QObject.connect( self, QtCore.SIGNAL("song_end()"), self.need_2_next ) # 当前歌曲播放完毕时

    def center_ui(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move( ( screen.width() - size.width() ) / 2, ( screen.height() - size.height() ) / 2 )

    def parse_conf(self):
        if os.path.isfile(CONF_FILE_PATH):
            fp = open(CONF_FILE_PATH, 'r')
            content = fp.readlines()
            fp.close()
            account = content[0].replace(os.linesep, '')
            password = content[1].replace(os.linesep, '')
            #print account, password
            self.ui.lineEdit_account.setText(account)
            self.ui.lineEdit_password.setText(password)
        if os.path.isfile(LIKED_LIST_FILE_PATH):
            fp = open(LIKED_LIST_FILE_PATH, 'r')
            content = fp.read()
            fp.close()
            self.liked_list = content.split(r'|')


    def login(self):
        self.account = str(self.ui.lineEdit_account.text())
        self.password = str(self.ui.lineEdit_password.text())
        self.ui.pB_login.setText(u'登录中...')
        self.ui.pB_login.setEnabled(False)
        if not self.fm:
            self.fm = lib_douban_fm.DOUBAN_FM()
        if self.fm.captcha_id:
            verification_code = str(self.ui.lineEdit_v_code.text())
            is_login = self.fm.login( self.account, self.password, verification_code )
        else:
            is_login = self.fm.login(self.account, self.password)
        if is_login.startswith(r'http://'):
            captcha_id = self.fm.get_verification_img()
            if captcha_id:
                self.ui.label_v_code_pic.setVisible(True)
                self.ui.lineEdit_v_code.setVisible(True)
                img_path = os.path.expanduser('./douban_verification_img.jpg')
                pixmap = QtGui.QPixmap(img_path)
                self.ui.label_v_code_pic.setPixmap(pixmap)
                QtGui.QMessageBox.information(None, u"登录失败", u'请输入验证码', u"确定")
                self.ui.pB_login.setEnabled(True)
                self.ui.pB_login.setText(u'登录')
                return 0


            else:
                QtGui.QMessageBox.information(None, u"登录失败", u'验证码获取不了', u"确定")
                self.ui.pB_login.setEnabled(True)
                self.ui.pB_login.setText(u'登录')
                return 0


        if is_login and not is_login.startswith(r'http://'):
            self.ui.pB_login.setText(u'登录成功')
            self.set_channel_2_cm()
            self.ui.pB_login.setEnabled(False)
            self.ui.pB_play_pause.setEnabled(True)
            self.ui.pB_next.setEnabled(True)
            self.ui.pB_like_unlike.setEnabled(True)
            self.ui.lineEdit_account.setReadOnly(True)
            self.ui.lineEdit_account.setEnabled(False)
            self.ui.lineEdit_password.setReadOnly(True)
            self.ui.lineEdit_password.setEnabled(False)
            self.ui.lineEdit_v_code.setVisible(False)
            self.ui.label_v_code_pic.setVisible(False)

            self.play_pause()
        else:
            QtGui.QMessageBox.information(None, u"登录失败", u'登录失败', u"确定")
            self.ui.pB_login.setEnabled(True)
            self.ui.pB_login.setText(u'登录')

    def play_pause(self):
        """ play_pause   PAUSE / UNPAUSE / PLAY(first login) """
        if self.playing_clip: # PAUSE / UNPAUSE
            if not self.playing_clip.is_playing() and not self.playing_clip.is_paused():
                self.play_next()
            elif self.playing_clip.is_paused():
                self.playing_clip.unpause()
                self.ui.pB_play_pause.setText(u'Pause')
            elif self.playing_clip.is_playing():
                self.playing_clip.pause()
                self.ui.pB_play_pause.setText(u'Play')
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
            if self.playing_clip.is_playing() or self.playing_clip.is_paused():
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
            QtGui.QMessageBox.information(None, u"错误", u'不能播放该歌曲', u"确定")
            sys.exit(1)

        del self.song_list[0]
        self.emit( QtCore.SIGNAL("new_play()") )

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
            os.unlink(mp3_file_path)
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

    def set_volume(self):
        value = self.ui.verticalSlider_volume.value()
        #print value
        if self.playing_clip:
            self.playing_clip.set_volume(value)
        else:
            pass

    def like_unlike(self):
        if not self.like:
            self.fm.like_song(self.playing_song['sid'])
            self.like = True
            self.ui.pB_like_unlike.setText(u'Unlike')
            if self.playing_song['sid'] not in self.liked_list:
                self.liked_list.append( self.playing_song['sid'] )
        else:
            self.fm.unlike_song(self.playing_song['sid'])
            self.ui.pB_like_unlike.setText(u'Like')
            self.like = False
            if self.playing_song['sid'] in self.liked_list:
                self.liked_list.remove( self.playing_song['sid'] )

    def set_playing_ui(self):
        #print self.playing_song
        try:
            print self.playing_song['sid'].decode('utf8'),
            print self.playing_song['artist'].decode('utf8'),
            print self.playing_song['title'].decode('utf8'),
            print self.playing_song['albumtitle'].decode('utf8')
        except:
            pass


        title=self.playing_song['title'].decode('utf8')
        artist = self.playing_song['artist'].decode('utf8')
        albumtitle = self.playing_song['albumtitle'].decode('utf8')
        public_time = self.playing_song['public_time'].decode('utf8')
        album_link = 'http://music.douban.com' + self.playing_song['album'].decode('utf8')
        google_song_link = 'http://www.google.cn/music/search?q='+ self.playing_song['title'].decode('utf8')

        detail_html = u'<a href="%s">专辑详情</a>'% album_link
        save_song_html = u'<a href="%s">下载</a>'% self.playing_song['url']
        google_song_html = u'<a href="%s">Google It</a>'% google_song_link
        #print google_song_html

        self.ui.label_singer.setText(u'歌手:'+artist)
        self.ui.label_song_name.setText(u'歌名:'+title)
        self.ui.label_album_name.setText(u'专辑:'+albumtitle)
        self.ui.label_public_time.setText(u'发行时间:'+ public_time)
        self.ui.label_album_detail.setVisible(True)
        self.ui.label_save_song.setVisible(True)
        self.ui.label_google_song.setVisible(True)
        self.ui.label_album_detail.setText(detail_html)
        self.ui.label_google_song.setText(google_song_html)
        self.ui.label_save_song.setText(save_song_html)

        self.ui.pB_play_pause.setText(u'Pause')

        if self.playing_song['like'] == 1 :
            self.ui.pB_like_unlike.setText(u'Unlike')
            self.like = True
            if self.playing_song['sid'] not in self.liked_list:
                self.liked_list.append( self.playing_song['sid'] )
        else:
            self.ui.pB_like_unlike.setText(u'Like')
            self.like = False

        album_pic_path = self.get_album_pic(self.playing_song)
        if not album_pic_path:
            album_pic_path = u':/fm.jpg'
        pixmap = QtGui.QPixmap(album_pic_path)
        self.ui.label_album_pic.setPixmap(pixmap)
        self.user_record = self.fm.get_user_record()
        user_record_htm=u'累计<font color="blue"> %d </font>首, 红心<font color="red"> %s </font> 首, 不再听 %s 首'% ( self.user_record['played'],
                self.user_record['liked'], self.user_record['banned'] )
        self.ui.label_status.setText(user_record_htm)
        self.ui.label_status.setVisible(True)


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

    def set_channel_2_cm(self):
        self.channel_list = self.fm.get_channel_list()
        #print len(self.channel_list)
        for channel in self.channel_list:
            seq_id = int(channel['seq_id'])
            channel_id = int(channel['channel_id'])
            channel_name = channel['name'].decode('utf8')
            self.ui.cB_channel.insertItem(seq_id, channel_name)
            if channel_id == self.current_channel :
                self.ui.cB_channel.setCurrentIndex(seq_id)

    def set_current_channel(self, seq_id):
        for channel in self.channel_list:
            if channel['seq_id'] == seq_id :
                self.current_channel = channel['channel_id']
                #print seq_id
                print self.current_channel

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
            self.emit( QtCore.SIGNAL("song_end()") )

    def closeEvent(self, event):
        if self.check_song_end_t :
            self.check_song_end_t.kill()
        if self.check_song_list_t :
            self.check_song_list_t.kill()
        if self.check_cache_t:
            self.check_cache_t.kill()

        if self.playing_clip:
            self.playing_clip.stop()
        try:
            self.save_liked_list()
        except:
            pass

        #self.close()
        event.accept()
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
                    if file_info['size'] == 0:
                        os.unlink(file_path)
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
        cache_info = self.get_cache_info()
        delta_size = CACHE_MAX_SIZE - cache_info['size']
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
                    if self.playing_clip and self.playing_clip.filepath == cache['path']:
                        continue
                    print "clean cache:",
                    print cache['path']
                    os.unlink(cache['path'])
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
    def __init__():
        pass


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    douban_dlg = DOUBAN_DLG()
    douban_dlg.show()
    sys.exit(app.exec_())
