from Cryptodome import Random
import pickle
from Cryptodome.Cipher import AES
import base64
import sys
import os

  # name of file in which key is stored
KEY_LENGTH = 32  # bytes
BLOCK_SIZE = 16


def pad(data: bytes, bs: int = BLOCK_SIZE) -> bytes:  # function to pad data to block size, which is typically 16 bytes
    """
    Shmoosey's trademarked padding function, the function appends identical bytes to the end, each with the
    value of the length of the padding which is at most 16 (0x10). When the data perfectly fits the block size,
    a decoy padding is added to avoid confusion and to allow all data to be compatible with the algorithm.

    My understanding is that this kind of padding goes by an different name, fork this and fix the comment!
    @param data: Data to pad
    @param bs: block size of encryption algorithm, in the case of AES is 16 bytes
    @return: padded data
    """
    if len(data) % bs == 0:  # if fits in block size
        padding_length = bs
    else:
        padding_length = bs - len(data) % bs
    data += bytes([padding_length]) * padding_length
    return data


def unpad(data: bytes):
    padding_length = data[-1]
    padded = True
    for byte in data[-padding_length:]:
        if byte != padding_length:
            padded = False
    if padded:
        return data[:-padding_length]
    else:
        return data


class Cryptologor:
    def __init__(self, key_file):
        """
        Class to deal with encryption stuff, please fork me and think of a better name.
        @param key_file: Path to key file
        """
        self.rand = Random.new()
        try:
            f = open(key_file, "rb")
            self.key = pickle.load(f)

            f.close()
        except IOError:
            self.key = self.rand.read(KEY_LENGTH)
            with open(key_file, "wb") as f:
                pickle.dump(self.key, f)

    def encrypt(self, data: bytes) -> bytes:
        """
        Shmoosey's revolutionary encryption function, returned bytes include the initialization vector (IV)
        as first 16 bytes. The IV is randomly generated for each cipher and serves as a sort of salt for
        the encryption algorithm. This will be separated automagically in the decryption function.
        @param data: data to encrypt
        @return: encrypted data
        """

        iv = self.rand.read(BLOCK_SIZE)
        aes = AES.new(self.key, AES.MODE_CBC, iv)
        encrypted_data = aes.encrypt(pad(data))
        return iv + encrypted_data

    def decrypt(self, data: bytes) -> bytes:
        """
        Shmoosey's revolutionary decryption function. It does it all. It does the IV separation, it does
        the decryption, it does the unpadding.
        @param data: data to decrypt
        @return: decrypted data
        """
        iv = data[:BLOCK_SIZE]  # separate out IV
        encrypted_data = data[BLOCK_SIZE:]

        aes = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(aes.decrypt(encrypted_data))

    def encrypt_name(self, name: str):
        """
        Shmoosey's revolutionary name encryption function. Simply input a string and it will encrypt it into
        a base64 string, which can be easily decrypted using the below function. Good for, say, the name of
        a google drive file.
        @param name: String to encrypt
        @return: Base 64 encoded cipher
        """

        data = name.encode("UTF-8")
        encrypted_data = self.encrypt(data)
        b64 = base64.urlsafe_b64encode(encrypted_data)
        return b64.decode("UTF-8")

    def decrypt_name(self, encrypted_name: str):
        data = base64.urlsafe_b64decode(encrypted_name)
        return self.decrypt(data).decode("UTF-8")

