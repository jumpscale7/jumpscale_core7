from JumpScale import j
import JumpScale.baselib.remote
import JumpScale.baselib.serializers

class NginxFactory(object):

    def get(self, host, password):
        return Nginx(host, password)


class Nginx(object):

    def __init__(self, host, password):
        self.configPath = j.system.fs.joinPaths('/etc', 'nginx', 'conf.d')
        self.remoteApi = j.remote.cuisine.api
        j.remote.cuisine.fabric.env['password'] = password
        self.remoteApi.connect(host)

    def list(self):
        configfiles = self.remoteApi.run('ls %s' % self.configPath)
        return configfiles.split('  ')

    def load(self, configContent):
        return NginxConfig(configContent)

    def configure(self, fwObject):
        json = j.db.serializers.getSerializerType('j')
        fwDict = json.loads(fwObject)
        wsForwardRules = fwDict.get('wsForwardRules')
        configfile = j.system.fs.joinPaths(self.configPath, '%s.conf' % fwDict['name'])
        config = ''
        for rule in wsForwardRules:
            if len(rule['toUrls']) == 1:
                config += '''server {
    listen 80;
    server_name _;
    location %s {
        proxy_pass       %s;
        proxy_set_header Host      $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}''' % (rule['url'], rule['toUrls'][0])
            else:
                config += '''
upstream %s {
''' % fwDict['name']
                for toUrl in rule['toUrls']:
                    config += '    server %s;\n' % toUrl
                config += '}\n'
                config += '''
server {
    listen 80;
    server_name _;
    location %s {
        proxy_pass  http://%s;
    }
}''' % (rule['url'], fwDict['name'])

        if config:
            self.remoteApi.run('touch %s' % configfile)
            self.remoteApi.file_write(configfile, config)
            self.reload()

    def deleteConfig(self, name):
        configfile = j.system.fs.joinPaths(self.configPath, '%s.conf' % name)
        if self.remoteApi.file_exists(configfile):
            self.remoteApi.run('rm %s' % configfile)
            self.reload()

    def start(self):
        self.remoteApi.run('service nginx start')

    def stop(self):
        self.remoteApi.run('service nginx stop')

    def reload(self):
        self.remoteApi.run('service nginx reload')

    def restart(self):
        self.remoteApi.run('service nginx restart')

class NginxBaseConfig(object):
    def __init__(self, config):
        self._properties = list()
        for key, value in config:
            if isinstance(value, basestring):
                self._properties.append([key, value])
            else:
                self._specialconfig(key, value)

    @property
    def properties(self):
        return self._properties

    def addProperty(self, directive, value):
        self._properties.append((directive, value))

class NginxConfig(NginxBaseConfig):
    def __init__(self, configContent):
        self.http = None
        self.events = None
        import nginxparser
        config = nginxparser.loads(configContent)
        super(NginxConfig, self).__init__(config)
        if self.http is None:
            self.http = NginxHTTP([])
        if self.events is None:
            self.events = NginxEvents([])

    def _specialconfig(self, key, value):
        if key[0] == 'http':
            self.http = NginxHTTP(value)
        elif key[0] == 'events':
            self.events = NginxEvents(value)

    def returnContent(self):
        import jinja2
        import os
        jinja = jinja2.Environment(trim_blocks=True, variable_start_string="${", variable_end_string="}", loader=jinja2.FileSystemLoader( os.path.join(os.path.dirname(__file__), 'templates') ))
        template = jinja.get_template('nginxJinjaTemplate')
        content = template.render(properties= self.properties, events= self.events.properties, http= self.http, servers= self.http.servers)
        return content

class NginxEvents(NginxBaseConfig):
    pass

class NginxHTTP(NginxBaseConfig):
    def __init__(self, config):
        self.servers = list()
        super(NginxHTTP, self).__init__(config)

    def _specialconfig(self, key, value):
        if key[0] == 'server':
            self.servers.append(NginxServer(value))

    def addServer(self):
        server = NginxServer([])
        self.servers.append(server)
        return server

class NginxServer(NginxBaseConfig):
    def __init__(self, config):
        self.locations = list()
        super(NginxServer, self).__init__(config)

    def _specialconfig(self, key, value):
        if key[0] == 'location':
            self.locations.append(NginxLocation(key[1], value))

    def addLocation(self, path):
        location = NginxLocation(path, [])
        self.locations.append(location)
        return location


class NginxLocation(NginxBaseConfig):
    def __init__(self, path, config):
        self.path = path
        super(NginxLocation, self).__init__(config)
