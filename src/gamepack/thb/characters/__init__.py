# -*- coding: utf-8 -*-
# Character definitions are here.

import baseclasses

import parsee  # noqa
import youmu  # noqa
import koakuma  # noqa
import marisa  # noqa
import daiyousei  # noqa
import flandre  # noqa
import alice  # noqa
import nazrin  # noqa
import yugi  # noqa
import patchouli  # noqa
import tewi  # noqa
import reimu  # noqa
import kogasa  # noqa
import eirin  # noqa
import shikieiki  # noqa
import tenshi  # noqa
import rumia  # noqa
import yuuka  # noqa
import rinnosuke  # noqa
import ran  # noqa
import remilia  # noqa
import minoriko  # noqa
import meirin  # noqa
import suika  # noqa
import chen  # noqa
import yukari  # noqa
import cirno  # noqa
import sakuya  # noqa
import sanae  # noqa
import seiga  # noqa
import kaguya  # noqa
import momiji  # noqa
import komachi  # noqa
import mokou  # noqa
import kokoro  # noqa
import mamizou  # noqa

import remilia_ex  # noqa

# special
import dummy  # noqa
import akari  # noqa

import sys

from game.autoenv import Game
from options import options
options.testing and baseclasses.register_character(dummy.Dummy)

characters = tuple(sorted(baseclasses.characters, key=lambda i: i.__name__))
raid_characters = tuple(sorted(baseclasses.raid_characters, key=lambda i: i.__name__))
id8exclusive_characters = tuple(sorted(baseclasses.id8exclusive_characters, key=lambda i: i.__name__))
del baseclasses.characters
del baseclasses.raid_characters
del baseclasses.id8exclusive_characters

del sys, Game, options
