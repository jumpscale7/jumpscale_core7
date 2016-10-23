from JumpScale import j
import Dumper
import collections
import json


Stats = collections.namedtuple("Stats", "node key epoch stat avg max")


class InfluxDumper(Dumper.BaseDumper):
    QUEUE_MIN = 'queues:stats:min'
    QUEUE_HOUR = 'queues:stats:hour'
    QUEUES = [QUEUE_MIN, QUEUE_HOUR]

    def __init__(self, influx, database=None, cidr='127.0.0.1', ports=[9999]):
        """
        Create a new instance of influx dumper

        On start. the dump method will get called with the found redis connections object. the `dump`
        method should process the given instance queues until there is no more data to process and then return
        This will make the worker move to the next available connection

        :param influx: Influx connection
        :param database: Influx database name
        :param cidr: Network CIDR to scan for all redis instances that listen on the specified port
        :param port: Find all redis instances that listens on that port on the given CIDR
        """
        super(InfluxDumper, self).__init__(cidr, ports)

        self.influxdb = influx

        if database is None:
            database = 'statistics'

        self.database = database

        for db in self.influxdb.get_list_database():
            if db['name'] == database:
                break
        else:
            self.influxdb.create_database(database)

    def _parse_line(self, line):
        """
        Line is formated as:
        node|key|epoch|stat|avg|max|total
        :param line: Line to parse
        :return: Stats object
        """

        parts = line.split('|')
        if len(parts) != 7:
            raise Exception('Invalid stats line "%s"' % line)
        return Stats(parts[0], parts[1], int(parts[2]), float(parts[3]), float(parts[4]), float(parts[5]), float(parts[6]))

    def _mk_point(self, key, epoch, value, max, tags):
        return {
            "measurement": key,
            "tags": tags,
            "time": epoch,
            "fields": {
                "value": value,
                "max": max,
            }
        }

    def _dump_hour(self, stats):
        print(stats)

    def dump(self, redis):
        """
        Process redis connection until the queue is empty, then return None
        :param redis:
        :return:
        """
        while True:
            data = redis.blpop(self.QUEUES, 1)
            if data is None:
                return

            queue, line = data
            queue = queue.decode()
            line = line.decode()

            stats = self._parse_line(line)
            info = redis.get("stats:%s:%s" % (stats.node, stats.key))

            if stats.key.find('@') != -1:
                stats.key = stats.key.split('@')[0]

            if info is not None:
                info = json.loads(info)
            else:
                info = dict()

            info['tags'] = j.core.tags.getObject(info.get('tags', []))
            info['tags'].tags['node'] = stats.node
            points = []

            tags = info['tags'].tags
            if queue == self.QUEUE_MIN:
                points.append(self._mk_point("%s|m" % (stats.key,), stats.epoch, stats.avg, stats.max, tags))
                points.append(self._mk_point("%s|t" % (stats.key,), stats.epoch, stats.total, stats.max, tags))
            else:
                points.append(self._mk_point("%s|h" % (stats.key,), stats.epoch, stats.avg, stats.max, tags))

            self.influxdb.write_points(points, database=self.database, time_precision='s')
