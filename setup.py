#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

install_requires = [
    'M2Crypto',
    # 'MySQL-python',
    'Pillow',
    # 'PyMySQL',
    'SQLAlchemy==0.9.10',
    # 'bottle',
    'colorlog',
    'gevent<1.2.0',
    'msgpack-python==0.4.2',
    # 'pygit2==0.20.3',
    'redis==2.10.6',
    # 'python-spidermonkey',
    'requests==1.2.3',
    # 'unidecode',
    # 'upyun',
    'raven',
    'dnspython==1.16.0',
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
