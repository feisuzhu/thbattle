#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

install_requires = [
    'M2Crypto',
    'MySQL-python',
    'Pillow',
    'PyMySQL',
    'SQLAlchemy',
    'bottle',
    'colorlog',
    'gevent>=1.0.1',
    'msgpack-python',
    'pygit2>=0.21.3',
    'redis',
    'requests',
    'unidecode',
    'upyun',
    'raven',
]

entry_points = {
    'console_scripts': [
        'services_events = services.events:main',
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
