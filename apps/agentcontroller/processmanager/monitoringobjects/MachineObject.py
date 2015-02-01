from JumpScale import j

from _MonObjectBaseFactory import *

class MachineObjectFactory(MonObjectBaseFactory):
    def __init__(self,host,classs):
        MonObjectBaseFactory.__init__(self,host,classs)
        self.osis=j.clients.osis.getCategory(self.host.daemon.osis,"system","machine")
        self.osisobjects={} #@todo P1 load them from ES at start (otherwise delete will not work), make sure they are proper osis objects


class MachineObject(MonObjectBase):
    pass
