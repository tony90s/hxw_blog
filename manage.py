#!/usr/bin/env python
"""
Usage: manage.py {blog\microsite} [--settings env] ...

Run django management commands. Because edx-platform contains multiple django projects,
the first argument specifies which project to run (blog or microsite).

By default, those systems run in with a settings file appropriate for development. However,
by passing the --settings flag, you can specify what environment specific settings file to use.

Any arguments not understood by this manage.py will be passed to django-admin.py
"""

import os
import sys
from argparse import ArgumentParser


def parse_args():
    """Parse edx specific arguments to manage.py"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(title='system', description='blog service to run')

    blog = subparsers.add_parser(
        'blog',
        help='Blog',
        add_help=False,
        usage='%(prog)s [options] ...'
    )
    blog.add_argument('-h', '--help', action='store_true', help='show this help message and exit')
    blog.add_argument(
        '--settings',
        help="Which django settings module to use under blog. If not provided, the DJANGO_SETTINGS_MODULE "
             "environment variable will be used if it is set, otherwise it will default to blog.settings")
    blog.add_argument(
        '--service-variant',
        choices=['hxw_blog', 'hxw_blog-xml', 'hxw_blog-preview'],
        default='hxw_blog',
        help='Which service variant to run, when using the aws environment')
    blog.set_defaults(
        help_string=blog.format_help(),
        settings_base='hxw_blog',
        default_settings='hxw_blog.settings'
    )

    microsite = subparsers.add_parser(
        'microsite',
        help='Mobile Version Of Blog',
        add_help=False,
        usage='%(prog)s [options] ...'
    )
    microsite.add_argument('-h', '--help', action='store_true', help='show this help message and exit')
    microsite.add_argument(
        '--settings',
        help="Which django settings module to use under microsite. If not provided, the DJANGO_SETTINGS_MODULE "
             "environment variable will be used if it is set, otherwise it will default to microsite.settings")
    microsite.add_argument(
        '--service-variant',
        choices=['microsite', 'microsite-xml', 'microsite-preview'],
        default='microsite',
        help='Which service variant to run, when using the aws environment')
    microsite.set_defaults(
        help_string=microsite.format_help(),
        settings_base='microsite',
        default_settings='microsite.settings',
    )

    blog_args, django_args = parser.parse_known_args()

    if blog_args.help:
        print("edX:")
        print(blog_args.help_string)

    return blog_args, django_args


if __name__ == "__main__":
    blog_args, django_args = parse_args()

    if blog_args.settings:
        os.environ["DJANGO_SETTINGS_MODULE"] = blog_args.settings_base.replace('/', '.') + "." + blog_args.settings
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", blog_args.default_settings)

    os.environ.setdefault("SERVICE_VARIANT", blog_args.service_variant)

    if blog_args.help:
        print("Django:")
        # This will trigger django-admin.py to print out its help
        django_args.append('--help')

    from django.core.management import execute_from_command_line

    execute_from_command_line([sys.argv[0]] + django_args)
