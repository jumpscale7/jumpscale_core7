from JumpScale import j

parentclass = j.core.osis.getOsisImplementationParentClass("system")  # is the name of the namespace

class mainclass(parentclass):

    """
    """

    def set(self, key, value, waitIndex=False, session=None):
        guid, new, changed = super(parentclass, self).set(key, value, session=session)

        if changed:
            print "OBJECT CHANGED WRITE"
            u = j.core.osis.cmds._getOsisInstanceForCat("system", "user")
            for user in value['users']:
                userkey = "%s_%s" % (value['gid'], user)
                if u.exists(userkey, session=session) == False:
                    # group does not exist yet, create
                    usernew = u.getObject()
                    usernew.id = user
                    usernew.gid = value['gid']
                    usernew.domain = value['domain']
                    usernew.groups = [value['id']]
                    userguid, a, b = u.set(usernew.guid, usernew.__dict__, session=session)
                else:
                    user = u.get(userkey, session=session)
                    if value['id'] not in user['groups']:
                        user['groups'].append(value['id'])
                        u.set(user['guid'], user, session=session)

        return [guid, new, changed]
