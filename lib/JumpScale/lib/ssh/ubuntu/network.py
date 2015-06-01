from JumpScale import j
from fabric.api import settings
import re 
import netaddr

class NetworkingErro(Exception):
    pass

class NetworkManager(object):

    def __init__(self, manager):
        self.manager = manager
        self._nics = None
    
    def _nicExists(self, nic):
        if nic not in self.nics:
            raise NetworkingErro('Invalid NIC')

    def ipGet(self, device):
        """
        Get IP of devie
        Result (ip, netmask, gateway)
        """
        self._nicExists(device)
        cmd  = 'echo `ip a | grep %s | sed -n 2p | xargs | cut -d " " -f 2`' % device
        res = self.manager.connection.run(cmd)
        ipmask = netaddr.IPNetwork(res)
        netmask = str(ipmask.netmask)
        ip = str(ipmask.ip) 
        return (ip, netmask)
    
    def ipSet(self, device, ip=None, netmask=None, gw=None, inet='dhcp', commit=False):
        """
        Return all interfaces that has this ifname
        """
        self._nicExists(device)
        
        if inet not in ['static', 'dhcp']:
            raise ValueError('Invalid inet .. use either dhcp or static')
        
        if inet == 'static' and (not ip or not netmask):
            raise ValueError('ip, and netmask, are required in static inet.')
        
        file = '/etc/network/interfaces.d/%s' % device
        content = 'auto %s\n' % device

        if inet == 'dhcp':
            content += 'iface %s inet dhcp\n' % device
        else:
            content += 'iface %s inet static\naddress %s\nnetmask %s\n' % (device, ip, netmask)
            if gw:
                content += 'gateway %s\n' % gw
        
        self.manager.connection.file_write(file, content)
        
        if commit:
            self.commit(device)
        else:
            j.logger.log('Do NOT FORGET TO COMMIT', 2)

    def ipReset(self, device, commit=False):
        self._nicExists(device)
        file = '/etc/network/interfaces.d/%s' % device
        self.manager.connection.file_write(file, '')
        
        if commit:
            self.commit()
        else:
            j.logger.log('Do NOT FORGET TO COMMIT', 2)

    @property
    def nics(self):
        if self._nics is None:
            ifaces =  self.manager.connection.run('ls --color=never -1 /sys/class/net')
            self._nics = ifaces.split('\r\n')
        return self._nics


    def nsGet(self):
        file = self.manager.connection.file_read('/etc/resolv.conf')
        results = []

        for line in file.split('\n'):                                   
            nameserver = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',line)
            if nameserver:
                nameserver = nameserver.string.replace('nameserver', '').strip()
                results.append(nameserver)
        return results

    def nsSet(self, nameservers=[], commit=False):
        if not nameservers:
            raise ValueError('You need to provide at least one DNS server')
        if not isinstance(nameservers, list):
            raise ValueError('nameservers must be a list')
        
        content = '#EDITED BY JUMPSCALE NETWORK MANAGER\n'
        content += '#DO NOT EDIT THIS FILE BY HAND -- YOUR CHANGES WILL BE OVERWRITTEN\n'
        
        for ns in nameservers:
            content += 'nameserver %s\n' % ns
        self.manager.connection.file_write('/etc/resolv.conf', content)

        if commit:
            self.commit()
        else:
            j.logger.log('Do NOT FORGET TO COMMIT', 2)

    def commit(self, device=None):
        #- make sure loopback exist
        content = 'auto lo\niface lo inet loopback\n'
        self.manager.connection.file_write('/etc/network/interfaces.d/lo', content)
        
        with settings(abort_exception=NetworkingErro):
            self.manager.connection.upstart_restart('networking')
            if device:
                j.logger.log('Restarting interface %s' % device, 2)
                self.manager.connection.run('ifdown %s && ifup %s' % (device, device))
        j.logger.log('DONE', 2)