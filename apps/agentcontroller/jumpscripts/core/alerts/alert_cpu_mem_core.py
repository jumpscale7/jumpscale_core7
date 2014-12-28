
from JumpScale import j

descr = """
Check on average cpu
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
license = "bsd"
version = "1.0"
period = 15*60  # always in sec
startatboot = True
order = 1
enable = True
async = True
log = False
queue ='process'
roles = ['master']


def action():
    osis = j.core.osis.client
    results = osis.search('system', 'stats', 'select mean(value) from /stats.gauges.\d+_\d+_(cpu.promile|memory.percent).*/ where time > now() - 1h;')
    for noderesult in results:
        parts = noderesult['name'].split('.')[2]
        value = noderesult['points'][0][-1]
        gid, nid, type = parts.split('_')
        gid = int(gid)
        nid = int(nid)
        if type == 'cpu':
            value /= 10.

        level = None
        if value > 95:
            level = 1
        elif value > 80:
            level = 2
        if level:
            #stats.gauges.500_6_cpu.promile
            msg = '%s load above treshhold value last hour avergage is %s' % (type.upper(), value)
            eco = j.errorconditionhandler.getErrorConditionObject(msg=msg, category='monitoring', level=level, type='OPERATIONS')
            eco.nid = nid
            eco.gid = gid
            eco.process()

if __name__ == '__main__':
    import JumpScale.grid.osis
    j.core.osis.client = j.core.osis.getClientByInstance('main')
    action()

