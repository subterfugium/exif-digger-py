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
import fnmatch
import exiftool
import sys

parser = argparse.ArgumentParser(description='Dig files with exif data.')

group = parser.add_mutually_exclusive_group()
group.add_argument('-v', '--verbose', help="Debug prints", action="store_true")
group.add_argument('-q', '--quiet', help="Do not print anything", action="store_true")

parser.add_argument('-s','--source', help='Source path', required=True)
parser.add_argument('-d','--destination', help='Destination path', required=True)
parser.add_argument('-m','--mode', help='Transfer method', required=False)

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

# Recursive glob
# Source: http://stackoverflow.com/questions/2186525/use-a-glob-to-find-files-recursively-in-python
def recursive_glob(treeroot, pattern):
  results = []
  if args.verbose:
    print "Starting os.walk..."
  for base, dirs, files in os.walk(treeroot):
    goodfiles = fnmatch.filter(files, pattern)
    results.extend(os.path.join(base, f) for f in goodfiles)
  return results

# Get files EXIF metadata
def get_exif_metadata(f):
    with exiftool.ExifTool() as et:
        metadata = et.get_metadata(f)
   
    if args.verbose:
        print
        
        print "Proccessing file: {}".format(f)
        if metadata.has_key('SourceFile'):
            print("SourceFile: {}".format(metadata["SourceFile"]))        
        if metadata.has_key('EXIF:DateTimeOriginal'):
            print("DateTimeOriginal: {:20.20}".format(metadata["EXIF:DateTimeOriginal"]))
        if metadata.has_key('File:MIMEType'):
            print("MIME Type: {}".format(metadata["File:MIMEType"]))
        print
    
    return metadata
     
# Main

# Get all Files
AllFiles = []
print "Getting list of all files in path {}".format(os.path.abspath(args.source))
AllFiles = recursive_glob(os.path.abspath(args.source),'*')
if args.verbose:
    print "Number of files found: {}".format(len(AllFiles))
print

# Get all files metadata
for f in AllFiles:
    print get_exif_metadata(f)

