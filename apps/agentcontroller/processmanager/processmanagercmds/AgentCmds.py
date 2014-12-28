from JumpScale import j
import JumpScale.grid.agentcontroller
import JumpScale.baselib.redisworker
import gevent
from JumpScale.grid.serverbase import returnCodes
import time

REDISIP = '127.0.0.1'
REDISPORT = 9999


class AgentCmds():
    ORDER = 20

    def __init__(self,daemon=None):
        self._name="agent"

        if daemon==None:
            return
        self.daemon=daemon
        self._adminAuth=daemon._adminAuth

        self.redis = j.clients.redis.getGeventRedisClient(REDISIP, REDISPORT)
        self.queue={}
        self.queue["io"] = j.clients.redis.getGeventRedisQueue("127.0.0.1",9999,"workers:work:io")
        self.queue["hypervisor"] = j.clients.redis.getGeventRedisQueue("127.0.0.1",9999,"workers:work:hypervisor")
        self.queue["default"] = j.clients.redis.getGeventRedisQueue("127.0.0.1",9999,"workers:work:default")
        self.queue["monitoring"] = j.clients.redis.getGeventRedisQueue("127.0.0.1",9999,"workers:work:monitoring")

    def _init(self):
        self.init()

    def log(self, msg):
        print "processmanager:%s" % msg

    def init(self, session=None):
        if session<>None:
            self._adminAuth(session.user,session.passwd)

        self._killGreenLets()
        acinstance = j.application.instanceconfig.get('agentcontroller.connection')
        config = j.clients.agentcontroller.getInstanceConfig(acinstance)
        ipaddr = config.pop('addr')
        for acip in ipaddr.split(','):
            j.core.processmanager.daemon.schedule("agent", self.loop, acip, config)

    def reconnect(self, acip, config):
        while True:
            try:
                client = j.clients.agentcontroller.get(acip, **config)
                client.register()
                return client
            except Exception:
                self.log("Failed to connect to agentcontroller %s" % acip)
                gevent.sleep(5)

    def loop(self, acip, config):
        """
        fetch work from agentcontroller & put on redis queue
        """
        client = self.reconnect(acip, config)
        gevent.sleep(2)
        self.log("start loop to fetch work")
        while True:
            try:
                try:
                    self.log("check if work")
                    job=client.getWork()
                    if job<>None:
                        self.log("WORK FOUND: jobid:%s"%job["id"])
                    else:
                        continue
                except Exception,e:
                    j.errorconditionhandler.processPythonExceptionObject(e)
                    client = self.reconnect(acip, config)
                    continue

                job['achost'] = client.ipaddr
                job['nid'] = j.application.whoAmI.nid
                if job["queue"]=="internal":
                    #cmd needs to be executed internally (is for proxy functionality)
                   
                    if self.daemon.cmdsInterfaces.has_key(job["category"]):
                        job["resultcode"],returnformat,job["result"]=self.daemon.processRPC(job["cmd"], data=job["args"], returnformat="m", session=None, category=job["category"])
                        if job["resultcode"]==returnCodes.OK:
                            job["state"]="OK"
                        else:
                            job["state"]="ERROR"
                    else:
                        job["resultcode"]=returnCodes.METHOD_NOT_FOUND
                        job["state"]="ERROR"
                        job["result"]="Could not find cmd category:%s"%job["category"]
                    client.notifyWorkCompleted(job)
                    continue

                if job["jscriptid"]==None:
                    raise RuntimeError("jscript id needs to be filled in")

                jscriptkey = "%(category)s_%(cmd)s" % job
                if jscriptkey not in  j.core.processmanager.cmds.jumpscripts.jumpscripts:
                    msg = "could not find jumpscript %s on processmanager"%jscriptkey
                    job['state'] = 'ERROR'
                    job['result'] = msg
                    client.notifyWorkCompleted(job)
                    j.events.bug_critical(msg, "jumpscript.notfound")

                jscript = j.core.processmanager.cmds.jumpscripts.jumpscripts[jscriptkey]
                if (jscript.async or job['queue']) and jscript.debug == False:
                    j.clients.redisworker.execJobAsync(job)
                else:
                    def run():
                        timeout = gevent.Timeout(job['timeout'])
                        timeout.start()
                        try:
                            status, result = jscript.execute(**job['args'])
                            job['state'] = 'OK' if status else 'ERROR'
                            job['result'] = result
                            client.notifyWorkCompleted(job)
                        finally:
                            timeout.cancel()
                    gevent.spawn(run)
            except Exception, e:
                j.errorconditionhandler.processPythonExceptionObject(e)


    def _killGreenLets(self,session=None):
        """
        make sure all running greenlets stop
        """
        if session<>None:
            self._adminAuth(session.user,session.passwd)
        todelete=[]

        for key,greenlet in j.core.processmanager.daemon.greenlets.iteritems():
            if key.find("agent")==0:
                greenlet.kill()
                todelete.append(key)
        for key in todelete:
            j.core.processmanager.daemon.greenlets.pop(key)

    def checkRedisStatus(self, session=None):
        notrunning = list()
        for redisinstance in ['redisac', 'redisp', 'redisc']:
            if not j.clients.redis.getProcessPids(redisinstance):
                notrunning.append(redisinstance)
        if not notrunning:
            return True
        return notrunning

    def checkRedisSize(self, session=None):
        redisinfo = j.clients.redisworker.redis.info().split('\r\n')
        info = dict()
        for entry in redisinfo:
            if ':' in entry:
                key, value = entry.split(':')
                info[key] = value
        size = info['used_memory']
        maxsize = 50 * 1024 * 1024
        if j.basetype.float.fromString(size) < maxsize:
            return True
        return False




