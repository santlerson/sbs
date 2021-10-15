 # Shmoosey's Backup Software

A tool for making remote, yet encrypted secure backups on Google Drive.

~~~
Usage: sbs [OPTIONS] COMMAND [ARGS]...

Options:
  -c, --config TEXT        Path to config file
  -v, --verbose / --quiet  Verbose
  --help                   Show this message and exit.

Commands:
  backup
  generate-config
  restore
~~~

SBS will automatically back up ann 
encrypted form of your files to Google Drive.

Backup in two simple steps:

## Config generation

~~~
sbs generate-config
~~~
As the command suggests, generates configuration.
It accomplishes this by asking the user a series of questions.
It is entirely ok to accept all the default options.

## Backup
~~~
sbs backup
~~~
Automatically performs a backup using the default backup path.

Should you want to back up using a different config, supply the path:
~~~
sbs -c /path/to/config.json backup
~~~

The software will automatically iterate through all files and directories
to only find files which are yet to be uploaded.


## Restoration
In order to restore a file, or an entire directory,
simply type
~~~
sbs restore
~~~
The program will guide you through a series of menus to 
select the file or directory you wish to restore. The files are restored to 
the restoration directory, specified in you config.json.

##Path Exclusion

~~~
{
    "backup_path": "/path/to/backup",
    "credentials_dir": "/any/empty/directory",
    "exclude": [
        "/path/to/excluded/root/dir"
    ],
    "key_path": "/path/to/aes/key",
    "log_dir": "/path/to/log/dir",
    "parent_id": "parent-id",
    "restore_dir": "/restore/dir",
    "version": "1.1.1"
}
~~~

Above is an example of a config file. All
the values are filled in at generation except "exclude". You may
leave this as default, or fill in a list of comma separated paths to directories you wish to exclude from the backup
(large, dynamic, non-critical files, e.g. VM disks).
