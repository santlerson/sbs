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
        if verbose:
            print("Found config")
    except FileNotFoundError:
        if verbose:
            print("Found no config!")


@cli.command()
@click.option("--do/--dont", default=True, help="Whether or not to do backup, if not, perform file check")
@click.option("--unique/--not-unique", default=False, help="Whether it is first backup (helps time-wise)")
@click.pass_context
def backup(context, do: bool, unique: bool):
    config: Config = context.obj["config"]
    fm = FileManager(config=config, key_file=config.key)

    fm.backup(config.backup_path, do=do, limit=None, unique=unique, exclude_list=config.exclude,
              config=config)


@cli.command()
def generate_config():
    generate_config_by_questions()


@cli.command()
@click.option("--restore-path", "-p", help="Path for restoration of files")
@click.pass_context
def restore(context, restore_path):
    config: Config = context.obj["config"]

    if restore_path is None:
        restore_path = config.restore
    navigator = Navigator(config.key, config)
    backups = navigator.fm.list_backups()
    bu = None
    for backup in backups:
        file_list = backup.get_files_list()
        if os.path.normpath(backup.source) == os.path.normpath(config.backup_path) and file_list:
            bu = backup
            break
    navigator.navigate(bu, restoration_path=restore_path)


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
