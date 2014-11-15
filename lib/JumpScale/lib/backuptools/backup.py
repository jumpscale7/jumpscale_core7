import ujson
from JumpScale import j
import lz4
import time
blocksize = 20*1024*1024
objects = []
new_objects = []

def _read_file(path, block_size=0):
    with open(path, 'rb') as f:
        while True:
            piece = f.read(block_size)
            if piece:
                yield piece
            else:
                return

def _dump2stor(store, bucketname, data, compress):
        if len(data)==0:
            return ""       
        key = j.tools.hash.md5_string(data)
        if not key in objects or not key in new_objects:
            if compress:
                data = lz4.compress(data)
            store.set_object(bucketname, key, data)
            new_objects.append(key)
        return key

def store_metadata(store, mdbucketname, backupname, backupmetadata):
    mdbucketname = str(mdbucketname)
    backupname = str(backupname)
    pools = store.list_pools()
    if not mdbucketname in pools:
        store.create_pool(mdbucketname)
    store.set_object(mdbucketname, backupname, ujson.dumps(backupmetadata))

def read_metadata(store, mdbucketname, backupname):
    data = store.get_object(mdbucketname, backupname)
    return ujson.loads(data)

def backup(store, bucketname, f, compress=True):
    global objects
    bucketname = str(bucketname)
    hashes = []
    pools = store.list_pools()
    if not bucketname in pools:
        store.create_pool(bucketname)
    objects = store.list_objects(bucketname)
    for data in _read_file(f, blocksize):
        hashes.append(_dump2stor(store, bucketname, data,compress))
    return {'path':f, 'fileparts':hashes}

def restore(store, bucketname, restorepath, parts, compress=True):
    bucketname = str(bucketname)
    for part in parts:
        part_content = store.get_object(bucketname, part)
        if compress:
            uncompressed_part_content = lz4.decompress(part_content)
        else:
            uncompressed_part_content = part_content
        j.system.fs.writeFile(restorepath, uncompressed_part_content, append=True)




