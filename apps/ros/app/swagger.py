import os
import copy

from eve_docs.config import get_cfg
from flask.ext.bootstrap import Bootstrap
from flask import request
import flask
from flask import send_from_directory
from flask import render_template


INMAP = {'post': 'formData', 'get': 'query', 'put': 'path', 'delete': 'path'}

INPUTMAP = {'bool': {'type': 'boolean'},
           'str': {'type': 'string'},
           'string': {'type': 'string'},
           'int': {'type': 'integer'},
           'float': {'type': 'number'},
           'list': {'type': 'string'},
           'dict': {'type': 'string'},
           }

RETURNMAP = {'bool': {'type': 'boolean'},
           'str': {'type': 'string'},
           'string': {'type': 'string'},
           'int': {'type': 'integer'},
           'float': {'type': 'number'},
           'list': {'$ref': '#/definitions/strarray'},
           'dict': {'$ref': '#/definitions/object'},
           }

def expose_docs(app, static_path):
    Bootstrap(app)
    
    @app.route('/docs/spec.json')
    def specs():
        url = request.url_root.replace('https://', '').replace('http://', '').replace(request.host, '').rstrip('/')
        catalog = {'swagger': '2.0', 'basePath': url, 'paths': {}, 'tags':[]}
        catalog['info'] = {'description': 'Autogenerated swagger for ROS', 'version': '7.0', 'title': 'JumpScale ROS API'}
        catalog['definitions'] = {'strarray': {'type': 'array', 'items': {'type': 'string'}},
                                  'object': { "type": "object", "additionalProperties": {"type": "string"}}}
        cfg = copy.deepcopy(get_cfg())
        for modelname, model in cfg['domains'].iteritems():
            catalog['tags'].append({'name': modelname, 'description': modelname})
            for path, pathmethods in model.iteritems():
                newpathmethods = {}
                for k, v in pathmethods.iteritems():
                    if 'params' in v:
                        params = v.pop('params')
                        for param in params:
                            type = param.get('type')
                            if '{' in path and '{%s}' % param['name'] in path:
                                param['in'] = 'path'
                            else:
                                param['in'] = INMAP.get(k.lower())
                            param['type'] = INPUTMAP.get(type, INPUTMAP['string'])['type']
                        v['parameters'] = params
                    newpathmethods[k.lower()] = v
                catalog['paths'][path] = newpathmethods
                for methodname, methodinfo in newpathmethods.iteritems():
                    res = {'type': 'string'}
                    if 'params' in methodinfo:
                        for param in params:
                            if param.get('name') == 'result':
                                type = param.get('type')
                                res = RETURNMAP.get(type, RETURNMAP['string'])
                    catalog['paths'][path][methodname]['description'] = methodinfo['label']
                    catalog['paths'][path][methodname]['tags'] = modelname
                    catalog['paths'][path][methodname]['responses'] = {'200': {'description': 'result', 'schema': res}}
                    catalog['paths'][path][methodname]['summary'] = methodinfo['label']
                    catalog['paths'][path][methodname]['operationId'] = '%s_%s' % (methodname, path.replace('/', '_'))
        return flask.jsonify(**catalog)

    @app.route('/docs')
    def docs():
        return send_from_directory(static_path, 'ros_index.html')
    
    @app.route('/lib/<path:path>')
    def js(path):
        return send_from_directory(os.path.join(static_path, 'lib'), path)
    
    @app.route('/css/<path:path>')
    def css(path):
        return send_from_directory(os.path.join(static_path, 'css'), path)
    
    @app.route('/images/<path:path>')
    def images(path):
        return send_from_directory(os.path.join(static_path, 'images'), path)
    
    @app.route('/fonts/<path:path>')
    def fonts(path):
        return send_from_directory(os.path.join(static_path, 'fonts'), path)