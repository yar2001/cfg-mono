import copy
import src.Model.CFGNode
import src.Model.DDGNode


class DDGVisitor:

    def __init__(self, cfg_nodes: list, name: str='main'):
        self.cfg_nodes = copy.deepcopy(cfg_nodes)
        # all node instances collector
        self.ddg_nodes: list = []
        self.ddg_node_counter: int = 1
        # from instance id (id function) to search node
        self.cfg_node_id_mapping = {}
        self.ddg_node_id_mapping = {}
        # from my id to search node
        self.ddg_node_instances: dict = {}
        self.name = name
        self.var_dict: dict = {}
        self.visited_table: set = set()

        for each in self.cfg_nodes:

            if id(each) not in self.cfg_node_id_mapping:
                self.create_ddg_node(each)

            for child in each.children:
                if id(child) not in self.cfg_node_id_mapping:
                    self.create_ddg_node(child)

    def create_ddg_node(self, cfg_node: src.Model.CFGNode.CFGNode):
        self.cfg_node_id_mapping[id(cfg_node)] = self.ddg_node_counter
        # create new ddg node
        node = src.Model.DDGNode.DDGNode(cfg_node)
        self.ddg_node_instances[self.ddg_node_counter] = node
        self.ddg_node_id_mapping[id(node)] = self.ddg_node_counter
        self.ddg_node_counter = self.ddg_node_counter + 1
        self.ddg_nodes.append(node)

    def build_ddg(self):
        # from var_name to node_id
        self.var_dict.clear()
        self.visited_table.clear()
        for each in self.cfg_nodes:
            if id(each) not in self.visited_table:
                self.dfs_search(each)

    def dfs_search(self, node: src.Model.CFGNode.CFGNode):
        self.visited_table.add(id(node))
        var_backup: list = []
        ddg_node_id: int = self.cfg_node_id_mapping[id(node)]
        ddg_node: src.Model.DDGNode.DDGNode = self.ddg_node_instances[ddg_node_id]
        # deal the variable
        for each in node.used_vars:
            try:
                target_obj_id = self.var_dict[each]
                target_id = self.ddg_node_id_mapping[target_obj_id]
                ddg_node.add_parent(self.ddg_node_instances[target_id])
            except KeyError:
                pass

        for each in node.defined_vars:
            try:
                var_backup.append({each: self.var_dict[each]})
            except KeyError:
                pass
            self.var_dict[each] = id(ddg_node)

        for each in node.children:
            self.dfs_search(each)

        for each in node.defined_vars:
            # reverse variable, delete them
            del self.var_dict[each]

        for each in var_backup:
            for key, value in each.items():
                self.var_dict[key] = value
