##
##  sparkle-builder.py
##  SparkleBuilder
##
##  Created by James Baker on 4/29/15.
##  Copyright (c) 2015 WDDG, Inc. All rights reserved.
##
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in
## all copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
## THE SOFTWARE.
##

from __future__ import division

import os
import sys
import datetime
import time
import json

from subprocess import Popen, PIPE
from shutil import move, copy, copytree, rmtree
from plistlib import readPlist
from pprint import pprint

from appcast import Appcast, Delta

# functions

def log(msg):
    if VERBOSE:
        print msg

def create_dir_if_needed(path, name):
    if not os.path.isdir(path):
        log("Creating {} directory.".format(name))
        os.makedirs(path)

def clean_directory(dir):
    for f in os.listdir(dir):
        fp = os.path.join(dir, f)
        try:
            if os.path.isfile(fp):
                os.unlink(fp)
            elif os.path.isdir(fp):
                rmtree(fp)
        except Exception, e:
            print e

def create_delta(old_source = '', new_source = ''):
    binary_delta_script = SPARKLE_BIN_PATH + "BinaryDelta"
    old_version = get_version_info(old_source)
    new_version = get_version_info(new_source)
    delta_file = "{}-{}.delta".format(old_version, new_version)
    delta_file_path = "{}{}".format(DELTAS_PATH, delta_file)
    create_delta_call = [binary_delta_script, "create", old_source, new_source, delta_file_path]
    process = Popen(create_delta_call, stdout=PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    log("create {}".format(delta_file))
    return delta_file, delta_file_path


def create_zip(file_name, new_name=''):
    path = CURRENT_APP_PATH
    source_file = path + file_name
    if new_name:
        file_name = new_name

    ## build the zip and move into place
    zip_file = path + file_name + ".zip"
    new_zip_file = ZIPS_PATH + file_name + '.zip'
    if os.path.exists(new_zip_file):
        os.remove(new_zip_file)
    ditto_call = ["ditto", "-c", "-k", "--keepParent", "-rsrc", source_file, zip_file]
    process = Popen(ditto_call, stdout=PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    move(zip_file, ZIPS_PATH)

    log("create {}.zip".format(file_name))
    if ARCHIVE_ZIPS:
        archive_file(new_zip_file, 'Zips/')
    # return path to new zip
    return new_zip_file


def sign_update(zip_file = '', private_key_path = ''):
    sign_update_script = SPARKLE_BIN_PATH + "sign_update.sh"
    sign_update_call = [sign_update_script, zip_file, private_key_path]
    process = Popen(sign_update_call, stdout=PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    return output.rstrip()


def get_key_from_bundle(key='', bundle=''):
    info_plist = bundle + "/Contents/Info.plist"
    with open(info_plist, 'rb') as fp:
        pl = readPlist(fp)
    return pl[key]


def get_version_info(bundle):
    info_plist = bundle + "/Contents/Info.plist"
    with open(info_plist, 'rb') as fp:
        pl = readPlist(fp)
    major_version = get_key_from_bundle(key='CFBundleShortVersionString', bundle=bundle)
    minor_version = get_key_from_bundle(key='CFBundleVersion', bundle=bundle) #pl['CFBundleVersion']
    return "{}.{}".format(major_version,minor_version)


def get_version_info__(app_file):
    info_plist = app_file + "/Contents/Info.plist"
    with open(info_plist, 'rb') as fp:
        pl = readPlist(fp)
    major_version = pl['CFBundleShortVersionString']
    minor_version = pl['CFBundleVersion']
    return "{}.{}".format(major_version,minor_version)


def get_bundle_version(app_file):
    info_plist = app_file + "/Contents/Info.plist"
    with open(info_plist, 'rb') as fp:
        pl = readPlist(fp)
    return pl['CFBundleVersion']


def archive_file(filepath, subdirectory):
    basename = os.path.basename(filepath)
    filename, extension = os.path.splitext(basename)
    date = time.strftime("%d%m%Y")
    new_filename = "{}{}_{}".format(ARCHIVE_PATH+subdirectory, filename, date)
    i = 0
    while os.path.exists("{}_{}{}".format(new_filename, str(i), extension)):
        i+=1
    copy(filepath,"{}_{}{}".format(new_filename, str(i), extension))
    log("archive {}".format(basename))


def copy_files(origin="", destination="", extension=""):
    for (dirpath, _, filenames) in os.walk(origin):
        for filename in filenames:
            _, _extension = os.path.splitext(filename)
            if _extension == extension:
                log("publish {}".format(filename))
                origin_file = os.path.join(dirpath, filename)
                published_file = os.path.join(destination, filename)
                copy(origin_file, published_file)


##############################
###   configuration setup  ###
##############################

with open('sparkle-builder-config.json') as data_file:
    data = json.load(data_file)


VERBOSE                 = data["VERBOSE"]

# paths
BUILD_PATH              = data["BUILD_DIRECTORY_PATH"]
os.chdir(BUILD_PATH)
APPS_PATH               = BUILD_PATH + "Apps/"
ZIPS_PATH               = BUILD_PATH + "Zips/"
DELTAS_PATH             = BUILD_PATH + "Deltas/"
APPCAST_PATH            = BUILD_PATH + "Appcast/"
ARCHIVE_PATH            = BUILD_PATH + "Archives/"
CURRENT_APP_PATH        = BUILD_PATH + "App/"
APP_ARCHIVE_PATH        = ARCHIVE_PATH + "Apps/"

## get the latest app
## bark and exit if there is more than one in the directory

_apps = []
for (_, dirname, _) in os.walk(CURRENT_APP_PATH):
    _apps.extend(dirname)
    break

if not _apps:
    print "nothing found at {}, please place latest version of the app there".format(CURRENT_APP_PATH)
    sys.exit()

if len(_apps) > 1:
    print "more than one app found at {}. remove all apps, files and directories other the latest version".format(CURRENT_APP_PATH)
    sys.exit()

LATEST_APP              = _apps[0]
APP_NAME                = get_key_from_bundle(key='CFBundleExecutable', bundle=CURRENT_APP_PATH+LATEST_APP)
BUNDLE_VERSION          = get_key_from_bundle(key='CFBundleVersion', bundle=CURRENT_APP_PATH+LATEST_APP)
CURRENT_VERSION         = get_version_info(CURRENT_APP_PATH+LATEST_APP)
LATEST_APP_ARCHIVE      = '{}-{}.app'.format(APP_NAME, CURRENT_VERSION)

PRIVATE_KEY_PATH        = data["PRIVATE_KEY_PATH"]
SPARKLE_BIN_PATH        = data["SPARKLE_BIN_PATH"]

# options
CLEAN_DIRECTORIES       = data["CLEAN_DIRECTORIES"]
OVERWRITE_APP_ARCHIVES  = data["OVERWRITE_APP_ARCHIVES"]
ARCHIVE_ZIPS            = data["ARCHIVE_ZIPS"]
ARCHIVE_APPCASTS        = data["ARCHIVE_APPCASTS"]
ARCHIVE_DELTAS          = data["ARCHIVE_DELTAS"]

# Appcast setup
APPCAST_FILE_NAME                           = data["APPCAST_FILE_NAME"]
APPCAST_BASE_URL                            = data["APPCAST_BASE_URL"]
APPCAST_TITLE                               = data["APPCAST_TITLE"]
APPCAST_DESCRIPTION                         = data["APPCAST_DESCRIPTION"]
APPCAST_LANGUAGE                            = data["APPCAST_LANGUAGE"]
APPCAST_LATEST_VERSION_UPDATE_DESCRIPTION   = data["APPCAST_LATEST_VERSION_UPDATE_DESCRIPTION"]
APPCAST_RELEASE_NOTES_FILE                  = data["APPCAST_RELEASE_NOTES_FILE"]

if APPCAST_RELEASE_NOTES_FILE:
    APPCAST_RELEASE_NOTES_FILE = "{}appcast/{}".format(APPCAST_BASE_URL, APPCAST_RELEASE_NOTES_FILE)

## publish configuration
PUBLISH                                     = data["PUBLISH"]
PUBLISH_ROOT_PATH                           = data["PUBLISH_ROOT_PATH"]
PUBLISH_APPCAST_DIR                         = data["PUBLISH_APPCAST_DIR"]
PUBLISH_DOWNLOADS_DIR                       = data["PUBLISH_DOWNLOADS_DIR"]
PUBLISH_DELTAS_DIR                          = data["PUBLISH_DELTAS_DIR"]

## app derived
# LATEST_APP = '{}-{}.app'.format(APP_NAME, CURRENT_VERSION)

## appcast derived
APPCAST_URL                                 = APPCAST_BASE_URL + "appcast/" + APPCAST_FILE_NAME
APPCAST_PUBDATE                             = time.strftime("%a, %d %b %G %T %z")
APPCAST_LATEST_VERSION_NUMBER               = CURRENT_VERSION
APPCAST_LATEST_VERSION_URL                  = APPCAST_BASE_URL + "downloads/" + LATEST_APP_ARCHIVE + ".zip"
APPCAST_DELTA_URL                           = APPCAST_BASE_URL + 'deltas/'

APPCAST_FILE = APPCAST_PATH + APPCAST_FILE_NAME


##############################
###   appcast genreration  ###
##############################

# load old apps from Apps

apps = []
if os.path.isdir(APP_ARCHIVE_PATH):
    for (_, dirname, _) in os.walk(APP_ARCHIVE_PATH):
        apps.extend(dirname)
        break

if not apps:
    print "no apps found in {}. no deltas will be produced".format(APP_ARCHIVE_PATH)

## check for directories, if Zips or Deltas don't exist create them

create_dir_if_needed(ZIPS_PATH, 'Zips`')
create_dir_if_needed(APPCAST_PATH, 'Appcast')
create_dir_if_needed(DELTAS_PATH, 'Deltas')

if CLEAN_DIRECTORIES:
    clean_directory(DELTAS_PATH)
    clean_directory(APPCAST_PATH)
    clean_directory(ZIPS_PATH)

create_dir_if_needed(ARCHIVE_PATH, 'Archive')
create_dir_if_needed(ARCHIVE_PATH+'Apps/', 'Archive/Apps')

if ARCHIVE_APPCASTS:
    create_dir_if_needed(ARCHIVE_PATH+'Appcasts/', 'Archive/Appcasts')

if ARCHIVE_DELTAS:
    create_dir_if_needed(ARCHIVE_PATH+'Deltas/', 'Archive/Deltas')

if ARCHIVE_ZIPS:
    create_dir_if_needed(ARCHIVE_PATH+'Zips/', 'Archive/Zips')

## appcast setup
appcast = Appcast()

appcast.title                               = APPCAST_TITLE
appcast.appcast_url                         = APPCAST_URL
appcast.appcast_description                 = APPCAST_DESCRIPTION
if APPCAST_RELEASE_NOTES_FILE:
     appcast.release_notes_file             = APPCAST_RELEASE_NOTES_FILE
appcast.launguage                           = APPCAST_LANGUAGE
appcast.latest_version_number               = CURRENT_VERSION
appcast.latest_version_update_description   = APPCAST_LATEST_VERSION_UPDATE_DESCRIPTION
appcast.pub_date                            = APPCAST_PUBDATE
appcast.latest_version_url                  = APPCAST_LATEST_VERSION_URL
zipped_app                                  = create_zip(LATEST_APP, new_name=LATEST_APP_ARCHIVE)
appcast.latest_version_size                 = os.path.getsize(zipped_app)
appcast.latest_version_dsa_key              = sign_update(zipped_app, private_key_path=PRIVATE_KEY_PATH)

## deltas
for app in apps:
    if app.endswith('.app'):
        if not app == LATEST_APP_ARCHIVE:
            app_path                            = APP_ARCHIVE_PATH + app
            delta                               = Delta()
            delta_file_name, delta_file_path    = create_delta(old_source=app_path, new_source=CURRENT_APP_PATH+LATEST_APP)
            delta.delta_url                     = APPCAST_DELTA_URL + delta_file_name
            delta.delta_to_version              = CURRENT_VERSION
            delta.delta_from_version            = get_version_info(app_path)
            delta.delta_size                    = os.path.getsize(delta_file_path)
            delta.delta_dsa_key                 = sign_update(delta_file_path, private_key_path=PRIVATE_KEY_PATH)
            appcast.append_delta(delta)


## write out the appcast
appcast_xml =  appcast.render()
with open(APPCAST_FILE, 'w') as f:
    f.write(appcast_xml)
log("create {}".format(APPCAST_FILE_NAME))


################
## Publishing ##
################

if PUBLISH:
    appcast_publish_path    = PUBLISH_ROOT_PATH + PUBLISH_APPCAST_DIR
    downloads_publish_path  = PUBLISH_ROOT_PATH + PUBLISH_DOWNLOADS_DIR
    deltas_publish_path     = PUBLISH_ROOT_PATH + PUBLISH_DELTAS_DIR

    ## create directories if needed
    create_dir_if_needed(appcast_publish_path, 'Appcast Publish')
    create_dir_if_needed(downloads_publish_path, 'Downloads Publish')
    create_dir_if_needed(deltas_publish_path, 'Deltas Publish')

    appcast_publish_file = appcast_publish_path + APPCAST_FILE_NAME
    copy(APPCAST_FILE, appcast_publish_file)
    log("publish {}".format(APPCAST_FILE_NAME))

    copy_files(origin=DELTAS_PATH, destination=deltas_publish_path, extension=".delta")
    copy_files(origin=ZIPS_PATH, destination=downloads_publish_path, extension=".zip")


###############
## Archiving ##
###############

## always archive the latest app unless it's already there

if OVERWRITE_APP_ARCHIVES:
    if os.path.isdir(APP_ARCHIVE_PATH+LATEST_APP_ARCHIVE):
        rmtree(APP_ARCHIVE_PATH+LATEST_APP_ARCHIVE)

if not os.path.isdir(APP_ARCHIVE_PATH+LATEST_APP_ARCHIVE):
    copytree(CURRENT_APP_PATH+LATEST_APP, APP_ARCHIVE_PATH+LATEST_APP_ARCHIVE)
    log("archive {}".format(LATEST_APP_ARCHIVE))
else:
    log("{} already archived - skipping".format(LATEST_APP_ARCHIVE))


if ARCHIVE_APPCASTS:
    archive_file(APPCAST_FILE, 'Appcasts/')

## archive Deltas
if ARCHIVE_DELTAS:
    date = time.strftime("%m%d%Y")
    delta_directory = DELTAS_PATH
    if delta_directory.endswith('/'):
        delta_directory = delta_directory[:-1]
    new_directory = "{}/Deltas_{}".format(ARCHIVE_PATH+'Deltas/', date)
    i = 0
    while os.path.exists("{}_{}".format(new_directory, str(i))):
        i+=1
    copytree(DELTAS_PATH,"{}_{}".format(new_directory, str(i)))
    log("archive deltas")
