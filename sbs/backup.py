from sbs.stoof import Cryptologor
import json
from time import ctime
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload
from tqdm import tqdm
from sbs.values import *


class Backup:
    def __init__(self, service, file: map, config, c: Cryptologor = None):

        if c is None:
            self.c = Cryptologor()
        else:
            self.c = c
        self.id = file['id']
        self.service = service
        json_map = json.JSONDecoder().decode(c.decrypt_name(file.get('name')))
        self.source = json_map.get("dir")
        self.time = json_map.get("time")
        self.files_list = None
        self.files_list_by_digest = None
        self.pointer = 0
        self.total_size = None
        self.files_map = None

    def __repr__(self):
        return "<Backup of {} uploaded {}>".format(self.source, ctime(self.time))



    def get_files_list(self):

        if self.files_map is None:
            files = self.service.files().list(spaces="appDataFolder", q="'{}' in parents".format(self.id)).execute()[
                'files']
            for file in files:
                if self.c.decrypt_name(file.get("name")) == "backup_{}.json".format(VERSION_CODE):
                    request = self.service.files().get_media(fileId=file.get('id'))
                    fh = BytesIO()
                    downloader = MediaIoBaseDownload(fh, request, chunksize=CHUNK_SIZE)
                    done = False
                    bar = tqdm(total=1)
                    total = 0
                    while done is False:
                        status, done = downloader.next_chunk()
                        progress = status.progress()
                        bar.update(progress - total)
                        total = progress
                    bar.update(1 - total)
                    bar.close()
                    fh.seek(0)
                    json_data = self.c.decrypt(fh.read()).decode("UTF-8")
                    data = json.JSONDecoder().decode(json_data)
                    self.files_map = {file.get("source"): file for file in data.get("files")}
        return self.files_map

    def find_file_by_path(self, path: str):
        self.get_files_list()
        # by_path = bin_search(self.get_files_list(), path)
        # if by_path: return by_path
        # return None
        return self.files_map.get(path)

    def get_digest_list(self):
        if self.files_list_by_digest:
            return self.files_list_by_digest
        else:
            print("\nSorting digest list")
            self.files_list_by_digest = sorted(self.get_files_list(), key=lambda file: file.get("digest"))
            return self.files_list_by_digest

    def get_full_backup_size(self):
        if self.total_size:
            return self.total_size
        else:
            self.total_size = 0
            for file in self.get_files_list():
                for piece in file.get("pieces"):
                    self.total_size += piece.get("size")
        return self.total_size


