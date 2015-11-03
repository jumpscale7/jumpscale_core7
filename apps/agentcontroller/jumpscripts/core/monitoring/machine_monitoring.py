from JumpScale import j

descr = """
gather statistics about machines
"""

organization = "jumpscale"
author = "deboeckj@incubaid.com"
license = "bsd"
version = "1.0"
category = "monitoring.machine"
period = 60*60 #always in sec
timeout = period * 0.2
order = 1
enable=True
async=True
queue='process'
log=False

roles = []

from xml.etree import ElementTree
try:
    import JumpScale.lib.qemu_img
    import libvirt
except:
    enable=False

def getContentKey(obj):
    dd=j.code.object2json(obj, True, ignoreKeys=["guid","id","sguid","moddate", 'lastcheck'], ignoreUnderscoreKeys=True)
    return j.tools.hash.md5_string(str(dd))

def action():
    syscl = j.clients.osis.getNamespace('system')
    rediscl = j.clients.redis.getByInstance('system')
    con = libvirt.open('qemu:///system')
    #con = libvirt.open('qemu+ssh://10.101.190.24/system')
    stateMap = {libvirt.VIR_DOMAIN_RUNNING: 'RUNNING',
                libvirt.VIR_DOMAIN_NOSTATE: 'NOSTATE',
                libvirt.VIR_DOMAIN_PAUSED: 'PAUSED'}

    allmachines = syscl.machine.search({'nid': j.application.whoAmI.nid, 
                                        'gid': j.application.whoAmI.gid, 
                                        'state': {'$ne': 'DELETED'}
                                        })[1:]
    allmachines = { machine['guid']: machine for machine in allmachines }
    domainmachines = list()
    try:
        domains = con.listAllDomains()
        for domain in domains:
            machine = syscl.machine.new()
            machine.id = domain.ID()
            machine.guid = domain.UUIDString().replace('-', '')
            domainmachines.append(machine.guid)
            machine.name = domain.name()
            print 'Processing', machine.name
            machine.nid = j.application.whoAmI.nid
            machine.gid = j.application.whoAmI.gid
            machine.type = 'KVM'
            xml = ElementTree.fromstring(domain.XMLDesc())
            netaddr = dict()
            for interface in xml.findall('devices/interface'):
                mac = interface.find('mac').attrib['address']
                alias = interface.find('alias')
                name = None
                if alias is not None:
                    name = alias.attrib['name']
                netaddr[mac] = [ name, None ]

            machine.mem = int(xml.find('memory').text)

            machine.netaddr = netaddr
            machine.lastcheck = j.base.time.getTimeEpoch()
            machine.state = stateMap.get(domain.state()[0], 'STOPPED')
            machine.cpucore = int(xml.find('vcpu').text)

            ckeyOld = rediscl.hget('machines', machine.guid)
            ckey = getContentKey(machine)
            if ckeyOld != ckey:
                rediscl.hset('machines', machine.guid, ckey)
                print 'Saving', machine.name
                syscl.machine.set(machine)

            for disk in xml.findall('devices/disk'):
                if disk.attrib['device'] != 'disk':
                    continue
                diskattrib = disk.find('source').attrib
                path = diskattrib.get('dev', diskattrib.get('file'))
                vdisk = syscl.vdisk.new()
                ckeyOld = rediscl.hget('vdisks', path)
                vdisk.path = path
                vdisk.type = disk.find('driver').attrib['type']
                vdisk.devicename = disk.find('target').attrib['dev']
                vdisk.machineid = machine.guid
                vdisk.active = j.system.fs.exists(path)
                if vdisk.active:
                    try:
                        diskinfo = j.system.platform.qemu_img.info(path)
                        vdisk.size = diskinfo['virtual size']
                        vdisk.sizeondisk = diskinfo['disk size']
                        vdisk.backingpath = diskinfo.get('backing file', '')
                    except Exception:
                        # failed to get disk information
                        vdisk.size = -1
                        vdisk.sizeondisk = -1
                        vdisk.backingpath = ''

                if ckeyOld != vdisk.getContentKey():
                    #obj changed
                    rediscl.hset('vdisks', path, vdisk.getContentKey())
                    syscl.vdisk.set(vdisk)
    finally:
        deletedmachines = set(allmachines.keys()) - set(domainmachines)
        for deletedmachine in deletedmachines:
            machine = allmachines[deletedmachine]
            print 'Deleting', machine.name
            rediscl.hdel('machines', deletedmachine)
            machine['state'] = 'DELETED'
            syscl.machine.set(machine)
        con.close()

if __name__ == '__main__':
    import JumpScale.grid.osis
    j.core.osis.client = j.clients.osis.getByInstance('main')
    action()
