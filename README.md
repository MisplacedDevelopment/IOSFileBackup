# IOSFileBackup
Simple Pythonista script for file backup on iOS.  The use case for this script is to back up small but important files.  Not all applications use iCloud and a device failure could mean that important files are lost.  I also use it to take point in time snapshots of files which *are* backed up in iCloud in case any are accidentally deleted or are written with unwanted changes.

Use this script at your own risk.  You should check that what you think is being backed up really is being backed up!

Tested on iPad 7/Air 4 using iOS 14.4.

# Features
* Back up files or folders from your iOS device to iCloud
* Stores backups by device name so multiple devices can be backed up alongside each other.
* Use allowed/banned lists to allow or disallow files or directories using regular expressions

# How to use
## Installation
1. Install http://omz-software.com/pythonista/ from the iOS app store.  This is not free and there may be other lower cost/free options but this is what the tool was developed and tested with.
1. Download the filebackup.py script from this site, or clone the project on iOS using [Working Copy](https://workingcopyapp.com)
1. Load the script into Pythonista. **IMPORTANT** You must copy to and run the script from the Pythonista folder, i.e. somewhere under iCloud Drive/Pythonista 3, otherwise you will not have permission to write the backup data.

## First time use
The script uses everything defined under the Pythonista "EXTERNAL FILES" section as source locations for backup.  To begin, make sure that any folders and files that you do not want to back up are removed from this section.  Add a folder that you would like to back up using "EXTERNAL FILES -> Open... -> Folder...".  The whole folder will be archived by default.

The script is by default set to "path dump" mode.  This mode is used to help you create backup definitions.  Try running the script.  You should find that a folder is created in the same folder as the filebackup.py file which matches the name of your iOS device.  In this folder there should be a sub-folder containing the date and in here there should be a log file.

Open this log file and you will see something like this:

```
PATH:/private/var/mobile/Containers/Data/Application/919ACEC5-05E3-4D01-AE36-BCE432E92E57/Documents/Projects
Example backup file name if no friendly name is defined: Projects_20210306-123413.tar.gz
A sample of files from this path:
 |_ Untitled.prj
 ```
 
 You now have enough information to create a backup definition.  Edit the script and look for the `PATH_MAP` variable:
 
 ```
 PATH_MAP = { ".*919ACEC5-05E3-4D01-AE36-BCE432E92E57.*/Projects" : MyNewBackup}
```

This is a dictionary map where the key is a regular expression which should match the PATH that you see in the log file.  The value should be a variable of type `Backup`, e.g.

 ```
 MyNewBackup = Backup("MyNewBackup")
 PATH_MAP = { ".*919ACEC5-05E3-4D01-AE36-BCE432E92E57.*/Projects" : MyNewBackup}
```

The parameter passed to the `Backup` constructor is the friendly name of the backup and is what is used when naming the backup archive.  Why do this?  Once you have a few backups defined you will notice that they may have the same root folder name.  Without a friendly name then it will not be clear which backup each archive refers to.

If you now set `bPathDumpMode = False` then the script will be set to backup mode.  If the script is now run then you should see that a new folder is created with the current date/time and inside that is an archived version of the backup source location.

## Backup options
*WARNING* If you update the script then remember to save your configuration somewhere else first otherwise you may accidentally overwrite it!

The `Backup` class has a number of other properties which can be set to control which files and folders are backed up (or not).  There are some examples in the code but here is a description for each:
    
```
    NOTE: the allowed/banned lists below are string lists where each element is interpreted as an re.search type of regular expression.
    
    Backup.allowedFiles - *Only* the files in this list will be added to the archive.
    Backup.bannedFiles - *Any* files matching an entry in this list will be excluded from the archive.
    Backup.allowedDirs = *Only* the directories in this list will be added to the archive.
    Backup.bannedDirs = *Any* directory matching and entry in this list will be excluded from the archive
    Backup.maxFileSizeWarn = Print a warning if any file exceeds this size (in bytes)
    Backup.maxFileSizeFail = Fail the script if any file exceeds this size (in bytes)
```

The `allowedFiles/Dirs` properties take precedence over the banned versions.  If a file matches one of these then it is included even if it might have also matched something in the banned list.

If a folder is excluded then all of its child folders and files are also excluded, even if they might have matched something in one of the allowed lists.

A `Backup` definition can be used for multiple backup paths.  This may be useful if you have the same application being backed up from multiple devices, where each has a different internal path but the same backup configuration requirements.

## Limitations
This is a very barebones solution.  It has not been through rigorous testing and I do not know how/whether it copes with many thousands of files or very large files.

There a number of features that could be added:
* Save to somewhere other than the iCloud
* User interface
* Decouple backup configuration from script
* Restore mode
* Instructions for creating scheduled backups


