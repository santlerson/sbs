import os.path

import click
from sbs.file_manager import *
from sbs.config import *
from sbs.navigator import Navigator
from sbs.colors import *
from sbs.menu import *

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
@click.option("--debug / --not-debug", default=False, help="Whether or not to debug (choose backup).")

@click.pass_context
def backup(context, do: bool, unique: bool, limit: int, debug: bool):
    """
    Creates backup
    """
    config: Config = context.obj["config"]
    parent_id = config.parent_id
    fm: FileManager = FileManager(config=config, key_file=config.key)
    if debug:
        options = []
        chosen_backups = []
        for backup in fm.list_backups()[:10]:
            try:
                options.append( f"{str(backup)}; {backup.get_full_backup_size()} bytes")
                chosen_backups.append(backup)


            except:
                pass
        bu=chosen_backups[menu(options, default=0)]
    else:
        bu=None
    if limit < 0:
        fm.backup(config.backup_path, do=do, limit=None, unique=unique, exclude_list=config.exclude,
                  config=config, previous_backup=bu)
    else:
        fm.backup(config.backup_path, do=do, limit=limit, unique=unique, exclude_list=config.exclude,
                  config=config, previous_backup=bu)
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
@click.option("--debug / --normal", help="Whether or not to choose backup to restore (for debugging).")
@click.pass_context
def restore(context, restore_path, debug: bool):
    """
    Restores files to restore path
    """
    config: Config = context.obj["config"]

    if restore_path is None:
        restore_path = config.restore
    navigator = Navigator(config.key, config)
    backups = navigator.fm.list_backups()

    bu = None
    for back_up in backups:
        if back_up.get_files_list():
            bu = back_up
            break
    navigator.navigate(bu, restoration_path=restore_path)


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
