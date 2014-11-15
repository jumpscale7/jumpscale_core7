from JumpScale import j

class Ubuntu:
    def __init__(self):
        self._aptupdated = False
        self._checked = False
        self._cache=None
        self.installedPackageNames=[]

    def initApt(self):
        try:
            import apt
        except ImportError:
            #we dont wont jshell to break, self.check will take of this
            return
        apt.apt_pkg.init()
        if hasattr(apt.apt_pkg, 'Config'):
            cfg = apt.apt_pkg.Config
        else:
            cfg = apt.apt_pkg.Configuration
        try:
            cfg.set("APT::Install-Recommends", "0")
            cfg.set("APT::Install-Suggests", "0")
        except:
            pass
        self._cache = apt.Cache()
        self.aptCache=self._cache
        self.apt=apt

    def check(self, die=True):
        """
        check if ubuntu or mint (which is based on ubuntu)
        """
        if not self._checked:
            try:
                import lsb_release
                info = lsb_release.get_distro_information()['ID']
                if info != 'Ubuntu' and info !='LinuxMint':
                    raise RuntimeError("Only ubuntu or mint supported.")
                self._checked = True
            except ImportError:
                self._checked = False
                if die:
                    raise RuntimeError("Only ubuntu or mint supported.")
        return self._checked

    def getVersion(self):
        """
        returns codename,descr,id,release
        known ids" raring, linuxmint
        """
        self.check()
        import lsb_release
        result=lsb_release.get_distro_information()        
        return result["CODENAME"].lower().strip(),result["DESCRIPTION"],result["ID"].lower().strip(),result["RELEASE"],

    def createUser(self,name,passwd,home=None,creategroup=True):
        import JumpScale.baselib.remote.cuisine
        c=j.remote.cuisine.api

        if home==None:
            homeexists=True
        else:
            homeexists=j.system.fs.exists(home)

        c.user_ensure(name, passwd=passwd, home=home, uid=None, gid=None, shell=None, fullname=None, encrypted_passwd=False)
        if creategroup:
            self.createGroup(name)
            self.addUser2Group(name,name)

        if home<>None and not homeexists:
            c.dir_ensure(home,owner=name,group=name)

    def createGroup(self,name):
        import JumpScale.baselib.remote.cuisine
        c=j.remote.cuisine.api
        c.group_ensure(name)

    def addUser2Group(self,group,user):
        import JumpScale.baselib.remote.cuisine
        c=j.remote.cuisine.api
        c.group_user_ensure(group, user)

            

    def checkInstall(self, packagenames, cmdname):
        """
        @param packagenames is name or array of names of ubuntu package to install e.g. curl
        @param cmdname is cmd to check e.g. curl
        """
        self.check()
        if j.basetype.list.check(packagenames):
            for packagename in packagenames:
                self.checkInstall(packagename,cmdname)
        else:
            packagename=packagenames
            result, out = j.system.process.execute("which %s" % cmdname, False)
            if result != 0:
                self.install(packagename)
            else:
                return
            result, out = j.system.process.execute("which %s" % cmdname, False)
            if result != 0:
                raise RuntimeError("Could not install package %s and check for command %s." % (packagename, cmdname))

    def install(self, packagename):
        
        cmd='unset JSBASE;unset PYTHONPATH;apt-get install %s --force-yes -y'%packagename
        j.system.process.executeWithoutPipe(cmd)

        # self.check()
        # if self._cache==None:
        #     self.initApt()

        # if isinstance(packagename, basestring):
        #     packagename = [packagename]
        # for package in packagename:
        #     pkg = self._cache[package]
        #     if not pkg.is_installed:
        #         print "install %s" % packagename
        #         pkg.mark_install()
        # self._cache.commit()
        # self._cache.clear()

    def installVersion(self, packageName, version):
        '''
        Installs a specific version of an ubuntu package.

        @param packageName: name of the package
        @type packageName: str

        @param version: version of the package
        @type version: str
        '''

        self.check()
        if self._cache==None:
            self.initApt()

        mainPackage = self._cache[packageName]
        versionPackage = mainPackage.versions[version].package

        if not versionPackage.is_installed:
            versionPackage.mark_install()

        self._cache.commit()
        self._cache.clear()

    def installDebFile(self, path):
        self.check()
        if self._cache==None:
            self.initApt()
        import apt.debfile
        deb = apt.debfile.DebPackage(path, cache=self._cache)
        deb.install()

    def remove(self, packagename):
        j.logger.log("ubuntu remove package:%s"%packagename,category="ubuntu.remove")
        self.check()
        if self._cache==None:
            self.initApt()        
        pkg = self._cache[packagename]
        if pkg.is_installed:
            pkg.mark_delete()
        if packagename in self.installedPackageNames:
            self.installedPackageNames.pop(self.installedPackageNames.index(packagename))
        self._cache.commit()
        self._cache.clear()

    def serviceInstall(self,servicename, daemonpath, args='', respawn=True, pwd=None,env=None,reload=True):
        C="""
start on runlevel [2345]
stop on runlevel [016]
"""
        if respawn:
            C += "respawn\n"
        if pwd:
            C += "chdir %s\n" % pwd
        if env<>None:
            for key,value in env.iteritems():
                C+="env %s=%s\n"%(key,value)
        C+="exec %s %s\n"%(daemonpath,args)

        C=j.dirs.replaceTxtDirVars(C)

        j.system.fs.writeFile("/etc/init/%s.conf"%servicename,C)
        if reload:
            j.system.process.execute("initctl reload-configuration")

    def serviceUninstall(self,servicename):
        self.stopService(servicename)
        j.system.fs.remove("/etc/init/%s.conf"%servicename)

    def startService(self, servicename):
        j.logger.log("start service on ubuntu for:%s"%servicename,category="ubuntu.start")  #@todo P1 add log statements for all other methods of this class
        if not self.statusService(servicename):
            cmd="sudo start %s" % servicename
            # print cmd
            return j.system.process.execute(cmd)

    def stopService(self, servicename):
        cmd="sudo stop %s" % servicename
        # print cmd
        return j.system.process.execute(cmd,False)

    def restartService(self, servicename):
        return j.system.process.execute("sudo restart %s" % servicename,False)

    def statusService(self, servicename):
        exitcode, output = j.system.process.execute("sudo status %s" % servicename,False)
        parts = output.split(' ')
        if len(parts) >=2 and parts[1].startswith('start'):
            return True

        return False

    def serviceDisableStartAtBoot(self, servicename):
         j.system.process.execute("update-rc.d -f %s remove" % servicename)

    def serviceEnableStartAtBoot(self, servicename):
         j.system.process.execute("update-rc.d -f %s defaults" % servicename)

    def updatePackageMetadata(self, force=True):
        self.check()
        if self._cache==None:
            self.initApt()        
        self._cache.update()

    def upgradePackages(self, force=True):
        self.check()
        if self._cache==None:
            self.initApt()        
        self.updatePackageMetadata()
        self._cache.upgrade()

    def getPackageNamesRepo(self):        
        return self._cache.keys()

    def getPackageNamesInstalled(self):
        if self.installedPackageNames==[]:            
            result=[]
            for key in self.getPackageNamesRepo():
                p=self._cache[key]
                if p.installed:
                    self.installedPackageNames.append(p.name)
        return self.installedPackageNames

    def getPackage(self,name):
        return self._cache[name]

    def findPackagesRepo(self,packagename):
        packagename=packagename.lower().strip().replace("_","").replace("_","")
        if self._cache==None:
            self.initApt()        
        result=[]
        for item in self.getPackageNamesRepo():
            item2=item.replace("_","").replace("_","").lower()
            if item2.find(packagename)<>-1:
                result.append(item)
        return result

    def findPackagesInstalled(self,packagename):
        packagename=packagename.lower().strip().replace("_","").replace("_","")
        if self._cache==None:
            self.initApt()        
        result=[]
        for item in self.getPackageNamesInstalled():
            item2=item.replace("_","").replace("_","").lower()
            if item2.find(packagename)<>-1:
                result.append(item)
        return result


    def find1packageInstalled(self,packagename):
        j.logger.log("find 1 package in ubuntu",6,category="ubuntu.find")
        res=self.findPackagesInstalled(packagename)
        if len(res)==1:
            return res[0]
        elif len(res)>1:
            raise RuntimeError("Found more than 1 package for %s"%packagename)
        raise RuntimeError("Could not find package %s"%packagename)

    def listSources(self):
        from aptsources import sourceslist
        return sourceslist.SourcesList()

    def changeSourceUri(self, newuri):
        src = self.listSources()
        for entry in src.list:
            entry.uri = newuri
        src.save()
