from JumpScale import j

import JumpScale.baselib.jumpscripts

j.core.jumpscripts.load("/opt/jumpscale/apps/agentcontroller2/distrdir/jumscripts/")

print j.core.jumpscripts.execute("system","testactor","echo",msg="my message")
