
def main(j, args, params, tags, tasklet):
    params.merge(args)

    out = ""

    spaces = j.core.portal.active.spacesloader.spaces
    for item in spaces.keys():
        model = spaces[spacename].model
        out += "* [%s|/system/ReloadApplication/?name=%s]\n" % (item, item.lower().strip("/"))

    params.result = (out, params.doc)

    return params


def match(j, args, params, tags, tasklet):
    return True
