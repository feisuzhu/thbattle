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
    'gevent==0.13.8',
    'msgpack-python',
    'redis',
    'requests',
    'simplejson',
    'unidecode',
]

entry_points = {
    'console_scripts': [
        'start_server = start_server:start_server',
        'start_client = start_client:start_client',
        'services_events = services.events:main',
        'services_member = services.member:main',
        'aya = aya.aya:main',
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
