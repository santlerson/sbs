import os
from socket import timeout
from typing import List

from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
from google.auth.exceptions import *
from io import BytesIO
from tqdm import tqdm
from sbs.stoof import Cryptologor
import time
import json
import random
from Cryptodome.Hash import SHA256
import base64
from sbs.sha import digest
import httplib2
from sbs.service_getter import get_service
from sbs.backup import Backup

from sbs.values import *

from threading import Thread


def check_backups(backup_list: List[Backup], path: str) -> map:
    """
    Checks all previous backups for file using digest (including those not from source directory)
    @param backup_list: List of backups
    @param path: Path to file on local machine
    @return: File (map) or None
    """
    d = digest(path)
    for backup in backup_list:
        file = backup.find_file_by_digest(d)
        if file:
            return file.copy()
    return None


def check_latest_backup_without_hash_scan(backup: Backup, relative_path: str) -> map:
    """
    Checks for file path in latest backup (only most recent backup of source directory), skips check for digest.
    This is the much faster and recommended way of looking for a file.
    This also checks that the file was uploaded after it was most recently modified.

    @param backup: Backup object to check
    @param relative_path: path to seek
    @return: File map, or none
    """

    last_modified = os.path.getmtime(relative_path)
    if last_modified > backup.time:
        return None
    return backup.find_file_by_path(relative_path)


class FileManager:
    def __init__(self, config, key_file=None):
        """
        Object to manage backups and files
        @param key_file: path to AES key
        """
        if key_file:
            self.c = Cryptologor(key_file=key_file)
        else:
            self.c = Cryptologor(key_file=config.key)
        self.service = get_service(config)
        self.config = config

    def upload_file(self, path: str, log_file, parent_id, bar=None):
        """
        Uploads file at path to folder with parent_id
        :param bar: tqdm bar in use in larger backup
        :param path: path to file to be uploaded
        :param parent_id: google drive parent id of directory to be uploaded to
        :return: SHA1 digest of file, quantity of pieces and total file size, each returned to be stored in JSON file
        """
        total_file_size = 0
        pieces = []
        sha = SHA256.new()
        in_file = open(path, "rb")
        # Read PIECE_SIZE bytes from file
        data = in_file.read(PIECE_SIZE)
        log_file.write("Uploading {}".format(path))
        piece_counter = 0

        # If no bar is supplied, meaning this is a single file upload, we make our own progress bar,
        # and be sure to close it before returning
        if bar is None:
            bar = tqdm(total=os.path.getsize("path"), unit="B", unit_scale=True, dynamic_ncols=True)
            close_bar = True
        else:
            close_bar = False

        # Exit when no more data is left to be read
        while data:

            # Digest on separate thread for TIME EFFICIENCY
            hash_thread = Thread(target=sha.update, args=(data,))
            hash_thread.start()
            encrypted_data = self.c.encrypt(data)
            size = len(encrypted_data)

            log_file.write("Uploading piece {} of size {} bytes\n".format(piece_counter, size))

            total_file_size += size
            media_body = MediaIoBaseUpload(BytesIO(encrypted_data), resumable=True, chunksize=CHUNK_SIZE,
                                           mimetype="application/octet-stream")
            # Application internal info for file is stored in Google Drive file name
            info = {
                "path": path,
                "index": piece_counter
            }

            # Google drive file metadata
            metadata = {
                "name": self.c.encrypt_name(json.JSONEncoder().encode(info)),
                "parents": [parent_id]
            }

            file = self.service.files().create(body=metadata, media_body=media_body, fields="id")

            response = None

            total = 0.0
            while response is None:
                try:
                    # Upload next chunk of file
                    status, response = file.next_chunk()
                    if status:
                        # If we get a response update progress bar (progress is a number between 0-1)
                        progress = status.progress()
                        bar.update((progress - total) * size)
                        total = progress
                except (httplib2.ServerNotFoundError, BrokenPipeError, TimeoutError, ConnectionResetError, OSError,
                        timeout, HttpError, TransportError):
                    seconds = random.randint(30, 91)
                    bar.write("Having internet troubles, waiting, {} seconds".format(seconds))
                    time.sleep(seconds)
            # Keep running list of pieces to return
            pieces.append({"id": response.get("id"),
                           "size": size})
            log_file.write("Uploaded piece {} of {} bytes\n".format(piece_counter, size))
            # Final update of bar just in case
            bar.update((1 - total) * size)

            # Read data for next iteration of loop
            data = in_file.read(PIECE_SIZE)
            piece_counter += 1
            hash_thread.join()

        if close_bar:
            bar.close()
        return sha.digest(), pieces, total_file_size

    def download_file(self, file: map, restoration_path: str, bar=None,
                      path=None):
        """
        Download and restore file
        @param file: File (map)
        @param restoration_path: path to restore to, in case of full backup restoration, should be same
                                 as source path, otherwise some other path for testing
        @param bar: Progress bar in case of large restoration
        @param path: Path to file in backup (optional)
        """

        restoration_path = os.path.abspath(restoration_path)

        # If no path is passed, find path in file map
        if path is None:
            path = file['source']

        if not os.path.exists(restoration_path):
            os.makedirs(restoration_path)
        os.chdir(restoration_path)

        if os.path.exists(path) and not os.path.isdir(path):
            sha = SHA256.new()
            with open(path, "rb") as file:
                data = file.read(PIECE_SIZE)
                while(data):
                    sha.update(data)
                    data=file.read(PIECE_SIZE)
            if base64.b64encode(sha.digest()).decode("UTF-8")==file['digest']:
                if bar is not None:
                    bar.update(file['total_size'])
                return

        # Make dirs leading to path
        if os.path.dirname(path) and not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        # Make own bar if no bar is supplied
        if bar is None:
            close_bar = True
            bar = tqdm(total=file.get("total_size"), unit_scale=True, unit="B", dynamic_ncols=True)
        else:
            close_bar = False
        out_file = open(path, "wb")

        # Iterate over all pieces in file to download whole file
        for piece, count in zip(file.get("pieces"), range(len(file.get("pieces")))):
            id = piece.get("id")
            size = piece.get("size")
            request = self.service.files().get_media(fileId=id)
            fh = BytesIO()
            downloader = MediaIoBaseDownload(fh, request, chunksize=CHUNK_SIZE)
            done = False
            total = 0.0
            while done is False:
                try:
                    
                    status, done = downloader.next_chunk()
                    if status:
                        progress = status.progress()
                        bar.update(size * (progress - total))
                        total = progress
                except (httplib2.ServerNotFoundError, BrokenPipeError, TimeoutError, ConnectionResetError, OSError,
                        timeout, HttpError, TransportError):
                    seconds = random.randint(30, 91)
                    bar.write("Having internet troubles, waiting, {} seconds".format(seconds))
                    time.sleep(seconds)
                    
            # Go to start of byteio to begin reading
            fh.seek(0)
            data = fh.read()
            # print(len(data))
            out_file.write(self.c.decrypt(data))
            # Final update of bar for piece just in case
            bar.update(size * (1 - total))
        if close_bar:
            bar.close()

    def backup(self, dir_path, exclude_list, config, do=False, unique=False, limit=5 * 10 ** 9, previous_backup: Backup=None
               ):
        """
        Performs backup of particular directory to Google Drive.
        @param dir_path: Path to do dir which is to be backed up
        @param do: Will perform backup if true, otherwise will perform backup scan
        @param unique: Will skip backup check if true
        @param hash_scan:
        @param limit: Limit of total backup size
        @param parent_id: id of directory containing backups on Google drive
        @param exclude_list: list of files to exclude (large, dynamic files for example)
        """

        if not config.parent_id:
            metadata = {
                "name": input("Please enter a folder name for your backups [Backups]: ") or "Backups",
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': ['appDataFolder']

            }

            file = self.service.files().create(body=metadata, fields="id").execute()
            config.parent_id = file.get("id")
        # Generate path to log with datetime and dir

        if not os.path.exists(config.log_dir):
            os.makedirs(config.log_dir)
        log_path = os.path.join(config.log_dir, time.ctime())
        log_file = open(log_path, "w")

        # Create link for latest log for ease of checking logs
        link_path = os.path.join(config.log_dir, "latest")
        try:
            os.unlink(link_path)
        except FileNotFoundError:
            pass
        os.symlink(log_path, link_path)
        backups = self.list_backups()
        json_list = []
        dir_path = os.path.abspath(dir_path)

        os.chdir(dir_path)

        file_list = []
        file_size = 0
        if not previous_backup:
            backup = None
            for backup in backups:
                if os.path.normpath(backup.source) == os.path.normpath(
                        dir_path) and backup.get_files_list():
                    break
            if backup is None or backup.get_files_list() is None:
                unique = True
        else:
            backup=previous_backup

        log_file.write("Beginning file check\n")
        for root, dirs, files in os.walk("."):
            exclude = False
            for exclusion in exclude_list:

                commonprefix = os.path.commonprefix([exclusion, root])
                length = len(commonprefix)

                if length > 2:
                    # checks if best common prefix is longer than "./", hence the dir is excluded
                    exclude = True  # continue in loop, skip this root directory
            # if finish: break
            if exclude:
                continue
            for file in files:
                full_path = os.path.join(root, file)
                if os.path.exists(full_path):
                    if unique:
                        backup_file = False
                    else:
                        excluded = False
                        # print("Checking {}".format(full_path))

                        backup_file: dict = check_latest_backup_without_hash_scan(backup, full_path)
                    if backup_file:
                        # print("Found {} in other backup".format(full_path))
                        # print(".",end=" ")

                        backup_file['source'] = full_path
                        if backup_file.get('size'):
                            backup_file['total_size'] = backup_file['size']
                            backup_file.pop("size")
                            log_file.write("Changed size to total_size\n")
                        json_list.append(backup_file)
                    else:
                        # print("!",end=" ")
                        log_file.write("{} not found... adding to backup\n".format(full_path))
                        current_file_size = os.path.getsize(full_path)
                        if limit and file_size + current_file_size > limit:
                            finish = True
                            # break
                        else:
                            file_list.append(full_path)
                            file_size += current_file_size

        # print("Size={Size

        file_list = sorted(file_list,
                           key=lambda x: random.random())  # randomizes order of file list for security reasons
        # print(file_list)
        if do:
            try:
                total_uploaded_bytes = 0
                m = {
                    "dir": dir_path,
                    "time": time.time()
                }
                name = json.encoder.JSONEncoder().encode(m)
                metadata = {
                    "name": self.c.encrypt_name(name),
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [config.parent_id]
                }
                file = self.service.files().create(body=metadata, fields="id").execute()
                folder_id = file.get("id")

                bar = tqdm(total=file_size, unit="B", unit_scale=True, dynamic_ncols=True)
                log_file.write("Beginning backup of size {}\n".format(file_size))
                for file in file_list:
                    try:
                        digest, pieces, size = self.upload_file(file, log_file, folder_id,
                                                                bar=bar)
                        json_list.append({
                            "source": file,
                            "digest": base64.b64encode(digest).decode("UTF-8"),
                            "pieces": pieces,
                            "uploaded": time.time(),
                            "total_size": size
                        })
                        total_uploaded_bytes += size
                        log_file.write(
                            "Uploaded {}, of size {} bytes complete, I have uploaded {} bytes in total\n".format(file,
                                                                                                                 size,
                                                                                                                 total_uploaded_bytes))
                    # except Exception:
                    #     print("Error with {}".format(file))
                    #     traceback.print_exc()
                    finally:
                        pass
            except KeyboardInterrupt:
                pass
            finally:

                bar.close()
                print("Cleaning up")
                json_map = {"version": VERSION_CODE,
                            "files": json_list}
                json_data = json.dumps(json_map)
                encrypted_json_data = self.c.encrypt(json_data.encode('UTF-8'))
                media_body = MediaIoBaseUpload(
                    BytesIO(
                        encrypted_json_data
                    ),
                    resumable=True, chunksize=256 * 1024,
                    mimetype="application/octet-stream"
                )
                metadata = {
                    "name": self.c.encrypt_name("backup_{}.json".format(VERSION_CODE)),
                    "parents": [folder_id]
                }
                file = self.service.files().create(body=metadata, media_body=media_body, fields="id")
                response = None
                enc_json_data_len = len(encrypted_json_data)
                bar = tqdm(total=enc_json_data_len, dynamic_ncols=True)
                total = 0.0
                while response is None:
                    try:
                        status, response = file.next_chunk()
                        if status:
                            # uploaded+=CHUNK_SIZE
                            # bar.update(uploaded)
                            # bar.
                            progress = status.progress()
                            bar.update((progress - total) * enc_json_data_len)
                            total = progress
                    except Exception as e:
                        bar.write(str(e))
                bar.update((1 - total)*enc_json_data_len)
                bar.close()
                # if verbose:
                #     for file in json_list:
                #         print(file.get("source"))

                print("Uploaded {} bytes.".format(total_uploaded_bytes))
                log_file.write("Uploaded {} bytes / {}".format(total_uploaded_bytes, file_size))

                log_file.close()


    def list_backups(self):

        files = self.service.files().list(spaces="appDataFolder", q=f"'{self.config.parent_id}' in parents").execute()['files']
        return [Backup(self.service, file,config=self.config, c=self.c) for file in files]
