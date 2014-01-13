#!/usr/bin/env python
#-*- coding: utf-8 -*-
import os
import subprocess

class MPLAYER(object):
    def __init__(self, fifo_path='/tmp/py-mplayer-fifo.sock', bin_path='mplayer', volume=30, debug=False):
        self.file_path    = None
        self.next_file    = None
        self.volume       = volume
        self.proc         = None
        self.fifo_path    = fifo_path
        self.fifo_isfirst = True # flag, for first cache one line to fifo sock ??
        self.args = [ bin_path,
                '-nolirc',
                '-nosub',
                '-really-quiet',
                '-noconsolecontrols',
                '-softvol', 'volume=%d'% self.volume,
                '-slave','-input','file=%s' % self.fifo_path,]
        self.debug = debug
        self.status = 'init' # init, load, playing, pause, stop

    def _mkfifo(self):
        """
           mkfifo the sock file is not exist!
        """
        if os.path.exists(self.fifo_path):
            print "fifo is already exist! skip mkfifo it!"
            return 202
        else:
            os.mkfifo(self.fifo_path)
            return 200

    def _init_fifo(self):
        """
           inital the fifo sock, send the first cmd to fifo sock when first start play!
           because mplayer input file must do any command before this.
        """
        if not self.fifo_isfirst:
            return

        if not os.path.exists(self.fifo_path):
            self._mkfifo()
        fw = open(self.fifo_path, 'w')
        fw.write('\n')
        fw.flush()
        fw.close()
        self.fifo_isfirst = False


    def _write_fifo(self, cmd):
        """
            send cmd to the fifo sock, if mplayer
            not running restart it autoly when loaded file_path.
        """
        if self.debug:print cmd
        cmd = cmd + "\n"
        if not os.path.exists( self.fifo_path ):
            self._mkfifo()
        if not self.is_alive( auto_restart=True ):
            print "mplayer is not running and file not load!!!"
            return False
        with open(self.fifo_path, 'w') as fw:
            fw.write(cmd)
            fw.flush()
        return True
    def _update_args_volume(self):
        old=''
        i = 6
        new='volume=%d'% self.volume
        for arg in self.args:
            if arg.startswith('volume='):
                old = arg
        if old:
            i = self.args.index( old )
            self.args.remove( old )

        self.args.insert( i, new )


    def _m_loadfile(self, file_path, append=True):
        cmd = "loadfile %s"
        if append:
            cmd=cmd+" 1"
        self._write_fifo( cmd )

    def pause(self):
        if self.status == 'playing':
            cmd='pause'
            self._write_fifo(cmd)
            self.status = 'pause'

    def unpause(self):
        if self.status == 'pause':
            cmd='pause'
            self._write_fifo(cmd)
            self.status = 'playing'

    def set_volume(self, n):
        n = int(n)
        if n<0 or n>100:
            return 401
        cmd = 'volume %d 1'% n
        if self._write_fifo( cmd ):
            self.volume = n
            self._update_args_volume()
            if self.debug:print self.args
            return 200
        else:
            return 600

    def play_next(self, file_path):
        self.file_path = file_path
        self._m_loadfile(self.file_path, append=False)
        self.status = 'playing'

    def get_status(self):
        return self.status

    def is_alive(self, auto_restart=False):
        if self.proc is not None:
            if self.proc.poll() is None:
                return True
            else:
                self.status = 'stop'

        if auto_restart and self.file_path:
            self.new_play()
            return True
        else:
            return False

    def load_file(self, file_path, append=True):
        if not os.path.isfile( file_path ):
            print "file not load, for the file not exist or not a file!"
            return 404
        if not os.path.exists( self.fifo_path ):
            self._mkfifo()
        self.file_path = file_path
        self.status = 'load'
        if not append:
            self.play_next(self.file_path)
        else:
            return 200

    def new_play(self):
        if self.debug:print "new_play!!!"
        if self.file_path:
            self.proc = subprocess.Popen(self.args + [self.file_path])
            print self.volume
            self.set_volume(self.volume)
            self.status = 'playing'

    def auto_restart(self):
        if self.debug:print "mplayer is not running, auto restarting!!!"
        self.new_play()

    def play(self):
        if not self.file_path:
            print "pls load_file first!!!"
            return 401
        if self.proc is None: # first play
            self.new_play()
            self._init_fifo()
        elif self.proc.poll() is not None: # mplayer is terminaled, restart it autoly
            self.auto_restart()
        else:
            if self.status == 'pause':
                self.unpause()
            elif self.status == 'stop':
                self.new_play()
            elif self.status == 'playing':
                print "is playing %s, donot call play again!"% self.file_path
                return 402
            else:
                raise "status not found!!!"

    def stop(self):
        if self.is_alive():
            cmd='stop'
            self._write_fifo( cmd )
        else:
            pass
        if self.is_alive():
            self.proc.kill()
            self.proc = None

        self.status = 'stop'

    def quit(self):
        self.stop()
        if os.path.exists( self.fifo_path ):
            os.unlink(self.fifo_path)



if __name__ == "__main__":
    import sys
    player = MPLAYER()
    player.load_file(sys.argv[1])
    player.play()
    import time
    player.set_volume( 80 )
    time.sleep(5)
    player.pause()
    time.sleep(5)
    player.unpause()
    while 1:
        if not player.is_alive() and player.status == 'stop':
            player.load_file('/home/yorks/vsftpd/down/再见二丁目.flac')
            player.play()
        time.sleep(5)


