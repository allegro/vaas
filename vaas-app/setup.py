# -*- encoding: utf-8 -*-

import os
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test
from setuptools.command.egg_info import egg_info as org_egg_info

assert sys.version_info >= (3, 5), "Python 3.5+ required."

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


class VaaSEggInfo(org_egg_info):
    active = True

    def run(self):
        if VaaSEggInfo.active:
            try:
                basic_configuration('production', db_path='/tmp')
                os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vaas.settings.base")
                from django.core.management import execute_from_command_line
                execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
            except ImportError as e:
                print("Info: Cannot import: {}, ommit custom egg_info".format(e.msg))
        org_egg_info.run(self)


def extract_requirement(requirement):
    req = None
    link = None
    if hasattr(requirement, 'req'):
        req = str(getattr(requirement, 'req'))
        if hasattr(requirement, 'link'):
            link = str(getattr(requirement, 'link'))
    elif hasattr(requirement, 'requirement'):
        from pip._internal.req.constructors import parse_req_from_line
        parts = parse_req_from_line(requirement.requirement, requirement.line_source)
        if parts.requirement.url:
            req = str(parts.requirement.name)
            link = str(parts.requirement.url)
        else:
            req = requirement.requirement

    assert req is not None, "Unknown requirement, cannot find properties req or requirement {}".format(requirement.__dict__)
    return req, link


base_requirements = []
test_requirements = []
dependency_links = []

for index, requirement in enumerate(parse_requirements('{}/requirements/base.txt'.format(current_dir), session=False)):
    req, dependency_link = extract_requirement(requirement)
    base_requirements.append(req)
    if dependency_link:
        dependency_links.append(dependency_link)

for requirement in parse_requirements('{}/requirements/test.txt'.format(current_dir), session=False):
    req, dependency_link = extract_requirement(requirement)
    test_requirements.append(req)
    if dependency_link and dependency_link not in dependency_links:
        dependency_links.append(dependency_link)

dependency_links = list(filter(lambda x: x is not None, dependency_links))
setup(
    cmdclass={'test': DjangoTestRunner, 'egg_info': VaaSEggInfo},
    name='vaas',
    version=release,
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
