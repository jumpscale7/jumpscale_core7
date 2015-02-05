from JumpScale import j

from .CodeGeneratorBase import CodeGeneratorBase


class CodeGeneratorActorLocal(CodeGeneratorBase):

    def __init__(self, spec, typecheck=True, dieInGenCode=True):
        CodeGeneratorBase.__init__(self, spec, typecheck, dieInGenCode)

        self.actorpath = j.system.fs.joinPaths(j.core.codegenerator.codepath, spec.appname, spec.actorname)
        j.system.fs.createDir(self.actorpath)
        self.type = "actorlocal"

    def addMethod(self, method):
        spec = self.spec
        s = "def %s(self{paramcodestr}):\n" % method.name
        descr = ""

        if method.description != "":
            if method.description[-1] != "\n":
                method.description += "\n\n"
            descr = method.description

        for var in method.vars:
            descr += "param:%s %s" % (var.name, self.descrTo1Line(var.description))
            if var.defaultvalue != None:
                descr += " default=%s" % var.defaultvalue
            descr += "\n"

        if method.result != None:
            descr += "result %s %s\n" % (method.result.type, self.descrTo1Line(method.result.description))

        if descr != "":
            s += j.code.indent("\"\"\"\n%s\n\"\"\"\n" % descr, 1)

        paramCodeStr = ","
        for param in method.vars:
            if param.defaultvalue != None:
                paramCodeStr += "%s=%r," % (param.name, param.defaultvalue)
            else:
                paramCodeStr += "%s," % param.name
        if len(paramCodeStr) > 0 and paramCodeStr[-1] == ",":
            paramCodeStr = paramCodeStr[:-1]
        if paramCodeStr != "":
            s = s.replace("{paramcodestr}", self.descrTo1Line(paramCodeStr))
        else:
            s = s.replace("{paramcodestr}", "")

        self.content += "\n%s" % j.code.indent(s, 1)

        s = "params=j.core.params.get()\n"

        for var in method.vars:
            s += "params.%s=%s\n" % (var.name, var.name)

        key = "%s_%s_%s" % (spec.appname, spec.actorname, method.name)

        s += """
te=j.core.portal.active.taskletengines["{key}"]
params=te.execute(params)
if params.has_key("result"):
    return params.result
else:
    return params
"""
        #@todo need to complete the code for te.execute(self, params, service=None, job=None, tags=None, groupname='main')
        s = s.replace("{key}", key)

        self.content += j.code.indent(s, 2)
        return

    def addInitExtras(self):
        s = """
## following code will be loaded at runtime
from JumpScale.core.Shell import ipshellDebug,ipshell
print("DEBUG NOW db init")
ipshell()

actorObject.dbfs=self.dbclientFactory.get(self.appName,actorName,self.dbtype)
actorObject.dbmem=self.dbclientFactory.get(self.appName,actorName,"MEMORY")
actorObject.dbredis=self.dbclientFactory.get(self.appName,actorName,"REDIS")
actorObject.name=actorName
actorObject.appname=self.appName
"""
        # self.initprops+=j.code.indent(s,2)

    def generate(self):
        self.addClass()

        self.addInitExtras()

        for method in self.spec.methods:
            self.addMethod(method)

        return self.getContent()
