#!/usr/bin/env python3

# iOS file backup script v0.5
# Copyright (C) 2021 MisplacedDevelopment
# Function get_bookmark_paths() adapted from https://github.com/zrzka/blackmamba
# which is Copyright (c) 2017 Robert Vojta (@robertvojta) and uses the same MIT
# license as this script.  See LICENSE for license information
#
# Use this script at your own risk!  Ensure that you read the
# code and understand exactly what it will do before running it. 

import plistlib
import time
import os
import re
import sys
import console
import tarfile
from objc_util import ns, NSURL
import atexit
import platform
import glob


### SCROLL DOWN to user-configurable parameters! ###


class Backup(object):
  def __init__(self, friendlyName):
    self.friendlyName = friendlyName
    self.allowedFiles = []
    self.bannedFiles = []
    self.allowedDirs = []
    self.bannedDirs = []
    self.maxFileSizeWarn = None
    self.maxFileSizeFail = None
    self.warnCount = 0
    
  def checkPattern(self, name, allowedItems, bannedItems):
    # If there are items in allowedItems then the file *must* match one of them
    for pattern in allowedItems:
      if re.search(pattern, name):
        debugPrint(" INCLUDE: Matches include pattern {}".format(pattern))
        return True
    
    # If allowedItems is not empty and we get here then this can't be an an allowed item
    if allowedItems:
      debugPrint(" EXCLUDE: Did not match any of the allowed filters")
      return False
    
    # Note that allowedItems takes precedence over bannedItems  
    for pattern in bannedItems:
      if re.search(pattern, name):
        debugPrint(" EXCLUDE: Matches exclude pattern {}".format(pattern))
        return False
        
    # Not banned or specifically allowed so allow
    debugPrint(" INCLUDE: default rule")
    return True    
    
  def shouldInclude(self, tarInfo):
    name = tarInfo.name
    if tarInfo.isfile():
      fileSize = tarInfo.size
      
      if self.maxFileSizeWarn and fileSize > self.maxFileSizeWarn:
        print(" WARN: File size {} > warn size {}".format(fileSize, self.maxFileSizeWarn))
        self.warnCount += 1
      
      if self.maxFileSizeFail and fileSize > self.maxFileSizeFail:
        quitWithError(" File {}, size {} > max size {}".format(name, fileSize, self.maxFileSizeFail))
      
      return self.checkPattern(name, self.allowedFiles, self.bannedFiles)
          
    elif tarInfo.isdir():
      return self.checkPattern(name, self.allowedDirs, self.bannedDirs)
    
    # This is neither a file or directory.  User can decide whether to include it
        
    debugPrint(" WARN: Found something that is not a file or directory of type {} ".format(tarInfo.type))
    if bIgnoreNonFileOrDir:
      debugPrint(" EXCLUDE: Ignoring")
      return False
    else:
      debugPrint(" INCLUDE: Including")
      return True

def atexitFunc():
  if bWriteToFile:
    newStdout.close()
    sys.stdout = origStdout
    
atexit.register(atexitFunc)

_BOOKMARKS_FILE = os.path.expanduser('~/Bookmarks.plist')
TIMESTAMP = time.strftime("%Y%m%d-%H%M%S")
ROOT_DIR = os.getcwd()
MACHINE_ID = platform.node()
WORKING_DIR = os.path.join(ROOT_DIR, "{}".format(MACHINE_ID), "{}".format(TIMESTAMP))
  
####################################
### User-configurable parameters ###
####################################

## Dump paths ## - Use this to dump the internal path names for the paths added in EXTERNAL FILES.
               #   Use this information to update PATH_MAP and then when you are happy, set it
               #   to False and the script will switch to backup mode.
bPathDumpMode = True

## Debug mode ## - Make the output more verbose
bDebug = True

## Ignore non-file/dir ## - If a file is neither a file or a directory (see TarInfo.type) then by
                        #   default the file is excluded from the archive.  Override that behaviour here.
bIgnoreNonFileOrDir = True

## Write to file ## - By default the script will put its output to a log file.  Override that behaviour here.
bWriteToFile = True

# Use the script with bPathDumpMode set to get some values to plug into this section
# If you know what you are doing then you may want to move this configuration outside
# of the script in case you update the script in future.
if True:
  # EXAMPLE USES:
  # Define a backup configuration for NS2, using the friendly name "NS2"
# NS2Backup = Backup("NS2")
  # I do not want to include any jpg files in my backup
# NS2Backup.bannedFiles = ["\.jpg"]
  # I *only* want to back up this project folder
# NS2Backup.allowedDirs = ["Untitled\.prj"]
  # I want a warning to be added to the output if any of the files I archive
  # are larger than 300K bytes in size
# NS2Backup.maxFileSizeWarn = 300000
  
# AUMBackup = Backup("AUM")
  # I *only* want to archive .aumproj files
# AUMBackup.allowedFiles = ["\.aumproj"]
# AUMBackup.maxFileSizeWarn = 1000000
  
# StaffPadBackup = Backup("StaffPad")
# StaffPadBackup.allowedFiles = ["\.stf"]
  # I do not want to back up these folders.
# StaffPadBackup.bannedDirs = ["Templates", "\.Trash", "\.thumbnails"]
# StaffPadBackup.maxFileSizeWarn = 200000
  
  # Key is a regex.  If this matches any of the Pythonista "External Files" then
  # the map value will be used to name the archive rather than the name as it 
  # appears in "External Files".
  # Note that you can reuse backup configurations.  Here I have two iPads with
  # different application paths and so I configure both sets so that the script
  # can be run to back up correctly regardless of which iPad I run it from.
# PATH_MAP = { ".*ABA9AB34-5BC8-4A57-2353-CA62CCABC903.*/Projects" : NS2Backup,
#              ".*90900E45-01E0-4D01-AFAB-BC82B7E92E57.*/Projects" : NS2Backup,
#              ".*A1BD7CE0-9132-4384-A306-9E50F5BA4EDD.*" : AUMBackup,
#              ".*6592BB30-D446-403D-A21B-225431BC0A0E.*" : AUMBackup,
#              ".*StaffPad.*" : StaffPadBackup}

  # By default everything is archived from each backup source and
  # the backup names are picked on a best-can-do basis
  PATH_MAP = {}
else:  
  PATH_MAP = {}

########################################
### END User-configurable parameters ###
########################################

def createPath(path):
  try:
    if(not os.path.exists(path)):
      os.makedirs(path)
  except OSError:
    quitWithError("ERROR: Could not create path {}".format(path))

def cleanStringForFile(stringToClean):
  cleanedString = ""
  if(stringToClean):
    cleanedString = "".join(thisChar for thisChar in stringToClean if (thisChar.isalnum() or thisChar in "._-"))
  return cleanedString

def createBackupFileName(backupName):
  return cleanStringForFile("{}_{}.tar.gz".format(backupName, TIMESTAMP))
 
def quitWithError(errorString):
  print(errorString)
  console.hud_alert(errorString, 'error', 4)
  sys.exit(1)

def debugPrint(stringToPrint):
  if(bDebug): print(stringToPrint)
  
def filter_function(tarInfo, backupDefinition, rootFolder):
  debugPrint("Filter on {}".format(tarInfo.name))
  # We always allow the root folder.  If we do not then the
  # processing ends immediately since it is clever enough to
  # know that if we exclude the root folder then we don't need to
  # look at any of its contents
  if tarInfo.name == rootFolder:
    debugPrint(" INCLUDE: Always match root folder {}".format(rootFolder))
    return tarInfo
    
  if backupDefinition:
    if backupDefinition.shouldInclude(tarInfo):
      return tarInfo
    else:
      return None
  else:
    debugPrint(" INCLUDE: default action")
    return tarInfo

def get_bookmark_paths():
  if not os.path.isfile(_BOOKMARKS_FILE):
    return []

  with open(_BOOKMARKS_FILE, 'rb') as in_file:
    content = plistlib.readPlist(in_file)

    if not content:
      return []

    paths = []
    for data in content:
      url = NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(
          ns(data.data), 1 << 8, None, None, None
      )
      if url and url.isFileURL():
        paths.append(str(url.path()))

    return paths

### START OF MAIN ###
        
createPath(WORKING_DIR)
os.chdir(WORKING_DIR)

if bWriteToFile:
  origStdout = sys.stdout
  newStdout = open("fileBackup_Log_{}.log".format(TIMESTAMP), 'w')
  sys.stdout = newStdout
        
bookmarkPaths = get_bookmark_paths()

if(not bookmarkPaths):
  quitWithError("No backup sources found.  Add files or folders to EXTERNAL FILES in Pythonista.")

# User wants to see what the EXTERNAL FILES look like so they
# can create appropriate PATH_MAP entries
if bPathDumpMode:
  usedBackupNames = []
  print("PATH DUMP MODE")
  print("==============")
  print()
  # Print each bookmark path along with first 5 files or folders found under each path
  for path in bookmarkPaths:
    # Skip backup log files...
    if("fileBackup_Log" in path):
      continue
  
    print("PATH:{}".format(path))
    
    backupName = os.path.basename(os.path.normpath(path))
    print("Example backup file name if no friendly name is defined: {}".format(createBackupFileName(backupName)))
    if(backupName in usedBackupNames):
      print("**NOTE** {} will be used in the backup file name.  This name was also found for one of your other backup locations and so you should ensure that it has a friendly named defined.".format(backupName))
    else:
      usedBackupNames.append(backupName)
    
    paths = glob.glob(os.path.join(path, "*"))
    if paths:
      print("A sample of files from this path:")
    
    fileCount = 5
    for file in paths:
      if fileCount <= 0: 
        break
      baseName = os.path.basename(file)
      print(" |_ {}".format(baseName))
      fileCount -= 1
    
    print()
      
  sys.exit()
  
usedBackupNames = []

print("BACKUP MODE")
print("===========")
print()  
for path in bookmarkPaths:
  if "fileBackup_Log" in path:
    debugPrint("Skipping backup log")
    continue

  rootFolder = os.path.basename(os.path.normpath(path))  
  backupName = rootFolder
  backupDefinition = None
  # Do we have a backup definition for this path?
  for key, value in PATH_MAP.items():
    if re.search(key, path):
      debugPrint("Path {} matches pattern {} so using friendly name {}.".format(path, key, value.friendlyName))
      backupName = value.friendlyName
      backupDefinition = value
  
  # Attempt to make name unique if the root folder is the same as
  # a backup we have already processed
  if backupName in usedBackupNames:
    debugPrint("WARN: Already using backupName {}".format(backupName))
    backupName = "{}{}".format(backupName, time.time())
  
  print()
  print("--BACKING UP-- Folder {} using name {}".format(rootFolder, backupName))
  print()
  archiveName = createBackupFileName(backupName)
  archive = tarfile.open(archiveName, "w:gz")  
  archive.add(path, arcname=rootFolder, recursive=True, filter=lambda filterFile: filter_function(filterFile, backupDefinition, rootFolder))
  archive.close()
  usedBackupNames.append(backupName)
  print()
  print("--FILE WRITTEN-- {} of size {}".format(archiveName, os.stat(archiveName).st_size))
  print()
  
