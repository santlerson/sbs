import os.path

import click
from sbs.file_manager import *
from sbs.config import *
from sbs.navigator import Navigator


@click.group()
@click.option("--config", "-c", default=get_data_dir() / "config/config.json", help="Path to config file")
@click.option("--verbose/--quiet", "-v", default=False, help="Verbose")
@click.pass_context
def cli(context, config, verbose):
    context.ensure_object(dict)
    try:
        context.obj["config"] = Config(cfg_path=config)
        context.obj["cfg_path"] = config
        if verbose:
            print("Found config")
    except FileNotFoundError:
        if verbose:
            print("Found no config!")


@cli.command()
@click.option("--do/--dont", default=True, help="Whether or not to do backup, if not, perform file check")
@click.option("--unique/--not-unique", default=False, help="Whethxer it is first backup (helps time-wise)")
@click.option("--limit", default=-1, help="Limit in bytes to backup size")
@click.pass_context
def backup(context, do: bool, unique: bool, limit: int):
    """
    Creates backup
    """
    config: Config = context.obj["config"]
    parent_id = config.parent_id
    fm = FileManager(config=config, key_file=config.key)
    if limit<0:
        fm.backup(config.backup_path, do=do, limit=None, unique=unique, exclude_list=config.exclude,
                  config=config)
    else:
        fm.backup(config.backup_path, do=do, limit=limit, unique=unique, exclude_list=config.exclude,
                  config=config)
    if not parent_id:
        config.dump(context.obj["cfg_path"])


@cli.command()
def generate_config():
    """
    Generates config file by asking the user questions
    """
    generate_config_by_questions()


@cli.command()
@click.option("--restore-path", "-p", help="Path for restoration of files")
@click.pass_context
def restore(context, restore_path):
    """
    Restores files to restore path
    """
    config: Config = context.obj["config"]

    if restore_path is None:
        restore_path = config.restore
    navigator = Navigator(config.key, config)
    backups = navigator.fm.list_backups()
    bu = None
    for backup in backups:
        file_list = backup.get_files_list()
        print(file_list)
        if os.path.normpath(backup.source) == os.path.normpath(config.backup_path) and file_list:
            bu = backup
            break
    navigator.navigate(bu, restoration_path=restore_path)


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
