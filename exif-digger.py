#!/bin/bash

# exif-digger

# To be run after disk recovery which usually doesn't return
# original folder/file structure (e.g. TestDisk)

# Tries to find all the files that includes exif information and
# organize them into folders. 
# - processing for jpg files
#   - Check that it's valid jpg (jpeginfo no WARNING or ERROR)
#   - Try to find out pictures taken with cameras
#      - Width > 640
#      - Camera model not null
#   - Try to find thumb nails generated from pictures taken with cameras
#     - Width < 640
#     - Camera model not null
#   - Rename jpg files to yyyy-mm-dd_hh-mm-ss_count-number 

# Images without exif data (jpeginfo)

#options: default just print
#        '-s /path/source/' source path, if missing use pwd
#        '-d /path/to/' destination path (mandatory)
#        '-m cp|mv' 
#           cp: copy files to destination folder
#           mv: files to destation folder ( in case -cp and -mv print error)
#        '-a' process audio files
#        '-i' process image files
#        '-v' process video files
#        '-c mime type/internet media type' process custom mime type

# 1. find $1 -type f
# 2. pipe all files to exiftool
# 3. grep for MIMEType
# 4. "image/*" create $2/image/* as respective folders
#    "audio/*"              ''
#    "video/*"              ''
#
#    For image/jpeg input file run jpeginfo warning/error check
#    -> move files $2/image/jpg/corrupted
# 
# 5. Create folders as new mime types found
# 6. print/cp/mv files - never replace nor rm!
# 7. Keep file names but fix extension (compare mime type to extension table)

import argparse
import os
import glob

parser = argparse.ArgumentParser(description='Dig files with exif data.')

group = parser.add_mutually_exclusive_group()
group.add_argument('-v', '--verbose', help="Debug prints", action="store_true")
group.add_argument('-q', '--quiet', help="Do not print anything", action="store_true")

parser.add_argument('-s','--source', help='Source path', required=True)
parser.add_argument('-d','--destination', help='Destination path', required=True)
parser.add_argument('-m','--mode', help='Transfer method', required=True)

args = parser.parse_args()
print

if not args.quiet:
    print "Source path:          {}".format(args.source)
    print "Destination path:     {}".format(args.destination)
    print

if args.verbose:
    print "Source absolute path: {}".format(os.path.abspath(args.source))
    print "Destination path:     {}".format(os.path.abspath(args.destination))
    print

# Find all files using glob. Glob with joined asterix on the path will skip
# files starting with dot
def FindAllFiles(source):
    scan_path = os.path.join(source,'*')
    if args.verbose:
        print "Scanning files:   {}".format(scan_path)
    return glob.glob(scan_path)

# Main
AllFiles = []
AllFiles = FindAllFiles(os.path.abspath(args.source))
print AllFiles


