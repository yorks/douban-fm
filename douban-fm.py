#!/usr/bin/env python2
#-*- coding: utf8 -*-
# Author: stuyorks@gmail.com

from PyQt4 import QtCore, QtGui
from dlg_douban_fm_ui import Ui_Dlg_douban
from dlg_setting_ui import Ui_Dlg_setting

import lib_douban_fm
import sys
import threading
import time
import urllib2
import urllib
import os
import ConfigParser

#import mp3player
import audio_player
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

# http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qt.html#Key-enum
KEY_MAP={'ESC':QtCore.Qt.Key_Escape, 'RETURN':QtCore.Qt.Key_Return, 'ENTER':QtCore.Qt.Key_Enter,'BACKSPACE':QtCore.Qt.Key_Backspace,
         'F1':QtCore.Qt.Key_F1, 'F2':QtCore.Qt.Key_F2, 'F3':QtCore.Qt.Key_F3, 'F4':QtCore.Qt.Key_F4, 'F5':QtCore.Qt.Key_F5, 'F6':QtCore.Qt.Key_F6,
         'F7':QtCore.Qt.Key_F7, 'F8':QtCore.Qt.Key_F8, 'F9':QtCore.Qt.Key_F9, 'F10':QtCore.Qt.Key_F10, 'F11':QtCore.Qt.Key_F11, 'F12':QtCore.Qt.Key_F12,
         '0':QtCore.Qt.Key_0, '1':QtCore.Qt.Key_1, '2':QtCore.Qt.Key_2, '3':QtCore.Qt.Key_3, '4':QtCore.Qt.Key_4,
         '5':QtCore.Qt.Key_5, '6':QtCore.Qt.Key_6, '7':QtCore.Qt.Key_7, '8':QtCore.Qt.Key_8, '9':QtCore.Qt.Key_9,
         'A':QtCore.Qt.Key_A, 'B':QtCore.Qt.Key_B, 'C':QtCore.Qt.Key_C, 'D':QtCore.Qt.Key_D, 'E':QtCore.Qt.Key_E, 'F':QtCore.Qt.Key_F, 'G':QtCore.Qt.Key_G,
         'H':QtCore.Qt.Key_H, 'I':QtCore.Qt.Key_I, 'J':QtCore.Qt.Key_J, 'K':QtCore.Qt.Key_K, 'L':QtCore.Qt.Key_L, 'M':QtCore.Qt.Key_M, 'N':QtCore.Qt.Key_N,
         'O':QtCore.Qt.Key_O, 'P':QtCore.Qt.Key_P, 'Q':QtCore.Qt.Key_Q, 'R':QtCore.Qt.Key_R, 'S':QtCore.Qt.Key_S, 'T':QtCore.Qt.Key_T, 'U':QtCore.Qt.Key_U,
         'V':QtCore.Qt.Key_V, 'X':QtCore.Qt.Key_X, 'Y':QtCore.Qt.Key_Y, 'Z':QtCore.Qt.Key_Z,
        }

class DOUBAN_DLG(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Dlg_douban()
        self.center_ui()
        self.ui.setupUi(self)
        #self.setWindowTitle(u'douban.fm   v1.0')

        self.account = ''
        self.password = ''
        self.islogined = False

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

        self.cache_max_size = CACHE_MAX_SIZE

        self.conf = CONFIG()
        self.cf_info = self.conf.get_cf_info()
        #print self.cf_info
        self.parse_conf()
        #print self.liked_list
        #self.conf.set_option('douban','username', 'stuyorks@gmail.com')
        if self.ui.lineEdit_account.text():
            self.ui.lineEdit_password.setFocus()
        if self.ui.lineEdit_password.text():
            self.ui.pB_login.setFocus()

        self.ui.label_singer.setText(u' ')
        self.ui.label_song_name.setText(u' ')
        self.ui.label_album_name.setText(u' ')
        self.ui.label_public_time.setText(u' ')
        self.ui.label_share.setText(u' ')
        self.ui.label_save_song.setText(u' ')
        self.ui.label_google_song.setText(u' ')
        self.current_channel = 0

        self.ui.pB_like_unlike.setText(u'Like')
        self.ui.pB_play_pause.setText(u'Play')
        self.ui.pB_play_pause.setEnabled(False)
        self.ui.pB_next.setEnabled(False)
        self.ui.pB_like_unlike.setEnabled(False)
        self.ui.pB_ban.setEnabled(False)
        self.ui.verticalSlider_volume.setMaximum(self.max_volume)
        self.ui.verticalSlider_volume.setValue( self.max_volume * 0.8 )
        self.ui.pB_album_pic.setFlat(True)
        self.ui.label_share.setOpenExternalLinks(True)
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
        QtCore.QObject.connect( self.ui.pB_ban, QtCore.SIGNAL("clicked()"), self.ban_song)
        QtCore.QObject.connect( self.ui.pB_setting, QtCore.SIGNAL("clicked()"), self.setting)
        QtCore.QObject.connect( self.ui.verticalSlider_volume, QtCore.SIGNAL("sliderReleased()"), self.set_volume)
        QtCore.QObject.connect( self.ui.cB_channel, QtCore.SIGNAL("currentIndexChanged(int)"), self.set_current_channel )
        QtCore.QObject.connect( self.ui.cB_channel, QtCore.SIGNAL("activated(int)"), self.combox_active )
        QtCore.QObject.connect( self.ui.pB_album_pic, QtCore.SIGNAL("clicked()"), self.open_album_url )

        QtCore.QObject.connect( self, QtCore.SIGNAL("new_play()"), self.set_playing_ui ) # 开始播放下一首歌曲时
        QtCore.QObject.connect( self, QtCore.SIGNAL("song_end()"), self.need_2_next ) # 当前歌曲播放完毕时

        # shortcut
        #self.sc_enter = QtGui.QShortcut(self)
        #self.sc_enter.setKey(QtGui.QKeySequence( QtCore.Qt.Key_Return))
        ##self.enter_sc.setContext(QtCore.Qt.WindowShortcut)
        #self.sc_enter.activated.connect(self.login)

        #self.sc_esc = QtGui.QShortcut(self)
        #self.sc_esc.setKey( QtGui.QKeySequence(QtCore.Qt.Key_Escape) )
        #self.sc_esc.activated.connect(self.closeEvent(QtCore.QEvent(QtCore.QEvent(QtCore.QEvent.Close))))


    def center_ui(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move( ( screen.width() - size.width() ) / 2, ( screen.height() - size.height() ) / 2 )

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
        if not self.account or not self.password:
            QtGui.QMessageBox.information(None, u"登录失败", u'帐号和密码不能为空', u"确定")
            return
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
                self.ui.lineEdit_v_code.setFocus()
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
            self.islogined = True
            self.set_channel_2_cm()
            self.ui.pB_login.setEnabled(False)
            self.ui.pB_play_pause.setEnabled(True)
            self.ui.pB_play_pause.setFocus()
            self.ui.pB_next.setEnabled(True)
            self.ui.pB_like_unlike.setEnabled(True)
            self.ui.pB_ban.setEnabled(True)
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

        sid    = self.playing_song['sid'].decode('utf8')
        ssid    = self.playing_song['ssid'].decode('utf8')
        title  = self.playing_song['title'].decode('utf8')
        artist = self.playing_song['artist'].decode('utf8')
        albumtitle = self.playing_song['albumtitle'].decode('utf8')
        public_time = self.playing_song['public_time'].decode('utf8')
        pic_url = self.playing_song['picture'].decode('utf8')
        try:
            print sid, title, atrist
        except:
            pass

        album_link = 'http://music.douban.com' + self.playing_song['album'].decode('utf8')
        google_song_link = 'http://www.google.cn/music/search?q='+ title

        s_song_url=u'http://douban.fm/?start=%sg%sg0&cid=0'% (sid, ssid)
        s_title=u'分享 %s 的 《%s》(来自Douban-FM #%s 频道)'% (artist, title, self.ui.cB_channel.currentText())
        try:
            s_title = urllib.quote(s_title.encode('utf8'))
        except:
            pass
        s_pic = pic_url.replace('/mpic/', '/lpic/')

        share_url=u'http://v.t.sina.com.cn/share/share.php?appkey=3163308509&url='+s_song_url+u'&title='+s_title+u'&source=&sourceUrl=&content=utf-8&pic='+s_pic
        #print share_url
        share_html = u'<a href="%s">分享</a>'% share_url

        save_song_html = u'<a href="%s">下载</a>'% self.playing_song['url']
        google_song_html = u'<a href="%s">Google It</a>'% google_song_link
        #print google_song_html

        self.setWindowTitle(u'douban-fm   '+title+u' - '+artist)
        self.ui.label_singer.setText(u'歌手:'+artist)
        self.ui.label_singer.setToolTip(artist)
        self.ui.label_song_name.setText(u'歌名:'+title)
        self.ui.label_song_name.setToolTip(title)
        self.ui.label_album_name.setText(u'专辑:'+albumtitle)
        self.ui.label_album_name.setToolTip(albumtitle)
        self.ui.label_public_time.setText(u'发行时间:'+ public_time)
        self.ui.label_public_time.setToolTip( public_time )
        self.ui.label_share.setVisible(True)
        self.ui.label_save_song.setVisible(True)
        self.ui.label_google_song.setVisible(True)
        self.ui.label_share.setText(share_html)
        self.ui.label_share.setToolTip(u'分享这首歌到微博')
        self.ui.label_google_song.setText(google_song_html)
        self.ui.label_google_song.setToolTip(u'到Google搜索该歌曲')
        self.ui.label_save_song.setText(save_song_html)
        self.ui.label_save_song.setToolTip(u'从豆瓣下载这首歌曲')

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
        #pixmap = QtGui.QPixmap(album_pic_path)
        #self.ui.label_album_pic.setPixmap(pixmap)
        album_ico = QtGui.QIcon(album_pic_path)
        self.ui.pB_album_pic.setIconSize(QtCore.QSize(106,140))
        self.ui.pB_album_pic.setIcon(album_ico)
        self.ui.pB_album_pic.setToolTip(u'到豆瓣看看该专辑')
        next_song_htm=u''
        if self.song_list:
            next_song=self.song_list[0]
            try:
                next_song_title=next_song['title'].decode('utf8')
                next_song_artist=next_song['artist'].decode('utf8')
            except:
                pass
            next_song_htm=u'下一首: '+ next_song_title + u' - '+ next_song_artist
        self.ui.pB_next.setToolTip(next_song_htm)

        self.user_record = self.fm.get_user_record()
        user_record_htm=u'累计<font color="blue"> %d </font>首, 红心<font color="red"> %s </font> 首, 不再听 %s 首'% ( self.user_record['played'],
                self.user_record['liked'], self.user_record['banned'] )
        self.ui.label_status.setText( user_record_htm )
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
        self.ui.pB_play_pause.setFocus()

    def combox_active(self, seq_id):
        self.ui.pB_play_pause.setFocus()

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
        self.quit()
        #self.close()
        print event
        event.accept()

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
                    if self.playing_clip and self.playing_clip.filepath == cache['path']:
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

    def open_album_url(self):
        self.ui.pB_play_pause.setFocus()
        if self.playing_song:
            album_link = u'http://music.douban.com' + self.playing_song['album'].decode('utf8')
            QtGui.QDesktopServices.openUrl( QtCore.QUrl(album_link) )

    def keyPressEvent(self, event):
        key = event.key()
        for v in self.cf_info['shortcut'].values():
            if v not in KEY_MAP.keys():
                QtGui.QMessageBox.critical(None, u"ERROR", u'按键" %s "在配置中有误，不支持该按键'% v, u"确定")
                return
        if key == KEY_MAP[ self.cf_info['shortcut']['login'] ]:
            if not self.islogined:
                self.login()
        elif key == KEY_MAP[ self.cf_info['shortcut']['quit'] ]:
            self.quit()
        elif key == KEY_MAP[ self.cf_info['shortcut']['setting'] ]:
            self.setting()
        elif key == KEY_MAP[ self.cf_info['shortcut']['next'] ]:
            if self.playing_song:
                self.play_next()
        elif key == KEY_MAP[ self.cf_info['shortcut']['play_pause'] ]:
            if self.playing_song:
                self.play_pause()
        elif key == KEY_MAP[ self.cf_info['shortcut']['like'] ]:
            if self.playing_song:
                self.like_unlike()
        elif key == KEY_MAP[ self.cf_info['shortcut']['ban'] ]:
            if self.playing_song:
                self.ban_song()
        else:
            print key

    def setting(self):
        setting_dlg = SETTING_DLG(self.cf_info)
        if setting_dlg.exec_():
            self.cf_info = self.conf.get_cf_info(force_new=True)

class SETTING_DLG(QtGui.QDialog):
    def __init__(self, config_info, parent=None):
        self.config_info = config_info
        super(SETTING_DLG, self).__init__(parent)
        self.ui = Ui_Dlg_setting()
        self.ui.setupUi(self)
        self.set_config_2_ui()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowSystemMenuHint)
        self.dragPosition=None
        self.setWindowOpacity(1)

        QtCore.QObject.connect( self.ui.pushButton_set, QtCore.SIGNAL("clicked()"), self.save_config)
        QtCore.QObject.connect( self.ui.pushButton_reset, QtCore.SIGNAL("clicked()"), self.set_config_2_ui)
        QtCore.QObject.connect( self.ui.pushButton_cancle, QtCore.SIGNAL("clicked()"), self.cancle)

    def set_config_2_ui(self):
        db_username = self.config_info['douban']['username']
        db_password = self.config_info['douban']['password']
        real_password = ''
        if db_password:
            real_password = secure_str.decode(db_password)
        cache_size = float(self.config_info['client']['max_cache_size']) / 1024 / 1024

        # 'shortcut':{'login':'ENTER','quit':'ESC', 'play_pause':'P', 'next':'N', 'like':'L', 'ban':'B', 'settting':'S' }
        login_key = self.config_info['shortcut']['login']
        quit_key = self.config_info['shortcut']['quit']
        play_pause_key = self.config_info['shortcut']['play_pause']
        next_key = self.config_info['shortcut']['next']
        like_key = self.config_info['shortcut']['like']
        ban_key = self.config_info['shortcut']['ban']
        setting_key = self.config_info['shortcut']['setting']


        self.ui.lineEdit_username.setText(db_username)
        self.ui.lineEdit_password.setText(real_password)
        if real_password:
            self.ui.checkBox_remember.setChecked(True)
        self.ui.doubleSpinBox_cache.setValue( cache_size )
        self.ui.lineEdit_login.setText(login_key)
        self.ui.lineEdit_quit.setText(quit_key)
        self.ui.lineEdit_play_pause.setText(play_pause_key)
        self.ui.lineEdit_next.setText(next_key)
        self.ui.lineEdit_like.setText(like_key)
        self.ui.lineEdit_ban.setText(ban_key)
        self.ui.lineEdit_setting.setText(setting_key)


    def get_config_info_from_ui(self):
        db_username = ''
        db_secure_password = ''
        if self.ui.checkBox_remember.isChecked():
            db_username = str( self.ui.lineEdit_username.text() )
            db_real_password = str( self.ui.lineEdit_password.text() )
            db_secure_password = secure_str.encode(db_real_password)
        cache_size = self.ui.doubleSpinBox_cache.value() * 1024 * 1024
        login_key = str( self.ui.lineEdit_login.text() ).upper()
        quit_key = str( self.ui.lineEdit_quit.text() ).upper()
        play_pause_key = str( self.ui.lineEdit_play_pause.text() ).upper()
        next_key = str( self.ui.lineEdit_next.text() ).upper()
        like_key = str( self.ui.lineEdit_like.text() ).upper()
        ban_key = str( self.ui.lineEdit_ban.text() ).upper()
        setting_key = str( self.ui.lineEdit_setting.text() ).upper()
        set_key_list=[login_key, quit_key, play_pause_key, next_key, like_key, ban_key]
        uniq_list=[]
        for key in set_key_list:
            if key not in uniq_list:
                uniq_list.append(key)

            else:
                QtGui.QMessageBox.critical(None, u"ERROR", u'按键" %s "设置重复了'% key, u"确定")
                return False

        if login_key not in KEY_MAP.keys():
            QtGui.QMessageBox.critical(None, u"ERROR", u'登录键设置错误或者不支持该按键" %s "'% login_key, u"确定")
            return False
        if quit_key not in KEY_MAP.keys():
            QtGui.QMessageBox.critical(None, u"ERROR", u'退出键设置错误或者不支持该按键" %s "'% quit_key, u"确定")
            return False
        if play_pause_key not in KEY_MAP.keys():
            QtGui.QMessageBox.critical(None, u"ERROR", u'播放/暂停键设置错误或者不支持该按键" %s "'% play_pause_key, u"确定")
            return False
        if next_key not in KEY_MAP.keys():
            QtGui.QMessageBox.critical(None, u"ERROR", u'下一首键设置错误或者不支持该按键" %s "'% next_key, u"确定")
            return False
        if like_key not in KEY_MAP.keys():
            QtGui.QMessageBox.critical(None, u"ERROR", u'加红/不加红键设置错误或者不支持该按键" %s "'% like_key, u"确定")
            return False
        if ban_key not in KEY_MAP.keys():
            QtGui.QMessageBox.critical(None, u"ERROR", u'不再收听键设置错误或者不支持该按键" %s "'% ban_key, u"确定")
            return False
        if setting_key not in KEY_MAP.keys():
            QtGui.QMessageBox.critical(None, u"ERROR", u'设置键设置错误或者不支持该按键" %s "'% setting_key, u"确定")
            return False
        import copy
        ui_config_info = copy.deepcopy(self.config_info)
        ui_config_info['douban']['username'] = db_username
        ui_config_info['douban']['password'] = db_secure_password
        ui_config_info['client']['max_cache_size'] = str(cache_size)
        ui_config_info['shortcut']['login'] = login_key
        ui_config_info['shortcut']['quit'] = quit_key
        ui_config_info['shortcut']['play_pause'] = play_pause_key
        ui_config_info['shortcut']['next'] = next_key
        ui_config_info['shortcut']['like'] = like_key
        ui_config_info['shortcut']['ban'] = ban_key
        ui_config_info['shortcut']['setting'] = setting_key
        return ui_config_info

    def save_config(self):
        ui_config_info = self.get_config_info_from_ui()
        if not ui_config_info:
            return

        print ui_config_info
        print "========="
        print self.config_info
        config = CONFIG()
        has_failed=False
        for section in self.config_info.keys():
            for option in self.config_info[section].keys():
                value_old = self.config_info[section][option]
                value_new = ui_config_info[section][option]
                if value_new != value_old:
                    print value_new, value_old
                    if not config.set_option( section, option, value_new):
                        has_failed=True
                        QtGui.QMessageBox.critical(None, u"ERROR", u' 保存" %s "出错!'% value_new, u"确定")
        if not has_failed:
            QtGui.QMessageBox.information(None, u"设置成功", u'设置成功', u"确定")
        self.cancle()

    def closeEvent(self, event):
        self.accept()

    def cancle(self):
        self.accept()

    def mousePressEvent(self,event):
        print "mouser"
        print  event.button()
        if event.button() == QtCore.Qt.LeftButton:
            self.dragPosition=event.globalPos()-self.frameGeometry().topLeft()
            event.accept()
    def mouseMoveEvent(self,event):
        if event.buttons() & QtCore.Qt.LeftButton:
            self.move(event.globalPos()-self.dragPosition)
            event.accept()


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



if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    douban_dlg = DOUBAN_DLG()
    douban_dlg.show()
    sys.exit(app.exec_())
