def main(j, args, params, tags, tasklet):
    params.merge(args)

    doc = params.doc
    tags = params.tags

    doc = j.apps.system.contentmanager.extensions.defmanager.processDefs(doc)

    params.result = ("", doc)

    return params


def match(j, args, params, tags, tasklet):
    return True
