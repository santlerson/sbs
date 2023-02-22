from typing import *
import json
import os
import sys
import pathlib

VERSION = "0.2.6"

EXAMPLE_BACKUP_PATH = "/path/to/backup"
EXAMPLE_EXCLUSION = "/path/to/excluded/root/dir"
EXAMPLE_RESTORATION_DIRECTORY = "/restore/dir"
EXAMPLE_PATH_TO_KEY = "/path/to/aes/key"
EXAMPLE_PARENT_ID = "parent-id"
EXAMPLE_CREDENTIALS_DIR = "/any/empty/directory"
EXAMPLE_LOG_DIR="/path/to/log/dir"


def get_data_dir() -> pathlib.Path:
    """
    Returns a parent directory path
    where persistent application data can be stored.

    # linux: ~/.local/share
    # macOS: ~/Library/Application Support
    # windows: C:/Users/<USER>/AppData/Roaming
    """

    home = pathlib.Path.home()

    if sys.platform == "win32":
        data_dir = home / "AppData/Roaming"
    elif sys.platform == "linux":
        data_dir = home / ".local/share"
    elif sys.platform == "darwin":
        data_dir = home / "Library/Application Support"
    return data_dir / "sbs"


def generate_config_by_questions():
    """
    Generates a config file by asking the user questions. Most of the questions can be answered using the default
    answer for ease of use.
    """
    cfg = Config()
    pwd = os.getcwd()
    default_cred_path = get_data_dir() / "creds/"
    default_key_path = get_data_dir() / "key"
    default_restore_path = get_data_dir() / "restore"
    default_cfg_dir = get_data_dir() / "config"
    default_log_dir = get_data_dir() / "logs"
    cfg.backup_path = input(f"Please enter a backup path [{pwd}]: ") or pwd
    cfg.credentials_dir = input(f"Please enter an empty directory to store Google Credentials [{default_cred_path}]: ") or default_cred_path
    cfg.key = input(f"Please enter a path to store your key [{default_key_path}]: ") or default_key_path
    cfg.parent_id = input(
        f"Please enter a Google drive file ID to use for backups (if you don't have one please leave it blank): ") or \
                    None
    cfg.restore = input(
        f"Please enter a default restoration path for your backup [{default_restore_path}]: ") or default_restore_path
    cfg.log_dir = input(f"Please enter a directory to store your logs [{default_log_dir}]: ") or default_log_dir
    cfg_dir = input(f"Please enter a path for your config file [{default_cfg_dir}]: ") or default_cfg_dir

    if not os.path.exists(cfg_dir):
        os.makedirs(cfg_dir)
    cfg_path = os.path.join(cfg_dir, "config.json")
    if os.path.exists(str(cfg_path)):
        i = 0
        done = False
        while not done:

            cfg_path = os.path.join(cfg_dir , f"config{i}.json")
            if not os.path.exists(str(cfg_path)):
                done = True
            i+=1
    cfg.dump(str(cfg_path))
    print(f"Success! Config dumped at {cfg_path}!")


class Config:


    def __init__(self, cfg_path=None):
        self.cfg_path = cfg_path
        if cfg_path is None:
            self.exclude: List[AnyStr] = [EXAMPLE_EXCLUSION]
            self.backup_path = EXAMPLE_BACKUP_PATH
            self.restore = EXAMPLE_RESTORATION_DIRECTORY
            self.key = EXAMPLE_PATH_TO_KEY
            self.parent_id = EXAMPLE_PARENT_ID
            self.credentials_dir = EXAMPLE_CREDENTIALS_DIR
            self.log_dir = EXAMPLE_LOG_DIR
            self.version = VERSION
        else:

            m = json.load(open(cfg_path, "r"))
            self.version = m.get("version")
            self.exclude = m.get("exclude")
            self.backup_path = m.get("backup_path")
            self.restore = m.get("restore_dir")
            self.credentials_dir = m.get("credentials_dir")
            self.key = m.get("key_path")
            self.parent_id = m.get("parent_id")

            self.log_dir=m.get("log_dir")

    def to_map(self):
        """

        @return: Map representing config for use in json file
        """
        return {
            "exclude": self.exclude,
            "backup_path": str(self.backup_path),
            "restore_dir": str(self.restore),
            "version": VERSION,
            "key_path": str(self.key),
            "parent_id": self.parent_id,
            "log_dir":str(self.log_dir),
            "credentials_dir":str(self.credentials_dir)
        }

    def dump(self, path=None):
        """
        Dump config object to config file to be retrieved later.
        @param path: path to dump file to
        """
        json.dump(self.to_map(), open(str(path or self.cfg_path), "w"), indent=4, sort_keys=True)


if __name__ == "__main__":
    config = Config()
    config.dump()
