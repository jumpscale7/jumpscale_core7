from JumpScale import j


class GitClient(object):

    def __init__(self, base_dir):
        if not j.system.fs.exists(path=base_dir):
            j.events.inputerror_critical("git repo on %s not found." % base_dir)

        # split path to find parts
        base_dir = base_dir.replace("\\", "/")
        if base_dir.find("/code/") == -1:
            j.events.inputerror_critical(
                "jumpscale code management always requires path in form of $somewhere/code/$type/$account/$reponame")
        base = base_dir.split("/code/", 1)[1]

        if base.count("/") != 2:
            j.events.inputerror_critical(
                "jumpscale code management always requires path in form of $somewhere/code/$type/$account/$reponame")

        self.type, self.account, self.name = base.split("/")

        self.base_dir = base_dir

        gitconfig = "%s/.git/config" % base_dir
        config = j.system.fs.fileGetContents(gitconfig)

        self.remoteUrl = None
        self.branch_name = None

        for line in config.split("\n"):
            line = line.strip()
            if line == "":
                continue
            if line.find("url =") != -1 or line.find("url=") != -1:
                self.remoteUrl = line.split("=")[1].strip()

            if line.startswith("[branch"):
                self.branch_name = line.split("\"")[1].strip()

        if self.remoteUrl is None or self.branch_name is None:
            j.events.inputerror_critical("git repo on %s is corrupt could not find branch & remote url" % base_dir)

        self._repo = None

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return self.__repr__

    @property
    def repo(self):
        # Load git when we absolutly need it cause it does not work in gevent mode
        import git
        if not self._repo:
            j.system.process.execute("git config --global http.sslVerify false")
            if not j.system.fs.exists(self.base_dir):
                self._clone()
            else:
                self._repo = git.Repo(self.base_dir)
        return self._repo

    def init(self):
        self.repo

    def switchBranch(self, branch_name):
        self.repo.git.checkout(branch_name)

    def getModifiedFiles(self):
        result = {}
        result["D"] = []
        result["N"] = []
        result["M"] = []
        result["R"] = []

        cmd = "cd %s;git status --porcelain" % self.base_dir
        rc, out = j.system.process.execute(cmd)
        for item in out.split("\n"):
            if item.strip() == "":
                continue
            item2 = item.split(" ", 1)[1]
            result["N"].append(item2)

        for diff in self.repo.index.diff(None):
            path = diff.a_blob.path
            if diff.deleted_file:
                result["D"].append(path)
            elif diff.new_file:
                result["N"].append(path)
            elif diff.renamed:
                result["R"].append(path)
            else:
                result["M"].append(path)
        return result

    def addRemoveFiles(self):
        cmd = 'cd %s;git add -A :/' % self.base_dir
        j.system.process.execute(cmd)
        # result=self.getModifiedFiles()
        # self.removeFiles(result["D"])
        # self.addFiles(result["N"])

    def addFiles(self, files=[]):
        if files != []:
            self.repo.index.add(files)

    def removeFiles(self, files=[]):
        if files != []:
            self.repo.index.remove(files)

    def pull(self):
        self.repo.git.pull()

    def fetch(self):
        self.repo.git.fetch()

    def commit(self, message='', addremove=True):
        if addremove:
            self.addRemoveFiles()
        self.repo.index.commit(message)

    def push(self, force=False):
        if force:
            self.repo.git.push('-f')
        else:
            self.repo.git.push('--all')

    def getUntrackedFiles(self):
        return self.repo.untracked_files

    def patchGitignore(self):
        gitignore = '''# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]

# C extensions
*.so

# Distribution / packaging
.Python
develop-eggs/
eggs/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
.tox/
.coverage
.cache
nosetests.xml
coverage.xml

# Translations
*.mo

# Mr Developer
.mr.developer.cfg
.project
.pydevproject

# Rope
.ropeproject

# Django stuff:
*.log
*.pot

# Sphinx documentation
docs/_build/
'''
        ignorefilepath = j.system.fs.joinPaths(self.base_dir, '.gitignore')
        if not j.system.fs.exists(ignorefilepath):
            j.system.fs.writeFile(ignorefilepath, gitignore)
        else:
            lines = gitignore.split('\n')
            inn = j.system.fs.fileGetContents(ignorefilepath)
            lines = inn.split('\n')
            linesout = []
            for line in lines:
                if line.strip():
                    linesout.append(line)
            for line in lines:
                if line not in lines and line.strip():
                    linesout.append(line)
            out = '\n'.join(linesout)
            if out.strip() != inn.strip():
                j.system.fs.writeFile(ignorefilepath, out)
