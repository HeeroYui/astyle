#! /usr/bin/env python
# encoding: utf-8

import os
import filecmp
import difflib
import sys
import subprocess
import shutil
from waflib.TaskGen import feature, after_method
from waflib import Errors
import waflib.extras.wurf_options

APPNAME = 'astyle'
VERSION = '0.1.0'


def options(opt):

    opt.load('wurf_common_tools')


def resolve(ctx):

    import waflib.extras.wurf_dependency_resolve as resolve

    ctx.load('wurf_common_tools')

    ctx.add_dependency(resolve.ResolveVersion(
        name='waf-tools',
        git_repository='github.com/steinwurf/waf-tools.git',
        major=3))


def configure(conf):

    conf.load("wurf_common_tools")


def build(bld):

    bld.load("wurf_common_tools")

    bld.env.append_unique(
        'DEFINES_STEINWURF_VERSION',
        'STEINWURF_ASTYLE_VERSION="{}"'.format(VERSION))

    if bld.is_toplevel():

        static_libs = []
        if bld.is_mkspec_platform('windows'):
            static_libs = ['Shell32']

        bld.program(
            features='cxx test_astyle',
            source=bld.path.ant_glob('src/*.cpp'),
            lib=static_libs,
            target='astyle')


@feature('test_astyle')
@after_method('apply_link')
def test_astyle(self):
    # Only execute the tests within the current project
    if self.path.is_child_of(self.bld.srcnode):
        if self.bld.has_tool_option('run_tests'):
            self.bld.add_post_fun(run_astyle_tests)


def run_command(args):
    print("Running: {}".format(args))
    sys.stdout.flush()
    subprocess.check_call(args)


def run_astyle_tests(bld):
    astyle = bld.get_tgen_by_name('astyle').link_task.outputs[0].abspath()
    options = "--options={}".format(bld.path.find_node('.astylerc').abspath())

    if os.path.isdir('test'):
        test_folder = os.path.join(os.getcwd(), 'test')
        correct_style = os.path.join(test_folder, 'correct_style.cpp')
        correct_lines = open(correct_style, 'U').readlines()

        temp_folder = os.path.join(test_folder, 'temp')
        # Make sure that the temp folder is deleted before copytree
        if os.path.isdir(temp_folder):
            shutil.rmtree(temp_folder)
        shutil.copytree(test_folder, temp_folder)

        incorrect_files = 0

        # Run astyle to format each test file
        for file in sorted(os.listdir(temp_folder)):
            test_file = os.path.join(temp_folder, file)
            if (os.path.isfile(test_file)):
                print('Test file: '+test_file)
                run_command([astyle, options, test_file])

                # Compare the formatted file with the correct style
                if not filecmp.cmp(correct_style, test_file):
                    incorrect_files += 1
                    print('\nIncorrect formatting: {}'.format(test_file))

                    test_lines = open(test_file, 'U').readlines()

                    diff = difflib.unified_diff(correct_lines, test_lines)
                    print(''.join(diff))

        # Clean up the temp directory
        shutil.rmtree(temp_folder)

        if incorrect_files > 0:
            raise Errors.WafError('Number of incorrectly formatted '
                                   'files: {}'.format(incorrect_files))