from setuptools import setup

import os
import shutil

setup(
    name='home-auto',
    description='Home automation made extra easy',
    author='Alessandro Righi',
    author_email='alessandro.righi@alerighi.it',
    install_requires=[
        'schedule',
        'paho_mqtt',
    ],
    packages=['home_auto'],
    entry_points={
        'console_scripts': [
            'home-auto=home_auto.main:main',
            'home-autod=home_auto.main:daemon',
        ]
    }
)

if os.getuid() == 0:
    shutil.copy(os.path.join(os.path.dirname(__file__),
                'home-auto.service'), '/etc/systemd/system/')
    print('installed Systemd unit: home-auto.service')
