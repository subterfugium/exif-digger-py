#!/usr/bin/python

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
import shutil
import math
import re

minwidth=640

parser = argparse.ArgumentParser(description='Dig files with exif data.')

group = parser.add_mutually_exclusive_group()
group.add_argument('-v', '--verbose', help="Debug prints", action="store_true")
group.add_argument('-q', '--quiet', help="Do not print anything", action="store_true")

parser.add_argument('-s','--source', help='Source path', required=True)
parser.add_argument('-d','--destination', help='Destination path', required=True)
parser.add_argument('-m','--mode', help='Transfer method', required=False)

args = parser.parse_args()

print 
if args.verbose:
    print
    
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
  if args.verbose:
    print "os.walk done"
  return results

# Get files EXIF metadata
def get_exif_metadata(f):
    with exiftool.ExifTool() as et:
        metadata = et.get_metadata(f)
   
    #if args.verbose:
    #    print "Proccessing file: {}".format(f)
    #    if metadata.has_key('SourceFile'):
    #        print("SourceFile: {}".format(metadata["SourceFile"]))        
    #    if metadata.has_key('EXIF:DateTimeOriginal'):
    #        print("DateTimeOriginal: {:20.20}".format(metadata["EXIF:DateTimeOriginal"]))
    #    if metadata.has_key('File:MIMEType'):
    #       print("MIME Type: {}".format(metadata["File:MIMEType"]))
    #    print
    
    return metadata

# Function to create folder if it doesn't exists
def create_folder_if_does_not_exists(directory):
    if args.verbose:
        print("Create {} if it doesn't exists".format(directory))
        print
    if not os.path.exists(directory):
        os.makedirs(directory)
        print("Created {}".format(directory))

# Function to process jpg files
def process_jpg_files(idx,f,metadata,destination,mode):

    picture_taken_with_camera=False
    picture_taken_with_camera_thumb=False
    
    # Determine if jpg file has camera model in metadata
    # and if it's width is less than minwidth (considered as thumb)
    if  (metadata.has_key('EXIF:Model')):
        print "  Model not null: {}".format(metadata['EXIF:Model'])
        if (metadata.has_key('EXIF:ExifImageWidth')):
            if (metadata['EXIF:ExifImageWidth'] >= minwidth):
                print "  ExifImageWidth greater than {}".format(minwidth)
                picture_taken_with_camera=True
            else:
                print "  ExifImageWidth NOT greater than {}".format(minwidth)
                picture_taken_with_camera=True
                picture_taken_with_camera_thumb=True
        elif (metadata.has_key('EXIF:ImageWidth')):
            if (metadata['EXIF:ImageWidth'] >= minwidth):
                print "  ImageWidth greater than {}".format(minwidth)
                picture_taken_with_camera=True
            else:
                print "  ImageWidth greater NOT than {}".format(minwidth)
                picture_taken_with_camera=True
                picture_taken_with_camera_thumb=True
        else:
            print "  No ExifImageWidth or ImageWidth found"
    else:
        print "  No camera model found"
     
    # If picture is taken with camera and is not a thumb
    if (picture_taken_with_camera) and (not picture_taken_with_camera_thumb):
        newf = check_jpg_date_taken_and_rename(idx,f,metadata)
        if newf:
            print("  JPG renamed to {}".format(newf))
            copy_or_move_file_to_new_dest_dir(newf,mode,destination+"/DCIM")  
        else:
            copy_or_move_file_to_new_dest_dir(f,mode,destination+"/DCIM")  
            
    # If picture is taken with camera and is a thumb
    elif (picture_taken_with_camera) and (picture_taken_with_camera_thumb):
        copy_or_move_file_to_new_dest_dir(f,mode,destination+"/DCIM/thumbs")
        
    # If picture is not taken with camera and is not at thumb
    else:
        copy_or_move_file_to_new_dest_dir(f,mode,destination)
    
    print 
    # 1. Is a picture
    # 2. Is a thumb
    # 3. Rename
        #newdate=${videoexif_date// /_}
        #newdate2=${newdate//:/-}
        #echo $newdate2.$extension
        #mv -v "$line" "`pwd`/videos/$newdate2.$extension"
    # 4. Check jpeginfo WARNING/ERROR
    # 5. cp/mv to folder

# Check for date taken or exif DateTimeModified EXIF tags and rename image
# and return new path.
def check_jpg_date_taken_and_rename(idx,f,metadata):

    newf = False
    
    # Parse filename and extension
    # /path/to/file.jpg
    #
    # -> basename file.jpg
    # -> filename = file
    # -> filextension = .jpg
    basename = os.path.basename(f)
    filename, filextension = os.path.splitext(basename)
    
    #Extract basename from f
    oldpath = re.sub(basename,'',f)
    # -> oldpath /path/to/
    
    if metadata.has_key('EXIF:DateTimeOriginal'):
        # u'EXIF:DateTimeOriginal': u'2012:06:23 02:19:19'
        # u'File:FileModifyDate': u'2012:06:23 02:19:19+03:00'
        DateTimeOriginal = metadata['EXIF:DateTimeOriginal']
        # Convert ':' to '-'
        DateTimeOriginal = re.sub(':','-', DateTimeOriginal)
        # Convert ' ' to '_'
        DateTimeOriginal = re.sub(' ','_', DateTimeOriginal)        
        # Convert '+' to '_'
        #DateTimeOriginal = re.sub('\+','_', DateTimeOriginal)        

        newf = oldpath+DateTimeOriginal+"_"+str(idx)+".jpg"
        shutil.move(f,newf)
        
    elif metadata.has_key('EXIF:CreateDate'):
        # u'EXIF:CreateDate': u'2012:06:23 02:19:19'
        # u'File:FileModifyDate': u'2012:06:23 02:19:19+03:00'
        CreateDate = metadata['EXIF:CreateDate']
        # Convert ':' to '-'
        CreateDate = re.sub(':','-', CreateDate)
        # Convert ' ' to '_'
        CreateDate = re.sub(' ','_', CreateDate)        
        # Convert '+' to '_'
        CreateDate = re.sub('\+','_', CreateDate)        

        newf = oldpath+CreateDate+"_"+str(idx)+".jpg"
        shutil.move(f,newf)

    return newf
        
def copy_or_move_file_to_new_dest_dir(f,mode,destination):
    
    create_folder_if_does_not_exists(destination)
    # Parse filename and extension
    # /path/to/file.jpg
    # -> basename file.jpg
    # -> filename = file
    # -> filextension = .jpg
    basename = os.path.basename(f)
    filename, filextension = os.path.splitext(basename)
    
    newdestination = destination+"/"+filename+filextension
    #Check if file already exists in destination folder
    if (os.path.isfile(newdestination)):
        print "File exists do not copy/move!"
    
    else:
        
        if mode == "mv":
            print("  Moving file")
            print("    '{}'".format(f))
            print("    to")
            print("    '{}'".format(newdestination))
            shutil.move(f,newdestination)
                       
        elif mode == "cp":
            print("  Copying file")
            print("    '{}'".format(f))
            print("    to")
            print("    '{}'".format(newdestination))
            shutil.copyfile(f,newdestination)
            
        else:
            print "Unkown mode '{}'!".format(mode)
           
# Main

AllFiles = []

# Create destination directory if it doesn't exists
create_folder_if_does_not_exists(os.path.abspath(args.destination))

print "Getting list of all files in path '{}'. This might take a while...".format(os.path.abspath(args.source))
# Get all Files
AllFiles = recursive_glob(os.path.abspath(args.source),'*')
AllFilesLen = len(AllFiles)-1

# Get all files metadata and process files accordingly
for idx, f in enumerate(AllFiles):
    procentage = math.ceil(float(idx) / float(AllFilesLen) * 100)
    print
    print("Proccessing file [{}/{}] ({}%): {}".format(idx,AllFilesLen,procentage,format(f)))
    # For one file at the time, get exif metadata
    metadata = get_exif_metadata(f)
    # If MIME Type is found from metadata, process accordingly...
    if metadata.has_key('File:MIMEType'):

        # Split registry/name to own variable
        # e.g. image/jpeg
        mediatype,name = metadata['File:MIMEType'].split("/")
        #print "File type is {}/{}".format(mediatype),format(name)
        #The following information is related to MIME Media-Types:
        #
        #The "media-types" directory contains a subdirectory for each content
        #type and each of those directories contains a file for each content
        #subtype.
        #
        #                 |-application-
        #                 |-audio-------
        #                 |-image-------
        #   |-media-types-|-message-----
        #                 |-model-------
        #                 |-multipart---
        #                 |-text--------
        #                 |-video-------
        #                       
        # Since python doesn't have switch/case let's just do if elif else
        # to hadle different media types
        
        # Create folder in destination for mediatype and name type
        create_folder_if_does_not_exists(os.path.abspath(args.destination)+"/"+mediatype)
        newdestination = os.path.abspath(args.destination)+"/"+mediatype+"/"+name
        create_folder_if_does_not_exists(newdestination)
       
        if mediatype == "application":
            # Do stuff for applications
            print "application"
            copy_or_move_file_to_new_dest_dir(f,args.mode,newdestination)

        elif mediatype == "audio":
            # Do stuff for audio
            print "audio"
            copy_or_move_file_to_new_dest_dir(f,args.mode,newdestination)
            
        elif mediatype == "image":
            if name == "jpeg":
                print "  File type image/jpeg"
                process_jpg_files(idx,f,metadata,newdestination,args.mode)
            else:
                copy_or_move_file_to_new_dest_dir(f,args.mode,newdestination)
        
        elif mediatype == "message":
            # Do stuff for message
            print "message"
            copy_or_move_file_to_new_dest_dir(f,args.mode,newdestination)

        elif mediatype == "model":
            # Do stuff for model
            print "model"
            copy_or_move_file_to_new_dest_dir(f,args.mode,newdestination)

        elif mediatype == "multipart":
            # Do stuff for multipart
            print "multipart"
            copy_or_move_file_to_new_dest_dir(f,args.mode,newdestination)
            
        elif mediatype == "text":
            # Do stuff for text
            print "text"
            copy_or_move_file_to_new_dest_dir(f,args.mode,newdestination)
            
        elif mediatype == "video":
            # Do stuff for video
            print "video"  
            copy_or_move_file_to_new_dest_dir(f,args.mode,newdestination)      
            
        else:
            # MIME type is a non-standard type. Do something to them too!
            print "non-standard mime type"
            create_folder_if_does_not_exists( \
            os.path.abspath(args.destination)+"/non-standard-files/" \
            )
            copy_or_move_file_to_new_dest_dir(\
                f, \
                args.mode, \
                os.path.abspath(args.destination)+"/non-standard-files/" \
                )
    #else:
        # Do stuff for files without MIME information
        #print "  No MIME Type found, do nothing..."

