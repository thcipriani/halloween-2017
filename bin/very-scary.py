#!/usr/bin/env python2

import argparse
import os
import json
import logging
import random
import requests
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

        self.has_hue = False

        if not args.no_hue:
            self.has_hue = True
            self.hue_ip = args.hue_ip
            self.hue_base_url = 'http://{}/api/newdeveloper'.format(self.hue_ip)
            self._setup_lights()

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
        time.sleep(0.1)
        self.pneumatic.down()
        time.sleep(0.1)
        self.pneumatic.up()
        self.log.debug('pneumatic is up for 5 seconds')

    def _do_popdown(self):
        self.pneumatic.down()
        self.log.debug('pneumatic is down')

    def _play_sound(self):
        if not self.play_sound:
            self.log.debug('not playing sound, in quiet mode')
            return

        cmd = ['/usr/bin/omxplayer', '-o', 'local', self.sound_file]

        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

    def _setup_lights(self):
        self.log.debug('Setup lights')
        lights = [2, 3]

        # Setup lights
        strobe_data = {'1' :'040000FFFF00003333000033330000FFFFFFFFFF'}

        def lights_path(light):
            return os.path.join(self.hue_base_url, 'lights', str(light), 'pointsymbol')

        for light in lights:
            r = requests.put(lights_path(light), data=json.dumps(strobe_data))
            r.raise_for_status()

        self._lights_normal()

    def _send_to_hue(self, action, data):
        if not self.has_hue:
            return

        data = json.dumps(data)
        url = os.path.join(self.hue_base_url, 'groups', '1', action)
        self.log.debug('Sending {}: {}'.format(url, data))
        r = requests.put(url, data)
        r.raise_for_status()
        return r

    def _lights_normal(self):
        """
        Make the lights normal
        """
        self.log.debug('Lights normal')
        data = {
            'transitiontime' : 0,
            'hue': 47118,
            'sat': 254,
            'bri': 254,
            'on': True,
        }

        self._send_to_hue('action', data=data)

    def _lights_red(self):
        self.log.debug('Lights red')
        data = {
            'hue': 0,
            'sat': 254,
            'bri': 254,
            'on': True,
        }

        self._send_to_hue('action', data=data)

    def _lights_flicker(self):
        """
        Strobe ligths
        """
        self.log.debug('Lights strobe')
        for x in xrange(0, 2):
            data = {
                'sat': 0,
                'transitiontime': 0,
            }
            r = self._send_to_hue('action', data=data)

            time.sleep(0.1)

            data = {
                'sat': 254,
                'transitiontime': 0,
            }
            r = self._send_to_hue('action', data=data)
            time.sleep(0.2)


    def scare_em(self):
        """
        Do the actual children scaring
        """
        self.log.info('Scaring child')
        proc = self._play_sound()

        self._lights_red()
        time.sleep(0.5)
        self._do_popup()
        self._lights_flicker()
        self._lights_normal()

        time.sleep(5)

        self._do_popdown()
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
    ap.add_argument('-i', '--hue-ip', default='172.16.1.29',
         help='IP Address of the Hue bulb base station')
    ap.add_argument('-n', '--no-hue', action='store_true',
         help="Don't use the hue lights")
    return ap.parse_args()


def main(args):
    app = App(args)
    app.run()


if __name__ == '__main__':
    main(parse_args())
