#!/usr/bin/env python
from JumpScale import j
import sys
import time
try:
    import ujson as json
except:
    import json
import psutil
import JumpScale.baselib.taskletengine
from JumpScale.baselib import cmdutils

# Preload libraries
j.system.platform.psutil=psutil
# import JumpScale.baselib.graphite
import JumpScale.lib.diskmanager
import JumpScale.baselib.stataggregator
import JumpScale.grid.agentcontroller
import JumpScale.grid.osis
import JumpScale.baselib.redis
from JumpScale.baselib.redisworker.RedisWorker import RedisWorkerFactory
import JumpScale.grid.jumpscripts

import os

RUNTIME = 24 * 3600

def restart_program():
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    python = sys.executable
    os.execl(python, python, * sys.argv)


class Worker(object):

    def __init__(self,queuename):
        self.actions={}
        self.clients = dict()
        self.acclient = None
        self.redisw = RedisWorkerFactory()
        self.queuename=queuename
        self.init()
        self.starttime = time.time()

    def getClient(self, job):
        ipaddr = getattr(job, 'achost', None)
        client = self.clients.get(ipaddr)
        if not client:
            if ipaddr:
                client = j.clients.agentcontroller.get(ipaddr, login='node')
                self.clients[ipaddr] = client
            else:
                if self.acclient==None:
                    self.acclient = j.clients.agentcontroller.getByInstance()
                return self.acclient
        return client

    def init(self):
        j.system.fs.createDir(j.system.fs.joinPaths(j.dirs.tmpDir,"jumpscripts"))
        self.redisw.redis.delete("workers:action:%s"%self.queuename)

    def processAction(self, action):
        self.redisw.redis.delete("workers:action:%s"%self.queuename)
        if action == "RESTART":
            print "RESTART ASKED"
            restart_program()
            j.application.stop()

        if action=="RELOAD":
            print "RELOAD ASKED"
            self.actions={}

    def run(self):
        self.log("STARTED")
        while True:
            self.redisw.redis.hset("workers:heartbeat",self.queuename,int(time.time()))
            if self.starttime + RUNTIME < time.time():
                print "Running for %s seconds restarting" % RUNTIME
                restart_program()

            try:
                self.log("check if work")
                jtype, job = self.redisw._getWork(self.queuename,timeout=10)
            except Exception,e:
                if str(e).find("Could not find queue to execute job")<>-1:
                    #create queue
                    self.log("could not find queue")
                else:
                    j.events.opserror("Could not get work from redis, is redis running?","workers.getwork",e)
                time.sleep(10)
                continue
            if jtype == "action":
                self.processAction(job)
                continue
            if job:
                
                j.application.jid=job.guid
                try:
                    if self.actions.has_key(job.jscriptid):
                        jscript=self.actions[job.jscriptid]
                    else:
                        self.log("JSCRIPT CACHEMISS")
                        try:
                            jscript=self.redisw.getJumpscriptFromId(job.jscriptid)
                            if jscript==None:
                                msg="cannot find jumpscript with id:%s"%job.jscriptid
                                self.log("ERROR:%s"%msg)
                                j.events.bug_warning(msg,category="worker.jscript.notfound")
                                job.result=msg
                                job.state="ERROR"
                                self.notifyWorkCompleted(job)
                                continue

                            if jscript.organization<>"" and jscript.name<>"" and jscript.id<1000000:
                                #this is to make sure when there is a new version of script since we launched this original script we take the newest one
                                jscript=self.redisw.getJumpscriptFromName(jscript.organization,jscript.name)
                                job.jscriptid=jscript.id
                                #result is method action

                            jscript.write()
                            jscript.load()

                            self.actions[job.jscriptid]=jscript

                        except Exception,e:                
                            agentid=j.application.getAgentId()
                            if jscript<>None:
                                msg="could not compile jscript:%s %s_%s on agent:%s.\nError:%s"%(jscript.id,jscript.organization,jscript.name,agentid,e)
                            else:
                                msg="could not compile jscriptid:%s on agent:%s.\nError:%s"%(job.jscriptid,agentid,e)
                            eco=j.errorconditionhandler.parsePythonErrorObject(e)
                            eco.errormessage = msg
                            eco.code=jscript.source
                            eco.jid = job.guid
                            eco.category = 'workers.compilescript'
                            eco.process()
                            job.state="ERROR"
                            eco.tb = None
                            job.result=eco.__dict__
                            # j.events.bug_warning(msg,category="worker.jscript.notcompile")
                            # self.loghandler.logECO(eco)
                            self.notifyWorkCompleted(job)
                            continue

                        self.actions[job.jscriptid]=jscript

                    self.log("Job started:%s script:%s %s/%s"%(job.id, jscript.id,jscript.organization,jscript.name))

                    j.logger.enabled = job.log

                    status, result=jscript.executeInWorker(**job.args)
                    self.redisw.redis.hdel("workers:inqueuetest",jscript.getKey())
                    j.logger.enabled = True
                    if status:
                        job.result=result
                        job.state="OK"
                        job.resultcode=0
                    else:
                        eco = result
                        agentid=j.application.getAgentId()
                        msg="Could not execute jscript:%s %s_%s on agent:%s\nError: %s"%(jscript.id,jscript.organization,jscript.name,agentid, eco.errormessage)
                        eco.errormessage = msg
                        eco.jid = job.guid
                        eco.code=jscript.source
                        eco.category = "workers.executejob"

                        out=""
                        tocheck=["\"worker.py\"","jscript.executeInWorker","return self.module.action","JumpscriptFactory.py"]
                        for line in eco.backtrace.split("\n"):
                            found=False
                            for check in tocheck:
                                if line.find(check)<>-1:
                                    found=True
                                    break
                            if found==False:
                                out+="%s\n"%line

                        eco.backtrace=out

                        if job.id<1000000 and job.errorreport==True:
                            eco.process()
                        else:
                            self.log(eco)
                        # j.events.bug_warning(msg,category="worker.jscript.notexecute")
                        # self.loghandler.logECO(eco)
                        job.state="ERROR"
                        eco.tb = None
                        job.result=eco.__dict__
                        job.resultcode=1

                    #ok or not ok, need to remove from queue test
                    #thisin queue test is done to now execute script multiple time
                    self.notifyWorkCompleted(job)
                finally:
                    j.application.jid = 0


    def notifyWorkCompleted(self,job):
        job.timeStop=int(time.time())

        # if job.state[0:2]<>"OK":
        #     self.log("result:%s"%job.result)


        if job.jscriptid>1000000:
            #means is internal job
            # q=j.clients.redis.getGeventRedisQueue("127.0.0.1",9999,"workers:return:%s"%jobid)
            self.redisw.redis.hset("workers:jobs",job.id, json.dumps(job.__dict__))
            self.redisw.redis.rpush("workers:return:%s"%job.id,time.time())            
        else:
            try:
                acclient = self.getClient(job)
            except Exception,e:
                j.events.opserror("could not report job in error to agentcontroller", category='workers.errorreporting', e=e)
                return
            #jumpscripts coming from AC
            if job.state<>"OK":
                try:
                    acclient.notifyWorkCompleted(job.__dict__)
                except Exception,e:
                    j.events.opserror("could not report job in error to agentcontroller", category='workers.errorreporting', e=e)
                    return
                #lets keep the errors
                # self.redis.hdel("workers:jobs",job.id)
            else:
                if job.log or job.wait:
                    try:
                        acclient.notifyWorkCompleted(job.__dict__)
                    except Exception,e:
                        j.events.opserror("could not report job result to agentcontroller", category='workers.jobreporting', e=e)
                        return
                    # job.state=="OKR" #means ok reported
                    #we don't have to keep status of local job result, has been forwarded to AC
                self.redisw.redis.hdel("workers:jobs",job.id)


    def log(self, message, category='',level=5):
        #queue saving logs        
        # j.logger.log(message,category=category,level=level)
        print "worker:%s:%s" % (self.queuename, message)

if __name__ == '__main__':
    parser = cmdutils.ArgumentParser()
    parser.add_argument("-qn", '--queuename', help='Queue name', required=True)
    parser.add_argument("-i", '--instance', help='JSAgent instance', required=True)

    opts = parser.parse_args()

    jp = j.packages.findNewest('jumpscale', 'jsagent')
    jp.load(opts.instance)
    j.application.instanceconfig = jp.hrd_instance

    j.core.osis.client = j.core.osis.getClientByInstance(die=False)

    j.application.start("jumpscale:worker:%s" % opts.queuename)

    if j.application.config.exists("grid.id"):
        j.application.initGrid()

    j.logger.consoleloglevel = 2
    j.logger.maxlevel=7

    worker=Worker(opts.queuename)
    worker.run()


