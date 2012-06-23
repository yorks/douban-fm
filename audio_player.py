#!/usr/bin/env python
#-*- coding:utf-8 -*-
# Author: stuyorks@gmail.com

import pymedia
import sys
import os
import time
import thread


class AUDIO_PLAYER():
    def __init__(self, filepath=""):
        self.filepath=filepath
        self.ext=None

        self.clip = None
        self.Resampler = None
        self.Decoder = None
        self.Demuxer = None

        self.audio_fp = None
        self.speed = 1

        self.th = None # playback thread
        self.status_list = ["init", "loaded", "playing", "paused", "stopped", "ended"]
        self.status = self.status_list[0]
        if self.filepath:
            pass

    def load_file(self, filepath):
        self.filepath=filepath
        if not os.path.isfile(filepath):
            return 404
        self.ext = self.filepath.split(r'.')[-1].lower()
        SoundCards = pymedia.audio.sound.getODevices()
        if not SoundCards:
            return 500
        self.Demuxer = pymedia.muxer.Demuxer( self.ext )
        self.clip, self.Resampler, self.Decoder = None, None, None
        self.audio_fp = open( self.filepath, "rb" )
        self.th = None # playback thread
        self.status = self.status_list[1]
        return 200

    def play(self):
        if self.status != 'loaded':
            raise "please load file first!"
        if not self.th:
            self.th = thread.start_new_thread( self._play, ( ) )

    def _play(self):
        audio_data = self.audio_fp.read( 32000 )
        self.status = self.status_list[2]
        while ( self.status != 'stopped' and self.status != 'ended' ):
            if self.is_paused():
                time.sleep(0.01)
                continue
            if audio_data:
                audio_frames = self.Demuxer.parse( audio_data )
                for audio_frame in audio_frames:
                    if not self.Decoder:
                        #print self.Demuxer.getHeaderInfo(), self.Demuxer.streams
                        self.Decoder = pymedia.audio.acodec.Decoder(self.Demuxer.streams[ audio_frame[0] ])
                    self.Resampled = self.Decoder.decode( audio_frame[1] )
                    if self.Resampled and self.Resampled.data:
                        if not self.clip:
                            self.clip = pymedia.audio.sound.Output( int(self.Resampled.sample_rate * self.speed),
                                    self.Resampled.channels, pymedia.audio.sound.AFMT_S16_LE, 0)
                        frame_data = self.Resampled.data
                        if self.Resampler:
                            frame_data = self.Resampler.resample( frame_data )
                        if self.status != 'stopped':
                            try:
                                self.clip.play( frame_data )
                            except:
                                continue
                if self.audio_fp:
                    audio_data = self.audio_fp.read( 128 )
            else:
                print "the end"
                self.stop()
                self.status = self.status_list[5]
        print "exit thread"
        self.th = None

    def pause(self):
        if self.clip and self.is_playing():
            self.clip.pause()
            self.status = self.status_list[3]

    def unpause(self):
        if self.clip and self.status == 'paused':
            self.clip.unpause()
            time.sleep(0.1)
            self.status = self.status_list[2]

    def stop(self):
        if self.clip:
            self.clip.stop()
            self.status = self.status_list[4]
            self.th = None
            time.sleep(1)
            self.audio_fp.close()
            self.clip = None

    def get_status(self):
        return self.status

    def is_playing(self):
        if self.status == "playing":
            return True
        else:
            return False
        #if self.clip:
        #    return self.clip.isPlaying()

    def is_paused(self):
        if self.status == "paused":
            return True
        else:
            return False

    def is_ended(self):
        if self.status == "ended":
            return True
        else:
            return False

    def get_volume(self):
        if self.clip:
            return self.clip.getVolume()

    def set_volume(self, volume):
        if self.clip:
            self.clip.setVolume(volume)

    def get_position(self):
        if self.clip:
            return self.clip.getPosition()


if __name__ == "__main__":
    mp3_file=r'/home/yorks/.douban.fm/mp3/297016.mp3'
    mp3_file2=r'/home/yorks/.douban.fm/mp3/422125.mp3'
    player = AUDIO_PLAYER()
    res = player.load_file(mp3_file2)
    if res != 200:
        print "cannot load file!!"
        sys.exit(1)
    player.play()
    time.sleep(5)
    #print player.set_volume(100)
    player.pause()
    print "paused"
    #print player.is_playing()
    #print player.get_position()
    time.sleep(5)
    player.unpause()
    #print player.is_playing()
    #print player.get_position()
    print "unpause"
    time.sleep(30)
    player.stop()
    while True:
        time.sleep(1)
        if player.is_ended():
            #player = AUDIO_PLAYER()
            player.load_file(mp3_file)
            print player.status
            player.play()

