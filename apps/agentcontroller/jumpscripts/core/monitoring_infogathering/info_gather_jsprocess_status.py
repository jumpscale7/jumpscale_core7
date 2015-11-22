
from JumpScale import j

descr = """
Check if all jsprocesses are running
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
period = 60  # always in sec
timeout = period * 0.2
order = 1
enable = True
async = True
log = True
queue ='process'
roles = []


def action():
    results =list()
    for ays in j.atyourservice.findTemplates():
        instances = ays.listInstances()
        for instance in instances:
            aysinstance = ays.getInstance(instance)
            result = dict()
            result['state'] = 'OK'
            result['message'] = "Process %s:%s:%s is running" % (aysinstance.domain, aysinstance.name, instance)
            result['category'] = 'AYS Process'
            if not aysinstance.actions.check_up_local(aysinstance, wait=False):
                message = "Process %s:%s:%s is not running" % (aysinstance.domain, aysinstance.name, instance)
                j.errorconditionhandler.raiseOperationalWarning(message, 'monitoring')
                result['state'] = 'WARNING'
                result['message'] = message
                result['category'] = 'AYS Process'
            results.append(result)
            
    return results
         
if __name__ == '__main__':
    action()
