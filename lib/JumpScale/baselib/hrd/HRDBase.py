from JumpScale import j

class HRDBase():

    def prefix(self, key,depth=0):
        """
        @param depth means prefix level to return
        """
        result=[]
        for knownkey in self.items.keys():
            # print "prefix: %s - %s"%(knownkey,key)
            if knownkey.startswith(key):
                if depth>0:                    
                    knownkey=".".join(knownkey.split(".")[0:depth])
                if knownkey not in result:                    
                    result.append(knownkey)
        result.sort()
        return result

    def prefixexists(self,key):
        result=[]
        for knownkey in self.items.keys():
            # print "prefix: %s - %s"%(knownkey,key)
            if knownkey.startswith(key):
                return True


    def getBool(self,key,default=None):
        res=self.get(key,default=default)
        if res==None:
            return False
        res2=str(res)
        if res==True or res2=="1" or res2.lower()=="true":
            return True
        else:
            return False            

    def getInt(self,key,default=None):
        if default<>None:
            default=int(default)        
        res=self.get(key,default=default)
        return j.tools.text.getInt(res)

    def getStr(self,key,default=None):
        if default<>None:
            default=str(default)        
        res=self.get(key,default=default)
        res=j.tools.text.pythonObjToStr(res,multiline=False)
        res=res.strip()
        return res

    def listAdd(self,key,item):
        arg=self.get(key)
        if item not in arg:
            arg.append(item)
        self.set(key,arg)

    def getFloat(self,key):
        res=self.get(key)
        return j.tools.text.getFloat(res)

    def exists(self,key):
        key=key.lower()
        return self.items.has_key(key)

    def getList(self,key):
        lst=self.get(key)
        if j.basetype.list.check(lst):
            return lst
        lst=str(lst)
        if j.basetype.string.check(lst):
            return [item.strip() for item in lst.split(",")]        
        raise RuntimeError("no list for %s"%key)

    def getDict(self,key):
        lst=self.get(key)
        if j.basetype.dictionary.check(lst):
            return lst
        if lst.strip()=="":
            return {}        
        raise RuntimeError("no dict for %s"%key)

    def getListFromPrefix(self, prefix):
        """
        returns values from prefix return as list
        """
        result=[]
        for key in self.prefix(prefix):
            result.append(self.get(key))
        return result
  
    def getDictFromPrefix(self, prefix):
        """
        returns values from prefix return as list
        """
        result={}
        l=len(prefix)
        for key in self.prefix(prefix):
            key2=key[l+1:]
            result[key2]=self.get(key)
        return result

    def checkValidity(self,template,hrddata={}):
        """
        @param template is example hrd content block, which will be used to check against, 
        if params not found will be added to existing hrd 
        """      
        from HRD import HRD
        hrdtemplate=HRD(content=template)
        for key in hrdtemplate.items.keys():
            if not self.items.has_key(key):
                hrdtemplateitem=hrdtemplate.items[key]
                if hrddata.has_key(key):
                    data=hrddata[key]
                else:
                    data=hrdtemplateitem.data
                self.set(hrdtemplateitem.name,data,comments=hrdtemplateitem.comments)

    def processall(self):
        for key,hrditem in self.items.iteritems():
            hrditem._process()

    def pop(self,key):
        if self.has_key(key):
            self.items.pop(key)

    def applyOnDir(self,path,filter=None, minmtime=None, maxmtime=None, depth=None,changeFileName=True,changeContent=True,additionalArgs={}):
        """
        look for $(name) and replace with hrd value
        """
        j.core.hrd.log("hrd %s apply on dir:%s"%(self.name,path),category="apply")
        
        items=j.system.fs.listFilesInDir( path, recursive=True, filter=filter, minmtime=minmtime, maxmtime=maxmtime, depth=depth)
        for item in items:
            if changeFileName:
                item2=self._replaceVarsInText(item,additionalArgs=additionalArgs)
                if item2<>item:
                     j.system.fs.renameFile(item,item2)
                    
            if changeContent:
                self.applyOnFile(item2,additionalArgs=additionalArgs)

    def applyOnFile(self,path,additionalArgs={}):
        """
        look for $(name) and replace with hrd value
        """

        j.core.hrd.log("hrd:%s apply on file:%s"%(self.path,path),category="apply")
        content=j.system.fs.fileGetContents(path)
        content=self._replaceVarsInText(content,additionalArgs=additionalArgs)
        j.system.fs.writeFile(path,content)

    def applyOnContent(self,content,additionalArgs={}):
        """
        look for $(name) and replace with hrd value
        """

        content=self._replaceVarsInText(content,self,position,additionalArgs=additionalArgs)
        return content

    def _replaceVarsInText(self,content,additionalArgs={}):
        if content=="":
            return content
            
        items=j.codetools.regex.findAll(r"\$\([\w.]*\)",content)
        j.core.hrd.log("replace vars in hrd:%s"%self.path,"replacevar",7)
        if len(items)>0:
            for item in items:
                # print "look for : %s"%item
                item2=item.strip(" ").strip("$").strip(" ").strip("(").strip(")")

                if additionalArgs.has_key(item2.lower()):
                    newcontent=additionalArgs[item2.lower()]
                    content=content.replace(item,newcontent)
                else:
                    if self.exists(item2):
                        replacewith=j.tools.text.pythonObjToStr(self.get(item2),multiline=True)
                        content=content.replace(item,replacewith)            
        return content          

    def __repr__(self):
        
        parts=[]
        keys=self.items.keys()
        keys.sort()
        if self.commentblock<>"":
            out=[self.commentblock]
        else:
            out=[""]
        keylast=[]
        for key in keys:
            keynew=key.split(".")
            
            #see how many newlines in between
            if keylast<>[] and keynew[0]<>keylast[0]:
                out.append("")
            else:
                if len(keynew)>1 and len(keylast)>1 and len(keylast[1])>0 and j.tools.text.isNumeric(keylast[1][-1]) and keynew[1]<>keylast[1]:
                    out.append("")   

            hrditem=self.items[key]   

            if hrditem.comments<>"":
                out.append("")
                out.append("%s" % (hrditem.comments.strip()))
            out.append("%-30s = %s" % (key, hrditem.getAsString()))
            keylast=key.split(".")
        out=out[1:]
        out="\n".join(out).replace("\n\n\n","\n\n")
        return out

    def __str__(self):
        return self.__repr__()

