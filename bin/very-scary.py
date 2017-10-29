#!/usr/bin/env python2

import argparse
import os
import logging
import subprocess
import time


import RPi.GPIO as GPIO
from Adafruit_MotorHAT import Adafruit_MotorHAT


# Two directories up from bin/very-scary.py is the base_dir
BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
SHARE_DIR = os.path.join(BASE_DIR, 'share', 'very-scary')


class Pneumatic(object):
    """
    Abstraction for Adafruit MotorHAT that I'm using as a weird way to drive
    a pneumatic pop-up.
    """

    UP = Adafruit_MotorHAT.FORWARD
    DOWN = Adafruit_MotorHAT.RELEASE

    def __init__(self, args=None):
        if args is None:
            args = {}

        mh = Adafruit_MotorHAT(addr=0x60)

        self.pop_up = mh.getMotor(args.motor)

        # Max motor speed is 255
        self.pop_up.setSpeed(255)

    def up(self):
        self.pop_up.run(self.UP)

    def down(self):
        self.pop_up.run(self.DOWN)


class App(object):

    def __init__(self, args):
        """
        Setup up for program
        """
        log_level = logging.INFO

        if args.verbose:
            log_level = logging.DEBUG

        logging.basicConfig(level=log_level)

        self.log = logging.getLogger()
        self.pneumatic = Pneumatic(args)
        self.motion_pin = args.motion_pin
        self.play_sound = args.quiet is False
        self.sound_file = os.path.realpath(os.path.expanduser(args.sound))

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.motion_pin, GPIO.IN)

    @property
    def motion(self):
        """
        Detect motion
        """
        return GPIO.input(self.motion_pin) == 1

    def _do_popup(self):
        self.pneumatic.up()
        self.log.debug('pneumatic is up for 5 seconds')
        time.sleep(5)

        self.pneumatic.down()
        self.log.debug('pneumatic is down')
        time.sleep(5)

    def _play_sound(self):
        if not self.play_sound:
            self.log.debug('not playing sound, in quiet mode')
            return

        cmd = ['/usr/bin/omxplayer', '-o', 'local', self.sound_file]

        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

    def scare_em(self):
        """
        Do the actual children scaring
        """
        self.log.info('Scaring child')
        proc = self._play_sound()
        self._do_popup()
        proc.communicate()


    def run(self):
        """
        check for motion in a loop, if detected, run scare
        """
        while True:
            self.log.debug('Checking for motion')
            if self.motion:
                self.scare_em()
                while self.motion:
                    self.log.debug('still motion, sleeping...')
                    time.sleep(5)

            time.sleep(0.2)


def parse_args():
    """
    Parse arguments
    """
    ap = argparse.ArgumentParser()
    ap.add_argument('-v', '--verbose', action='store_true',
        help='Increase verbosity of output')
    ap.add_argument('-p', '--motion-pin', type=int,
        default=21, help='Set the GPIO pin')
    ap.add_argument('-m', '--motor', type=int,
        default=4, help='Select which motor to use on'
                        'the adafruit MotorHAT')
    ap.add_argument('-q', '--quiet', action='store_true',
        help="Don't play a sound")
    ap.add_argument('-s', '--sound',
         default=os.path.join(SHARE_DIR, './Scream.mp3'),
         help='scary sound to play')
    return ap.parse_args()


def main(args):
    app = App(args)
    app.run()


if __name__ == '__main__':
    main(parse_args())
