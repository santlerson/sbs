from sbs.file import File
from sbs.colors import *
from sbs.file_manager import *
from sbs.backup import *


class Navigator:
    def __init__(self, key_file: str, config):
        """
        Class to allow navigation of backup in the event of a partial or full restore
        @param key_file: Path to AES key file
        """
        self.fm = FileManager(key_file=key_file,config=config)

    def navigate(self, bu: Backup, file_tree=None, restoration_path=None):
        """
        Navigate particular backup
        @param bu: Backup obj
        @param file_tree: File tree for recursion
        @param restoration_path: path to restore to
        """
        if file_tree is None:
            file_list = bu.get_files_list()
            file_tree = File.from_path_list([f.get("source") for f in file_list])
        misc_options = [
            "Download whole directory {}".format(color(file_tree.get_full_path(), CYAN)),
            "{} {}".format(color("<--", WARNING), color(file_tree.parent.name, CYAN)) if file_tree.parent else None
            # option to go back

        ]
        option_whole_dir = len(file_tree.children)  # option after all others
        option_navigate_back = len(file_tree.children) + 1 if file_tree.parent else None  # second after all others
        total_options = len(misc_options) + len(file_tree.children)

        for child, index in zip(file_tree.children, range(len(file_tree.children))):
            print("[{}]: {}".format(index, color(child.name, CYAN if child.is_dir else GREEN)))
        for option, index in zip(misc_options, range(len(file_tree.children), total_options)):
            # When option is None, do not print
            if option:
                print("[{}]: {}".format(index, option))
        done = False
        error_message = color("Please type an integer between 0 and {}".format(total_options), FAIL)
        while not done:
            # Iterate until valid input is met
            i = input("{} > ".format(color(file_tree.get_full_path(), CYAN)))
            try:
                i = int(i)
            except ValueError:
                # Case that input is not integer
                print(error_message)
                continue
            if i < 0 or i >= total_options:
                # Case that integer is not in range
                print(error_message)
            else:
                # Input is valid, exit loop
                done = True
        if i < len(file_tree.children):
            child = file_tree.children[i]
            if child.is_dir:
                # Recursive call for menu navigation
                self.navigate(bu, file_tree=child, restoration_path=restoration_path)
            else:

                f = bin_search(bu.get_files_list(), path=child.get_full_path())
                if restoration_path:
                    self.fm.download_file(f, path=child.name, restoration_path=restoration_path)
                else:
                    self.fm.download_file(f, path=child.name)
        elif i == option_navigate_back:
            self.navigate(bu, file_tree.parent, restoration_path=restoration_path)
        elif i == option_whole_dir:
            self.download_whole_dir(bu, file_tree, restoration_path=restoration_path)

    def download_whole_dir(self, bu: Backup, file_tree: File, restoration_path=None, bar=None):
        close_bar=False
        if bar is None:
            size = self.get_sizes_of_dir(bu, file_tree)

            bar = tqdm(total=size, unit_scale=True, unit="B", dynamic_ncols=True)
            close_bar=True
        for child in file_tree.children:
            if child.is_dir:
                self.download_whole_dir(bu, child, restoration_path=restoration_path, bar=bar)
            else:

                self.fm.download_file(bin_search(bu.get_files_list(), path=child.get_full_path()), bar=bar,
                                      restoration_path=restoration_path)
        if close_bar:
            bar.close()

    def get_sizes_of_dir(self, bu: Backup, file_tree: File):
        total_size = 0
        for child in file_tree.children:
            if child.is_dir:
                total_size += self.get_sizes_of_dir(bu, child)
            else:
                file_resource = bin_search(bu.get_files_list(), path=child.get_full_path())
                total_size += file_resource.get("total_size")
        return total_size
