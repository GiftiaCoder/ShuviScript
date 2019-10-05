import ply.lex as lex
import ply.yacc as yacc
import script.lexer
import script.syntax

import json
import os


class Graph(object):

    def __init__(self, script_text, method_registry, conf_paths, lexmod=None, synmod=None, logger=None):
        self.method_registry = method_registry
        self.logger = logger
        self.conf_paths = conf_paths

        self.node_map = {}
        self.conf_map = {}
        # to record the last loading time stamp for each conf file
        self.conf_update_ts = {}
        self.__load_confs__()

        if not lexmod:
            lexmod = script.lexer
        if not synmod:
            synmod = script.syntax

        lexer = lex.lex(module=lexmod)
        syntax = yacc.yacc(module=synmod)
        syntax.__define_node__ = __define_node__
        if logger:
            syntax.__logger__ = logger

        syntax.parse(script_text, lexer=lexer)

    def run(self, sess, outputpath):
        nodename, outputname = outputpath.split('.')
        node = self.node_map.get(nodename, None)
        if not node:
            self.logger.error('node of name[%s] not found' % nodename)
            return None
        return node.run(sess, outputname)

    def init(self, sess, tf_initializer):
        sess.run(tf_initializer)
        for node in self.node_map.itervalues():
            node.init(sess)

    def conf(self):
        self.__load_confs__()

    # private
    def __define_node__(self, nodename, methodname, outputs, placeholders, inputs):
        if methodname not in self.method_registry:
            self.logger.error('method name[%s] not registed' % methodname)
        if nodename in self.node_map:
            self.logger.error('node[%s] has already registed' % nodename)

        input_edge_list, input_node_list = [], set()
        for input_node_name, input_edge_name in inputs:
            input_node = self.node_map.get(input_node_name, None)
            if not input_node:
                self.logger.error('undefined node[%s]' % input_node_name)
            input_edge = input_node.get_output(input_edge_name)
            if not input_edge:
                self.logger.error('undefined edge[%s] of node[%s]' % (input_edge_name, input_node_name))
            input_node_list.add(input_node)
            input_edge_list.append(input_edge)

        node = self.method_registry[methodname](input_edge_list,
                                                list(input_node_list),
                                                self.conf_map,
                                                self.conf_map.get(nodename, None),
                                                self.logger)
        node.post_construct()

        __verify_outputs__(node, outputs)
        __verify_placeholders__(node, placeholders)

        self.node_map[nodename] = node

    def __load_confs__(self):
        for conf_path in self.conf_paths:
            try:
                cur_ts = os.path.getmtime(conf_path)
                if conf_path not in self.conf_update_ts or self.conf_update_ts[conf_path] != cur_ts:
                    with open(conf_path) as i_f:
                        js = json.loads(i_f.read())
                        for k in js:
                            self.conf_map[k] = js[k]
                    self.conf_update_ts[conf_path] = cur_ts
            except Exception as e:
                self.logger.warning('catch exception when loading conf file[%s]: %s' % (conf_path, str(e)))

    @staticmethod
    def __verify_outputs__(node, names):
        for name in names:
            output = node.get_output(name)
            if not output:
                self.logger.error('output[%s] not defined' % name)

    @staticmethod
    def __verify_placeholders__(node, names):
        for name in names:
            placeholder = node.get_placeholder(name)
            if not placeholder:
                self.logger.error('placeholder[%s] not defined' % name)

