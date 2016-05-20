# -*- encoding: utf-8 -*-

import os
import sys
from os.path import expanduser

from setuptools import setup, find_packages
from setuptools.command.test import test
from setuptools.command.install import install
from setuptools.command.egg_info import egg_info as org_egg_info

assert sys.version_info >= (2, 7), "Python 2.7+ required."

current_dir = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, current_dir + os.sep + 'src')
from vaas import VERSION
release = ".".join(str(num) for num in VERSION)


def basic_configuration(version, db_path=None):
    local_path = os.path.abspath(os.path.dirname(__file__))
    if db_path is None:
        db_path = local_path

    with open(os.path.join(local_path, 'src', 'vaas', 'settings', '__init__.py'), 'w') as init_file:
        init_file.write("from vaas.settings.base import *\nfrom vaas.settings." + version + " import *\n")

    if not os.path.exists(os.path.join(local_path, 'src', 'vaas', 'resources')):
        os.makedirs(os.path.join(local_path, 'src', 'vaas', 'resources'))

    with open(os.path.join(local_path, 'src', 'vaas', 'resources', 'db_config.yml'), 'w') as resource_file:
        resource_file.write(
            "default:\n  ENGINE: 'django.db.backends.sqlite3'\n  NAME: " + os.path.join(db_path, "db.sqlite3")
        )

    with open(os.path.join(local_path, 'src', 'vaas', 'resources', 'production.yml'), 'w') as resource_file:
        resource_file.write("default:\n")


class DjangoTestRunner(test):
    def finalize_options(self):
        test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run(self):
        VaaSEggInfo.active = False
        test.run(self)

    def run_tests(self):
        basic_configuration('test')
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vaas.settings")
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'test'])
        from atexit import _exithandlers
        del _exithandlers[:]


class VaaSEggInfo(org_egg_info):
    active = True

    def run(self):
        if VaaSEggInfo.active:
            try:
                basic_configuration('production', db_path='/tmp')
                os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vaas.settings.base")
                from django.core.management import execute_from_command_line
                execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
            except ImportError, e:
                print "Info: Cannot import: %s, ommit custom egg_info" % (e.message)
        org_egg_info.run(self)

with open('./requirements/base.txt') as f:
    base_requirements = f.read().splitlines()

with open('./requirements/test.txt') as f:
    test_requirements = f.read().splitlines()

base_requirements = [x for x in base_requirements if x.find('==') != -1]
test_requirements = [x for x in test_requirements if x.find('==') != -1]

setup(
    cmdclass={'test': DjangoTestRunner, 'egg_info': VaaSEggInfo},
    name='vaas',
    version='1.0.0',
    author='Grupa Allegro Sp. z o.o. and Contributors',
    author_email='pluton@allegro.pl',
    description="Vaas, Varnish as a Service - management tool",
    long_description="VaaS is a infrastructure service built around Varnish ESI . \
    From now on all developers are able to manage ESI backends by themselves,",
    url='https://github.com/allegro/vaas',
    keywords='',
    platforms=['any'],
    license='Apache Software License v2.0',
    packages=find_packages('src'),
    include_package_data=True,
    package_dir={'': 'src'},
    zip_safe=False,  # because templates are loaded from file path
    tests_require=test_requirements,
    install_requires=base_requirements,
    entry_points={
        'console_scripts': [
            'backend_statuses = vaas.__main__:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows :: Windows NT/2000',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Internet :: WWW/HTTP',
        ]
)
