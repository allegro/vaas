#!/usr/bin/env python
import os
import sys


def call_manage():
    os.environ["DJANGO_SETTINGS_MODULE"] = "vaas.settings"
    from django.core.management import execute_from_command_line
    sys.argv[0] = sys.argv[0].split(os.path.sep)[-1]
    execute_from_command_line(['manage.py'] + sys.argv)


def main():
    call_manage()


if __name__ == "__main__":
    main()
