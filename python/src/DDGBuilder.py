import copy
import src.Model.CFGNode
import src.Model.DDGNode
import time
import threading


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
        self.build_with_recursive: bool = True
        self.var_dict: dict = {}
        self.visited_table: set = set()
        # time limit to build the ddg, if timeout , everything about ddg would be None
        self.time_limit: float = 1
        self.timeout: bool = False

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
        thread = threading.Thread(target=self._build_ddg_imp)
        thread_id = thread.ident
        self.timeout = False
        start_time = time.time()
        thread.start()

        while thread.is_alive():
            elapsed_time = time.time() - start_time
            if elapsed_time > self.time_limit:
                # how to stop safeley
                thread._stop()
                self.timeout = True


    def _build_ddg_imp(self):
        if self.build_with_recursive:
            for each in self.cfg_nodes:
                if id(each) not in self.visited_table:
                    self.dfs_search(each)
        else:
            for each in self.cfg_nodes:
                if id(each) not in self.visited_table:
                    self.dfs_no_recursive()

    def dfs_search(self, node: src.Model.CFGNode.CFGNode):

        if isinstance(node, src.Model.CFGNode.ContinueNode):
            self.visit_Continue(node, copy.deepcopy(self.var_dict))

        if issubclass(type(node), src.Model.CFGNode.JumpNode):
            return

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
            try:
                del self.var_dict[each]
            except KeyError:
                pass

        for each in var_backup:
            for key, value in each.items():
                self.var_dict[key] = value

    def dfs_no_recursive(self):
        stack = []
        var_dict: dict = {}
        # we should find the start node
        # function is same as to the CFGBuilder's __get_head_node function
        def get_head_nodes() -> list:
            ret = []
            visited_table: dict = {}

            for each in self.cfg_nodes:
                if id(each) not in visited_table:
                    visited_table[(id(each))] = each

            for each in self.cfg_nodes:
                for each_child in each.children:
                    # if it is a child, it must not a head node
                    try:
                        del visited_table[id(each_child)]
                    except KeyError:
                        pass

            for key, value in visited_table.items():
                ret.append(value)

            return ret
        # get heads
        start_nodes: list = get_head_nodes()

        for node in start_nodes:
            if id(node) not in self.visited_table:
                stack.append(node)
                self.visited_table.add(id(node))

            while stack:
                current = stack.pop()
                self.__process_one_node(current, var_dict)
                for child in current.children:
                    if id(child) not in self.visited_table:
                        stack.append(child)
                        self.visited_table.add(id(child))
                    if isinstance(type(child), src.Model.CFGNode.ContinueNode):
                        self.visit_Continue(child, copy.deepcopy(var_dict))

    def visit_Continue(self, node, var_dict: dict):
        stack = []
        stack.append(node)
        visited_table: set = set()
        while stack:
            current = stack.pop()
            self.__process_one_node(current, var_dict)
            for child in current.children:
                if id(child) not in visited_table:
                    stack.append(child)
                    visited_table.add(id(child))
                if child is node:
                    return

    def __process_one_node(self, node, var_dict: dict):
        var_backup: list = []
        ddg_node_id: int = self.cfg_node_id_mapping[id(node)]
        ddg_node: src.Model.DDGNode.DDGNode = self.ddg_node_instances[ddg_node_id]
        # deal the variable
        for each in node.used_vars:
            try:
                target_obj_id = var_dict[each]
                target_id = self.ddg_node_id_mapping[target_obj_id]
                ddg_node.add_parent(self.ddg_node_instances[target_id])
            except KeyError:
                pass

        for each in node.defined_vars:
            try:
                var_backup.append({each: var_dict[each]})
            except KeyError:
                pass
            var_dict[each] = id(ddg_node)

        for each in node.defined_vars:
            # reverse variable, delete them
            try:
                del var_dict[each]
            except KeyError:
                pass

        for each in var_backup:
            for key, value in each.items():
                var_dict[key] = value