# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlg_douban_fm.ui'
#
# Created: Sun Jul  8 02:15:45 2012
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Dlg_douban(object):
    def setupUi(self, Dlg_douban):
        Dlg_douban.setObjectName(_fromUtf8("Dlg_douban"))
        Dlg_douban.resize(497, 268)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/fm.jpg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dlg_douban.setWindowIcon(icon)
        self.lable_auth = QtGui.QLabel(Dlg_douban)
        self.lable_auth.setGeometry(QtCore.QRect(310, 251, 171, 20))
        self.lable_auth.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lable_auth.setObjectName(_fromUtf8("lable_auth"))
        self.groupBox = QtGui.QGroupBox(Dlg_douban)
        self.groupBox.setGeometry(QtCore.QRect(310, 10, 171, 161))
        self.groupBox.setStyleSheet(_fromUtf8("QGroupBox {\n"
"     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n"
"                                       stop: 0 #E0E0E0, stop: 1 #FFFFFF);\n"
"     border: 2px solid gray;\n"
"     border-radius: 5px;\n"
"     margin-top: 1ex; /* leave space at the top for the title */\n"
" }\n"
"QGroupBox::title {\n"
"     subcontrol-origin: margin;\n"
"     subcontrol-position: top center; /* position at the top center */\n"
"     padding: 0 3px;\n"
" }"))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.lineEdit_account = QtGui.QLineEdit(self.groupBox)
        self.lineEdit_account.setGeometry(QtCore.QRect(18, 30, 135, 31))
        self.lineEdit_account.setObjectName(_fromUtf8("lineEdit_account"))
        self.lineEdit_password = QtGui.QLineEdit(self.groupBox)
        self.lineEdit_password.setGeometry(QtCore.QRect(18, 70, 135, 31))
        self.lineEdit_password.setEchoMode(QtGui.QLineEdit.Password)
        self.lineEdit_password.setObjectName(_fromUtf8("lineEdit_password"))
        self.pB_login = QtGui.QPushButton(self.groupBox)
        self.pB_login.setGeometry(QtCore.QRect(50, 110, 75, 31))
        self.pB_login.setObjectName(_fromUtf8("pB_login"))
        self.groupBox_2 = QtGui.QGroupBox(Dlg_douban)
        self.groupBox_2.setGeometry(QtCore.QRect(10, 180, 471, 61))
        self.groupBox_2.setStyleSheet(_fromUtf8("QGroupBox {\n"
"     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n"
"                                       stop: 0 #E0E0E0, stop: 1 #FFFFFF);\n"
"     border: 2px solid gray;\n"
"     border-radius: 5px;\n"
"     margin-top: 1ex; /* leave space at the top for the title */\n"
" }\n"
"QGroupBox::title {\n"
"     subcontrol-origin: margin;\n"
"     subcontrol-position: top center; /* position at the top center */\n"
"     padding: 0 3px;\n"
"     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n"
"                                       stop: 0 #CCCCCC, stop: 1 #FFFFFF);\n"
" }"))
        self.groupBox_2.setTitle(_fromUtf8(""))
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.pB_play_pause = QtGui.QPushButton(self.groupBox_2)
        self.pB_play_pause.setGeometry(QtCore.QRect(15, 20, 60, 31))
        self.pB_play_pause.setObjectName(_fromUtf8("pB_play_pause"))
        self.pB_next = QtGui.QPushButton(self.groupBox_2)
        self.pB_next.setGeometry(QtCore.QRect(90, 20, 60, 31))
        self.pB_next.setObjectName(_fromUtf8("pB_next"))
        self.pB_like_unlike = QtGui.QPushButton(self.groupBox_2)
        self.pB_like_unlike.setGeometry(QtCore.QRect(165, 20, 60, 31))
        self.pB_like_unlike.setObjectName(_fromUtf8("pB_like_unlike"))
        self.cB_channel = QtGui.QComboBox(self.groupBox_2)
        self.cB_channel.setGeometry(QtCore.QRect(345, 20, 81, 31))
        self.cB_channel.setObjectName(_fromUtf8("cB_channel"))
        self.verticalSlider_volume = QtGui.QSlider(self.groupBox_2)
        self.verticalSlider_volume.setGeometry(QtCore.QRect(435, 10, 21, 41))
        self.verticalSlider_volume.setMaximum(65535)
        self.verticalSlider_volume.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider_volume.setObjectName(_fromUtf8("verticalSlider_volume"))
        self.pB_ban = QtGui.QPushButton(self.groupBox_2)
        self.pB_ban.setGeometry(QtCore.QRect(240, 20, 41, 31))
        self.pB_ban.setStatusTip(_fromUtf8(""))
        self.pB_ban.setObjectName(_fromUtf8("pB_ban"))
        self.pB_setting = QtGui.QPushButton(self.groupBox_2)
        self.pB_setting.setGeometry(QtCore.QRect(290, 20, 45, 31))
        self.pB_setting.setStatusTip(_fromUtf8(""))
        self.pB_setting.setObjectName(_fromUtf8("pB_setting"))
        self.groupBox_3 = QtGui.QGroupBox(Dlg_douban)
        self.groupBox_3.setGeometry(QtCore.QRect(10, 10, 291, 161))
        self.groupBox_3.setStyleSheet(_fromUtf8("QGroupBox {\n"
"     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n"
"                                       stop: 0 #E0E0E0, stop: 1 #FFFFFF);\n"
"     border: 2px solid gray;\n"
"     border-radius: 5px;\n"
"     margin-top: 1ex; /* leave space at the top for the title */\n"
" }\n"
"QGroupBox::title {\n"
"     subcontrol-origin: margin;\n"
"     subcontrol-position: top center; /* position at the top center */\n"
"     padding: 0 3px;\n"
"     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n"
"                                       stop: 0 #CCCCCC, stop: 1 #FFFFFF);\n"
" }"))
        self.groupBox_3.setTitle(_fromUtf8(""))
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.label_album_pic = QtGui.QLabel(self.groupBox_3)
        self.label_album_pic.setGeometry(QtCore.QRect(10, 10, 106, 139))
        self.label_album_pic.setText(_fromUtf8(""))
        self.label_album_pic.setObjectName(_fromUtf8("label_album_pic"))
        self.label_public_time = QtGui.QLabel(self.groupBox_3)
        self.label_public_time.setGeometry(QtCore.QRect(130, 110, 151, 16))
        self.label_public_time.setObjectName(_fromUtf8("label_public_time"))
        self.label_album_name = QtGui.QLabel(self.groupBox_3)
        self.label_album_name.setGeometry(QtCore.QRect(130, 80, 151, 16))
        self.label_album_name.setObjectName(_fromUtf8("label_album_name"))
        self.label_song_name = QtGui.QLabel(self.groupBox_3)
        self.label_song_name.setGeometry(QtCore.QRect(130, 50, 151, 16))
        self.label_song_name.setObjectName(_fromUtf8("label_song_name"))
        self.label_singer = QtGui.QLabel(self.groupBox_3)
        self.label_singer.setGeometry(QtCore.QRect(130, 20, 151, 16))
        self.label_singer.setObjectName(_fromUtf8("label_singer"))
        self.label_album_detail = QtGui.QLabel(self.groupBox_3)
        self.label_album_detail.setGeometry(QtCore.QRect(130, 140, 51, 16))
        self.label_album_detail.setObjectName(_fromUtf8("label_album_detail"))
        self.label_save_song = QtGui.QLabel(self.groupBox_3)
        self.label_save_song.setGeometry(QtCore.QRect(190, 140, 31, 16))
        self.label_save_song.setObjectName(_fromUtf8("label_save_song"))
        self.label_google_song = QtGui.QLabel(self.groupBox_3)
        self.label_google_song.setGeometry(QtCore.QRect(230, 140, 61, 16))
        self.label_google_song.setObjectName(_fromUtf8("label_google_song"))
        self.lineEdit_v_code = QtGui.QLineEdit(self.groupBox_3)
        self.lineEdit_v_code.setGeometry(QtCore.QRect(90, 80, 131, 31))
        self.lineEdit_v_code.setEchoMode(QtGui.QLineEdit.Normal)
        self.lineEdit_v_code.setObjectName(_fromUtf8("lineEdit_v_code"))
        self.label_v_code_pic = QtGui.QLabel(self.groupBox_3)
        self.label_v_code_pic.setGeometry(QtCore.QRect(20, 30, 250, 40))
        self.label_v_code_pic.setText(_fromUtf8(""))
        self.label_v_code_pic.setObjectName(_fromUtf8("label_v_code_pic"))
        self.label_status = QtGui.QLabel(Dlg_douban)
        self.label_status.setGeometry(QtCore.QRect(10, 250, 331, 20))
        self.label_status.setTextFormat(QtCore.Qt.RichText)
        self.label_status.setObjectName(_fromUtf8("label_status"))

        self.retranslateUi(Dlg_douban)
        QtCore.QMetaObject.connectSlotsByName(Dlg_douban)

    def retranslateUi(self, Dlg_douban):
        Dlg_douban.setWindowTitle(QtGui.QApplication.translate("Dlg_douban", "douban.fm", None, QtGui.QApplication.UnicodeUTF8))
        self.lable_auth.setText(QtGui.QApplication.translate("Dlg_douban", "<html><head/><body><p><span style=\" font-size:7pt;\">Author: </span><a href=\"mailto:stuyorks@gmail.com\"><span style=\" font-size:7pt; text-decoration: underline; color:#0000ff;\">stuyorks@gmail.com</span></a></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("Dlg_douban", "登录豆瓣", None, QtGui.QApplication.UnicodeUTF8))
        self.pB_login.setText(QtGui.QApplication.translate("Dlg_douban", "Login", None, QtGui.QApplication.UnicodeUTF8))
        self.pB_play_pause.setText(QtGui.QApplication.translate("Dlg_douban", "Play/Pause", None, QtGui.QApplication.UnicodeUTF8))
        self.pB_next.setText(QtGui.QApplication.translate("Dlg_douban", "Next", None, QtGui.QApplication.UnicodeUTF8))
        self.pB_like_unlike.setText(QtGui.QApplication.translate("Dlg_douban", "Like/Unlike", None, QtGui.QApplication.UnicodeUTF8))
        self.pB_ban.setToolTip(QtGui.QApplication.translate("Dlg_douban", "<html><head/><body><p>不再收听这首歌</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.pB_ban.setWhatsThis(QtGui.QApplication.translate("Dlg_douban", "<html><head/><body><p>不再收听这首歌</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.pB_ban.setText(QtGui.QApplication.translate("Dlg_douban", "Ban", None, QtGui.QApplication.UnicodeUTF8))
        self.pB_setting.setToolTip(QtGui.QApplication.translate("Dlg_douban", "<html><head/><body><p>设置 快捷键/缓存...</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.pB_setting.setWhatsThis(QtGui.QApplication.translate("Dlg_douban", "<html><head/><body><p>设置 快捷键/缓存...</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.pB_setting.setText(QtGui.QApplication.translate("Dlg_douban", "Settig", None, QtGui.QApplication.UnicodeUTF8))
        self.label_public_time.setText(QtGui.QApplication.translate("Dlg_douban", "发布时间", None, QtGui.QApplication.UnicodeUTF8))
        self.label_album_name.setText(QtGui.QApplication.translate("Dlg_douban", "专辑:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_song_name.setText(QtGui.QApplication.translate("Dlg_douban", "歌名:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_singer.setText(QtGui.QApplication.translate("Dlg_douban", "歌手:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_album_detail.setText(QtGui.QApplication.translate("Dlg_douban", "专辑详情", None, QtGui.QApplication.UnicodeUTF8))
        self.label_save_song.setText(QtGui.QApplication.translate("Dlg_douban", "下载", None, QtGui.QApplication.UnicodeUTF8))
        self.label_google_song.setText(QtGui.QApplication.translate("Dlg_douban", "Google It", None, QtGui.QApplication.UnicodeUTF8))
        self.label_status.setText(QtGui.QApplication.translate("Dlg_douban", "累计11111首 加红心111首 111首不再播发", None, QtGui.QApplication.UnicodeUTF8))

import images_rc
