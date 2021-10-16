from Cryptodome.Hash import SHA256
import base64

BUFFER_SIZE = 1000 ** 2

def digest(path: str):
    f = open(path, "rb")
    sha = SHA256.new()
    data = f.read(BUFFER_SIZE)
    while data:
        sha.update(data)
        data = f.read(BUFFER_SIZE)
    return base64.b64encode(sha.digest()).decode("utf-8")
