from JumpScale import j
from NetworkScanner import NetworkScanner
import multiprocessing
import time
import logging


NUM_WORKERS = 4


def _process(dumper, ip, port, queue):
    print('processing %s:%s' % (ip, port))
    try:
        redis = j.clients.redis.getRedisClient(ip, port)
        now = int(time.time())
        dumper.dump(redis)
    except Exception:
        print("Failed to process redis '%s:%s'" % (ip, port))
    finally:
        # workers must have some rest (1 sec) before moving to next
        # ip to process
        if int(time.time()) - now < 1:
            # process took very short time. Give worker time to rest
            time.sleep(1)

        queue.put_nowait((ip, port))

class BaseDumper(object):
    def __init__(self, cidr, ports=[6379]):
        logging.root.setLevel(logging.INFO)

        self._cidr = cidr
        scanner = NetworkScanner(cidr, ports)
        self._candidates = scanner.scan()

    def start(self, workers=NUM_WORKERS):
        manager = multiprocessing.Manager()
        queue = manager.Queue()
        for ip, ports in self.candidates.items():
            for port in ports:
                queue.put_nowait((ip, port))

        pool = multiprocessing.Pool(workers)

        while True:
            ip, port = queue.get()
            pool.apply_async(_process, (self, ip, port, queue))

    @property
    def cidr(self):
        return self._cidr

    @property
    def candidates(self):
        return self._candidates
        
    def dump(self, redis):
        """
        Dump, gets a redis connection. It must process the queues of redis until there is no more items to
        process and then immediately return.

        :param redis: redis connection
        :return:
        """
        """
        :param redis:
        :return:
        """
        raise NotImplementedError
