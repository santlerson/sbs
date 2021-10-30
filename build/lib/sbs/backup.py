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

    def __repr__(self):
        return "<Backup of {} uploaded {}>".format(self.source, ctime(self.time))

    def get_files_list_deprecated(self):
        if self.files_list is None:
            files = self.service.files().list(q="'{}' in parents".format(self.id)).execute()['files']
            for file in files:
                if self.c.decrypt_name(file.get("name")) == "backup.json":
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
                    self.files_list = sorted(data, key=lambda file: file.get("source"))
        return self.files_list

    def get_files_list(self):

        if self.files_list is None:
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
                    self.files_list = sorted(data.get("files"), key=lambda file: file.get("source"))
                    print(self.files_list)
        return self.files_list

    def find_file_by_digest(self, digest: str):
        print("^", end=" ")

        return bin_search(self.get_digest_list(), digest, key=lambda file: file.get("digest"))

    def find_file_by_path(self, path: str):
        by_path = bin_search(self.get_files_list(), path)
        if by_path: return by_path
        return None

    def get_digest_list(self):
        if self.files_list_by_digest:
            return self.files_list_by_digest
        else:
            print("\nSorting digest list")
            self.files_list_by_digest = sorted(self.get_files_list(), key=lambda file: file.get("digest"))
            return self.files_list_by_digest


def bin_search(arr: list, path: str, start=0, end=None, key=lambda file: file.get('source'), n=0):
    if end is None:
        end = len(arr) - 1
    pivot = int((start + end) / 2)
    if key(arr[pivot]) == path:
        return arr[pivot]
    if start >= end:
        return None

    try:
        if key(arr[pivot]) < path:
            return bin_search(arr, path, start=pivot + 1, end=end, n=n + 1)
        else:
            return bin_search(arr, path, start=start, end=pivot - 1, n=n + 1)
    except Exception:
        print("Recursion Depth: {}".format(n))
        print("Length of Array: {}".format(len(arr)))
        print("Length of Remaining Search: {} (indexes {}-{})".format(end - start, start, end))

        raise KeyboardInterrupt
