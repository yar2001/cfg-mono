import src.Model.CFGNode
import copy
class DDGNode:

    def __init__(self, cfg_node: src.Model.CFGNode):
        self.line = copy.deepcopy(cfg_node.line)
        self.content = copy.deepcopy(cfg_node.content)
        # we don't have children in dgg, parent instead
        self.children = []
        self.parent = []
        self.function_calls = copy.deepcopy(cfg_node.function_calls)
        self.used_vars = copy.deepcopy(cfg_node.used_vars)
        self.defined_vars = copy.deepcopy(cfg_node.defined_vars)
        self.cfg_prototype = cfg_node

    def add_child(self, child):
        pass

    def add_parent(self, parent):
        if parent not in self.parent:
            self.parent.append(parent)

    def __str__(self) -> str:
        content = self.content.replace('\n', '\\n')
        return f'["{content}\n(line: {self.line})"]\n'
