#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

install_requires = [
    'M2Crypto',
    'MySQL-python',
    'Pillow',
    'SQLAlchemy',
    'bottle',
    'colorlog',
    'gevent==1.0.1',
    'msgpack-python',
    'pygit2>=0.21.3',
    'redis',
    'python-spidermonkey',
    'requests',
    'unidecode',
    'upyun',
]

entry_points = {
    'console_scripts': [
        'aya = aya.aya:main',
        'ayacharger = aya.charger:main',
        'forum_noti = aya.forum_noti:forum_noti',
        'services_events = services.events:main',
        'services_member = services.member:main',
        'start_client = start_client:start_client',
        'start_server = start_server:start_server',
    ]
}

setup(
    name="thbattle",
    version="1.0.0",
    url='http://thbattle.net',
    license='GPLv3',
    description="THBattle",
    author='proton',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=install_requires,
    entry_points=entry_points,
)
