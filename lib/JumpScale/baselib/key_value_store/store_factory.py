from JumpScale import j


class KeyValueStoreFactory(object):
    '''
    The key value store factory provides logic to retrieve store instances. It
    also caches the stores based on their type, name and namespace.
    '''

    def __init__(self):
        self._cache = dict()

    # def getMongoDBStore(self, namespace='',serializers=[]):
    #     '''
    #     Gets an MongoDB key value store.

    #     @param namespace: namespace of the store, defaults to None
    #     @type namespace: String

    #     @return: key value store
    #     @rtype: ArakoonKeyValueStore
    #     '''
    #     from mongodb_store import MongoDBKeyValueStore
    #     key = '%s_%s' % ("arakoon", namespace)
    #     if key not in self._cache:
    #         if namespace=="":
    #             namespace="main"
    #         self._cache[key] = MongoDBKeyValueStore(namespace)
    #     return self._cache[key]

    def getArakoonStore(self, namespace='',serializers=[]):
        '''
        Gets an Arakoon key value store.

        @param namespace: namespace of the store, defaults to None
        @type namespace: String

        @param defaultJSModelSerializer: default JSModel serializer
        @type defaultJSModelSerializer: Object

        @return: key value store
        @rtype: ArakoonKeyValueStore
        '''
        from arakoon_store import ArakoonKeyValueStore
        if serializers==[]:
            serializers=[j.db.serializers.getSerializerType('j')]
        key = '%s_%s' % ("arakoon", namespace)
        if key not in self._cache:
            if namespace=="":
                namespace="main"
            self._cache[key] = ArakoonKeyValueStore(namespace,serializers=serializers)
        return self._cache[key]

    def getFileSystemStore(self, namespace='', baseDir=None,serializers=[]):
        '''
        Gets a file system key value store.

        @param namespace: namespace of the store, defaults to an empty string
        @type namespace: String

        @param baseDir: base directory of the store, defaults to j.dirs.db
        @type namespace: String

        @param defaultJSModelSerializer: default JSModel serializer
        @type defaultJSModelSerializer: Object

        @return: key value store
        @rtype: FileSystemKeyValueStore
        '''
        from file_system_store import FileSystemKeyValueStore
        if serializers==[]:
            serializers=[j.db.serializers.getMessagePack()]

        key = '%s_%s' % ("fs", namespace)
        if key not in self._cache:
            if namespace=="":
                namespace="main"
            self._cache[key] = FileSystemKeyValueStore(namespace, baseDir=baseDir,serializers=serializers)
        return self._cache[key]

    def getMemoryStore(self, namespace=None):
        '''
        Gets a memory key value store.

        @return: key value store
        @rtype: MemoryKeyValueStore
        '''
        from memory_store import MemoryKeyValueStore
        return MemoryKeyValueStore(namespace)

    def getRedisStore(self, namespace='',host='localhost',port=9999,db=0,password='',serializers=None,masterdb=None,changelog=True):
        '''
        Gets a memory key value store.

        @param name: name of the store
        @type name: String

        @param namespace: namespace of the store, defaults to None
        @type namespace: String

        @return: key value store
        @rtype: MemoryKeyValueStore
        '''
        from redis_store import RedisKeyValueStore
        key = '%s_%s_%s' % ("redis", port, namespace)
        if key not in self._cache:
            self._cache[key] = RedisKeyValueStore(namespace=namespace,host=host,port=port,db=db,password=password,serializers=serializers,masterdb=masterdb, changelog=changelog)
        return self._cache[key]

    def getLevelDBStore(self, namespace='',basedir=None,serializers=[]):
        '''
        Gets a leveldb key value store.

        @param name: name of the store
        @type name: String

        @param namespace: namespace of the store, defaults to ''
        @type namespace: String

        @return: key value store
        '''
        from leveldb_store import LevelDBKeyValueStore
        key = '%s_%s' % ("leveldb", namespace)
        if key not in self._cache:
            self._cache[key] = LevelDBKeyValueStore(namespace=namespace,basedir=basedir,serializers=serializers)
        return self._cache[key]

