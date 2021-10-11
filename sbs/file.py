import os


class File:

    def __init__(self, is_dir: bool, parent, name: str):
        """
        Object to represent file tree for navigating the restore menus in navigator.py
        @param is_dir: whether or not file is directory (which can have children)
        @param parent: parent file whence file came
        @param name: file / directory name
        """
        self.is_dir = is_dir
        self.parent = parent
        self.name = name
        if is_dir:
            # Directories start without children
            self.children = []

    def add_child(self, child: str, isdir: bool):
        """
        Make new file as child
        @param child: name of file
        @param isdir: whether file is directory
        @return: file object of child
        """
        file = self.contains(child)
        if self.is_dir and not file:
            file = File(isdir, self, child)
            self.children.append(file)
        return file

    def contains(self, child: str):
        """
        Checks if dir has child of a particular name
        @param child: name of child
        @return: File object if child exists otherwise false.

        Consider changing False to None
        """
        for c in self.children:
            if c.name == child:
                return c
        return False

    def get_full_path(self):
        if self.parent is None:
            return self.name
        else:
            return os.path.join(self.parent.get_full_path(), self.name)

    def update_from_split_list(self, split_list: list):
        """
        Recursive function to create file tree.
        @param split_list: Split string containing parts
        """
        is_dir = len(split_list) > 1  # if list is greater than one, first file is dir
        child = self.add_child(split_list.pop(0), is_dir)
        if is_dir:
            child.update_from_split_list(split_list)

    def __repr__(self):
        return self.name

    @staticmethod
    def from_path_list(path_list: list):
        """
        Generates file tree from list of paths
        @param path_list: List of paths os files
        @return: File object representing file tree for navigator.py
        """
        root = File(True, None, ".")
        split_list_list = [path.split(os.path.sep) for path in path_list]
        for split_list in split_list_list:
            if split_list[0] == ".":
                split_list.pop(0)
            root.update_from_split_list(split_list)
        return root
