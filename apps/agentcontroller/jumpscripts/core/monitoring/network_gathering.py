from JumpScale import j
import psutil

descr = """
gather statistics about system
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "info.gather.nic"
period = 300 #always in sec
enable=True
async=True
queue='process'
roles = []
log=False

def action():
    ncl = j.core.osis.getClientForCategory(j.core.osis.client, "system", "nic")
    rediscl = j.clients.redis.getByInstanceName('system')
    netinfo=j.system.net.getNetworkInfo()
    results = dict()
    pattern = None
    if j.application.config.exists('nic.pattern'):
        pattern = j.application.config.getStr('nic.pattern')
    
    for mac,val in netinfo.iteritems():
        name,ipaddr=val
        if pattern and j.codetools.regex.match(pattern,name) == False:
                continue

        if ipaddr:
            ipaddr=ipaddr.split(",")
            if ipaddr==['']:
                ipaddr=[]
        else:
            ipaddr=[]

        nic = ncl.new()
        oldkey = rediscl.hget('nics', name)

        nic.name = name
        results[name] = nic
        nic.active=True
        nic.gid = j.application.whoAmI.gid
        nic.nid = j.application.whoAmI.nid
        nic.ipaddr=ipaddr
        nic.mac=mac
        nic.name=name

        ckey = nic.getContentKey()
        if oldkey != ckey:
            print('Nic %s changed ' % name)
            guid, _, _ = ncl.set(nic)
            rediscl.hset('nics', name, ckey)


    nics = ncl.search({'nid': j.application.whoAmI.nid, 'gid': j.application.whoAmI.gid})[1:]
    #find deleted nices
    for nic in nics:
        if nic['active'] and nic['name'] not in results:
            #no longer active
            print "NO LONGER ACTIVE:%s" % nic['name']
            nic['active'] = False
            ncl.set(nic)
            rediscl.hdel('nics', nic['name'])

if __name__ == '__main__':
    import JumpScale.grid.osis
    j.core.osis.client = j.core.osis.getClientByInstance('processmanager')
    action()
