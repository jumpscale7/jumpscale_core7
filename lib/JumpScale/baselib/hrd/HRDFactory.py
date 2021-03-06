from JumpScale import j
# import JumpScale.baselib.codeexecutor
from .HRD import HRD
from .HRDTree import HRDTree
from collections import OrderedDict

class HRDFactory:
    def __init__(self):
        self.logenable=False
        self.loglevel=5

    def log(self,msg,category="",level=5):
        if "logger" not in j.__dict__:
            print(msg)
        elif level<self.loglevel+1 and self.logenable:
            j.logger.log(msg,category="hrd.%s"%category,level=level)

    def get(self,path=None,content="",prefixWithName=True,keepformat=False,args=OrderedDict(),templates=[]):
        """
        @param path
        """        
        if templates=="":
            templates=[]
        if path is not None and j.system.fs.isDir(path):
            if content!="":
                j.events.inputerror_critical("HRD of directory cannot be build with as input content (should be empty)")
            return HRDTree(path,prefixWithName=prefixWithName,keepformat=keepformat)
        else:
            return HRD(path=path,content=content,prefixWithName=prefixWithName,keepformat=keepformat,args=args,templates=templates)


    def getHRDFromOsisObject(self,osisobj,prefixRootObjectType=True):
        txt=j.db.serializers.hrd.dumps(osisobj.obj2dict())
        prefix=osisobj._P__meta[2]
        out=""
        for line in txt.split("\n"):
            if line.strip()=="":
                continue
            if line[0]=="_":
                continue
            if line.find("_meta.")!=-1:
                continue
            if prefixRootObjectType:
                out+="%s.%s\n"%(prefix,line)
            else:
                out+="%s\n"%(line)
        return self.getHRDFromContent(out)   


    def getHRDFromDict(self,ddict={}):
        hrd=self.get(content=" ",prefixWithName=False)
        for key,val in ddict.iteritems():
            hrd.set(key,val)  
        return hrd
