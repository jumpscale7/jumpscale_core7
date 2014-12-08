from JumpScale import j
import imp
import copy

import JumpScale.baselib.remote.cuisine

# import JumpScale.lib.docker
try:
    import JumpScale.lib.docker
except:
    pass

class JPackage():

    def __init__(self,domain="",name=""):
        self.name=name
        self.domain=domain
        self.hrd=None
        self.metapath=""
        self._loaded=False

        self.hrdpath=""
        self.hrdpath_main=""



    def _load(self):
        if self._loaded==False:

            # self.hrdpath="%s/apps/%s__%s"%(j.dirs.hrdDir,self.jp.domain,self.jp.name)
            self.hrdpath="%s/apps/jpackage.%s.%s.hrd"%(j.dirs.hrdDir,self.domain,self.name)
            self.metapath="%s/%s"%(j.packages.domains[self.domain],self.name)
            self.hrdpath_main="%s/jp.hrd"%self.metapath

            #this is hrd for jpackage (for all instances)
            src="%s/app.hrd"%self.metapath
            if j.system.fs.exists(path=src):
                j.do.copyFile(src,self.hrdpath)

            dest="%s/actions.py"%self.metapath
            if not j.system.fs.exists(path=dest):
                templ="/opt/code/github/jumpscale/jumpscale_core7/lib/JumpScale/baselib/jpackages/templates/action.py"
                j.do.copyFile(templ,dest)
            args={}
            args["jp.name"]=self.name
            args["jp.domain"]=self.domain

            if j.system.fs.exists(path=self.hrdpath):
                j.application.config.applyOnFile(self.hrdpath,additionalArgs=args)            
                self.hrd=j.core.hrd.get(self.hrdpath_main)            

        self._loaded=True

    def getInstance(self,instance="main"):
        self._load()
        # if self.hrd.getInt("instances.maxnr",default=1)==1:
        #     instance="main"
        return JPackageInstance(self,instance)        

    def __repr__(self):
        return "%-15s:%s"%(self.domain,self.name)

    def __str__(self):
        return self.__repr__()

class JPackageInstance():

    def __init__(self,jp,instance):
        self.instance=instance
        self.jp=jp
        self.hrd=None
        self.metapath=""
        self.hrdpath=""
        self.actions=None
        self._loaded=False
        self._reposDone={}        

    def getLogPath(self):        
        logpath=j.system.fs.joinPaths(j.dirs.logDir,"startup", "%s_%s_%s.log" % (self.jp.domain, self.jp.name,self.instance))        
        return logpath

    def getTCPPorts(self):
        ports=[]
        for process in self.getProcessDicts():
            for item in process["ports"]:
                if item not in ports:
                    ports.append(item)
        return ports        

    def _load(self,args={}):
        if self._loaded==False:
            self.hrdpath="%s/apps/jpackage.%s.%s.%s.hrd"%(j.dirs.hrdDir,self.jp.domain,self.jp.name,self.instance)
            self.actionspath="%s/jpackage_actions/%s__%s__%s.py"%(j.dirs.baseDir,self.jp.domain,self.jp.name,self.instance)

            source="%s/instance.hrd"%self.jp.metapath
            if args!={} or (not j.system.fs.exists(path=self.hrdpath) and j.system.fs.exists(path=source)):
                j.do.copyFile(source,self.hrdpath)
            else:
                if not j.system.fs.exists(path=source):
                    j.do.writeFile(self.hrdpath,"")                

            source="%s/actions.py"%self.jp.metapath
            j.do.copyFile(source,self.actionspath)
            
            args["jp.name"]=self.jp.name
            args["jp.domain"]=self.jp.domain
            args["jp.instance"]=self.instance


            # orghrd=j.core.hrd.get(self.jp.hrdpath_main)
            self.hrd=j.core.hrd.get(self.hrdpath,args=args)

            self.hrd.applyTemplate(self.jp.hrdpath_main)

            self.hrd.set("jp.name",self.jp.name)
            self.hrd.set("jp.domain",self.jp.domain)
            self.hrd.set("jp.instance",self.instance)

            self.hrd.save()

            self.hrd=j.core.hrd.get(self.hrdpath)

            j.application.config.applyOnFile(self.hrdpath, additionalArgs=args)

            self.hrd=j.core.hrd.get(self.hrdpath)

            hrd=j.packages.getHRD(reload=True)

            hrd.applyOnFile(self.actionspath, additionalArgs=args)
            self.hrd.applyOnFile(self.actionspath, additionalArgs=args)
            j.application.config.applyOnFile(self.actionspath, additionalArgs=args)

            modulename="%s.%s.%s"%(self.jp.domain,self.jp.name,self.instance)
            mod = imp.load_source(modulename, self.actionspath)
            self.actions=mod.Actions()
            self.actions.jp_instance=self
            self._loaded=True

    def _getRepo(self,url):
        if url in self._reposDone:
            return self._reposDone[url]
        if j.application.config.get("whoami.git.login")!="":
            dest=j.do.pullGitRepo(url=url, login=j.application.config.get("whoami.git.login"), \
                passwd=j.application.config.get("whoami.git.passwd"), depth=1, branch='master')
        else:
            dest=j.do.pullGitRepo(url=url, login=None, passwd=None, depth=1, branch='master')  
        self._reposDone[url]=dest
        return dest      


    def getDependencies(self):
        res=[]
        for item in self.hrd.getListFromPrefix("dependencies"): 

            if isinstance(item,str):
                if item.strip()=="":
                    continue
                item2=item.strip()
                args={}
                item={}
                item["name"]=item2
                item["domain"]="jumpscale"

            if "args" in item:
                args=item["args"]
                if self.hrd.exists(args):
                    args=self.hrd.getDict(args)

                    #dirty hack for now (hrd format has bug)
                    args2={}
                    for key,val in args.items():
                        args2[key]=val.replace("\\n","").replace("\n","")
                    args=args2
            else:
                args={}

            item['args']=args

            if "name" in item:
                name=item["name"]

            domain=""
            if "domain" in item:
                domain=item["domain"].strip()
            if domain=="":
                domain="jumpscale"

            instance="main"
            if "instance" in item:
                instance=item["instance"].strip()
            if instance=="":
                instance="main"

            jp=j.packages.get(name=name,domain=domain)            
            jp=jp.getInstance(instance)

            jp.args=args

            res.append(jp) 

        return res

    def stop(self,args={}):
        self._load(args=args)
        self.actions.stop(**args)
        if not self.actions.check_down_local(**args):
            self.actions.halt(**args)

    def start(self,args={}):
        self._load(args=args)
        self.actions.start(**args)

    def restart(self,args={}):
        self.stop(args)
        self.start(args)

    def getProcessDicts(self):
        res=[]
        counter=0

        for process in self.hrd.getListFromPrefix("process"):
            if not isinstance(process, dict):
                continue
            counter+=1

                
            process=copy.copy(process)
            for item in ["args","cmd","cwd","env","filterstr","name","ports","prio","timeout_start","startupmanager","timeout_stop","user"]:
                if item not in process:
                    process[item]=""

            if isinstance(process["ports"],str) and process["ports"].strip()=="":
                process["ports"]=[]
            elif isinstance(process["ports"],str):
                process["ports"]=[int(item) for item in process["ports"].split(";") if item.strip()!=""]

            if process["name"].strip()=="":
                process["name"]="%s_%s"%(self.hrd.get("jp.name"),self.hrd.get("jp.instance"))

            if process["startupmanager"].strip()=="":
                process["startupmanager"]="tmux"

            if self.hrd.exists("env.process.%s"%counter):
                process["env"]=self.hrd.getDict("env.process.%s"%counter)
            elif process["env"].strip()=="":
                process["env"]={}
            else:
                process["env"]==j.tools.text.getDict(process["env"])                

            for item in ["prio","timeout_start","timeout_stop"]:
                process[item]=j.tools.text.getInt(process[item])

            res.append(process)

        return res

    def install(self,args={},start=True):
        
        self._load(args=args)
        
        docker=self.hrd.exists("docker.enable") and self.hrd.getBool("docker.enable")

        if j.packages.indocker or not docker:

            self.stop()

            for dep in self.getDependencies():
                if dep.jp.name not in j.packages._justinstalled:
                    if 'args' in dep.__dict__:
                        dep.install(args=dep.args)
                    else:
                        dep.install()
                    j.packages._justinstalled.append(dep.jp.name)

            
            for src in self.hrd.getListFromPrefix("ubuntu.apt.source"):
                src=src.replace(";",":")
                if src.strip()!="":     
                    j.system.platform.ubuntu.addSourceUri(src)                

            for src in self.hrd.getListFromPrefix("ubuntu.apt.key.pub"):
                src=src.replace(";",":")
                if src.strip()!="":            
                    cmd="wget -O - %s | apt-key add -"%src
                    j.do.execute(cmd,dieOnNonZeroExitCode=False)

            if self.hrd.getBool("ubuntu.apt.update",default=False):
                print "apt update"
                j.do.execute("apt-get update -y",dieOnNonZeroExitCode=False)

            if self.hrd.getBool("ubuntu.apt.upgrade -y",default=False):
                j.do.execute("apt-get upgrade -y",dieOnNonZeroExitCode=False)

            if self.hrd.exists("ubuntu.packages"):
                for jp in self.hrd.getList("ubuntu.packages"):
                    if jp.strip()!="":
                        j.do.execute("apt-get install %s -f"%jp,dieOnNonZeroExitCode=False)       

            self.actions.prepare()
            #download

            for recipeitem in self.hrd.getListFromPrefix("git.export"):
                print recipeitem
                
                #pull the required repo
                dest0=self._getRepo(recipeitem['url'])
                src="%s/%s"%(dest0,recipeitem['source'])
                src=src.replace("//","/")
                if "dest" not in recipeitem:
                    raise RuntimeError("could not find dest in hrditem for %s %s"%(recipeitem,self))
                dest=recipeitem['dest']          

                if "link" in recipeitem and str(recipeitem["link"]).lower()=='true':
                    #means we need to only list files & one by one link them
                    link=True
                else:
                    link=False

                if src[-1]=="*":
                    src=src.replace("*","")
                    if "nodirs" in recipeitem and str(recipeitem["nodirs"]).lower()=='true':
                        #means we need to only list files & one by one link them
                        nodirs=True
                    else:
                        nodirs=False

                    items=j.do.listFilesInDir( path=src, recursive=False, followSymlinks=False, listSymlinks=False)
                    if nodirs==False:
                        items+=j.do.listDirsInDir(path=src, recursive=False, dirNameOnly=False, findDirectorySymlinks=False)

                    items=[(item,"%s/%s"%(dest,j.do.getBaseName(item)),link) for item in items]
                else:
                    items=[(src,dest,link)]

                for src,dest,link in items:
                    if link:
                        j.system.fs.createDir(j.do.getParent(dest))
                        j.do.symlink(src, dest)
                    else:
                        if j.system.fs.exists(path=dest):
                            if "overwrite" in recipeitem:
                                if recipeitem["overwrite"].lower()=="false":
                                    continue
                                else:
                                    print ("copy: %s->%s"%(src,dest))
                                    j.do.delete(dest)
                                    j.system.fs.createDir(dest)
                                    j.do.copyTree(src,dest)
                        else:
                            print ("copy: %s->%s"%(src,dest))
                            j.do.copyTree(src,dest)

            self.actions.configure()

            if start:
                self.actions.start()

        else:
            #now bootstrap docker
            ports=""
            tcpports=self.hrd.getDict("docker.ports.tcp")
            for inn,outt in tcpports.items():
                ports+="%s:%s "%(inn,outt)
            ports=ports.strip()

            volsdict=self.hrd.getDict("docker.vols")
            vols=""
            for inn,outt in volsdict.items():
                vols+="%s:%s # "%(inn,outt)
            vols=vols.strip().strip("#").strip()

            if self.instance!="main":
                name="%s_%s"%(self.jp.name,self.instance)
            else:
                name="%s"%(self.jp.name)

            image=self.hrd.get("docker.base",default="despiegk/mc")

            mem=self.hrd.get("docker.mem",default="0")
            if mem.strip()=="":
                mem=0

            cpu=self.hrd.get("docker.cpu",default=None)
            if cpu.strip()=="":
                cpu=None

            ssh=self.hrd.get("docker.ssh",default=True)
            if ssh.strip()=="":
                ssh=True

            ns=self.hrd.get("docker.ns",default='8.8.8.8')
            if ns.strip()=="":
                ns='8.8.8.8'

            port=   j.tools.docker.create(name=name, ports=ports, vols=vols, volsro='', stdout=True, base=image, nameserver=ns, \
                replace=True, cpu=cpu, mem=0,jumpscale=True,ssh=ssh)

            self.hrd.set("docker.ssh.port",port)
            self.hrd.set("docker.name",name)
            self.hrd.save()

            hrdname="jpackage.%s.%s.%s.hrd"%(self.jp.domain,self.jp.name,self.instance)
            src="/%s/hrd/apps/%s"%(j.dirs.baseDir,hrdname)
            j.tools.docker.copy(name,src,src)
            j.tools.docker.run(name,"jpackage install -n %s -d %s"%(self.jp.name,self.jp.domain))



    def __repr__(self):
        return "%-15s:%-15s:%s"%(self.jp.domain,self.jp.name,self.instance)

    def __str__(self):
        return self.__repr__()
