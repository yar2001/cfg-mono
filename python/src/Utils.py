import json
import src.CFGBuilder
import src.DDGBuilder
import src.Model.CFGNode
import src.Model.DDGNode
import src.Model.AdapterNode

class DataContainer:
    def __init__(self, cfg_builder: src.CFGBuilder.CFGVisitor, ddgs: list=None,
                 export_function: bool=False):
        self.data: dict = {}
        self.id_counter: int = 1
        self.export_function: bool = export_function
        self.node_instance = {}
        self.cfg_data = cfg_builder
        if ddgs is not None:
            self.ddg_data = ddgs


    def export_cfg_mermaid(self) -> str:
        self.id_counter: int = 1
        self.node_instance.clear()
        if self.cfg_data is None:
            return 'error: empty cfg_data'
        ret = 'graph TD;\n'
        ret += f'subgraph \"main\"\n'
        ret += self._convert_nodes_to_str(self.cfg_data.cfg_nodes)
        # main edge
        for each in self.cfg_data.cfg_nodes:
            node_id = id(each)
            for child in each.children:
                child_id = id(child)
                ret += f'{self.node_instance[node_id]}-->{self.node_instance[child_id]}\n'
        ret += 'end\n'

        # function related
        if not self.export_function:
            return ret
        for key, value in self.cfg_data.function_def_node.items():
            if key == 'main':
                continue
            ret += f'subgraph \"{key}\"\n'
            ret += self._convert_nodes_to_str(value.cfg_nodes)
            # edge
            for each in value.cfg_nodes:
                node_id = id(each)
                for child in each.children:
                    child_id = id(child)
                    ret += f'{self.node_instance[node_id]}-->{self.node_instance[child_id]}\n'
            ret += 'end\n'

        return ret

    def _convert_nodes_to_str(self, nodes: list, ignore_end: bool=False, ddg_index=0) -> str:
        ret = ''
        for each in nodes:
            if ignore_end and isinstance(each, src.Model.DDGNode.DDGNode):
                if self.is_end_node(each, ddg_index):
                    continue
            if id(each) not in self.node_instance:
                self.node_instance[id(each)] = self.id_counter
                self.id_counter = self.id_counter + 1
                ret += f'{self.node_instance[id(each)]}{str(each)}'
            for child in each.children:
                if id(child) not in self.node_instance:
                    self.node_instance[id(child)] = self.id_counter
                    self.id_counter = self.id_counter + 1
                    ret += f'{self.node_instance[id(child)]}{str(child)}'
        return ret

    def export_ddg_mermaid(self) -> str:
        self.id_counter: int = 1
        self.node_instance.clear()
        if self.ddg_data is None:
            return 'error: empty ddg'
        ret = 'graph TD;\n'
        # export main function
        ret += f'subgraph \"main\"\n'
        ret += self._convert_nodes_to_str(self.ddg_data[0].ddg_nodes, True, 0)
        # edge
        for each in self.ddg_data[0].ddg_nodes:
            if self.is_end_node(each):
                continue
            node_id = id(each)
            for each_parent in each.parent:
                if self.is_end_node(each_parent):
                    continue
                parent_id = id(each_parent)
                ret += f'{self.node_instance[parent_id]}-->{self.node_instance[node_id]}\n'
        ret += 'end\n'

        # function related
        if not self.export_function:
            return ret
        index: int = 0
        while index < len(self.ddg_data):
            current_ddg: src.DDGBuilder.DDGVisitor = self.ddg_data[index]
            index = index + 1
            # get function name
            name = current_ddg.name
            if name == 'main':
                continue
            ret += f'subgraph \"{name}\"\n'
            ret += self._convert_nodes_to_str(current_ddg.ddg_nodes, True, index)
            # edge
            for each in current_ddg.ddg_nodes:
                node_id = id(each)
                for parent in each.parent:
                    parent_id = id(parent)
                    ret += f'{self.node_instance[parent_id]}-->{self.node_instance[node_id]}\n'
            ret += 'end\n'


        return ret

    def is_end_node(self, ddg_node: src.Model.DDGNode.DDGNode, index: int=0) -> bool:
        cfg_node = ddg_node.cfg_prototype

        if issubclass(type(cfg_node), src.Model.CFGNode.EndNode):
            return True
        else:
            return False

    def _pack(self):
        self._pack_cfg()

    def _pack_cfg(self):

        def create_cfg_data_node(cfg_node: src.Model.CFGNode, id: int) -> src.Model.AdapterNode.DataNode:
            node = src.Model.AdapterNode.CFGDataNode(cfg_node, id)
            return node

        def create_cfg_edge_node(source: int, target: int, ddg_node: src.Model.CFGNode.CFGNode)\
                -> src.Model.AdapterNode.CFGDataEdge:
            node = src.Model.AdapterNode.CFGDataEdge(0, source, target)
            return node


        # main
        visited_table: set = set()
        # id(cfg_node) --> id_counter
        cfg_node_to_id_mapping: dict = {}
        cfg_data_nodes: list = []
        cfg_edge_nodes: list = []
        id_counter: int = 0
        for each_cfg in self.cfg_data.cfg_nodes:

            if id(each_cfg) not in visited_table:
                cfg_data_nodes.append(create_cfg_data_node(each_cfg, id_counter))
                node_id: int = id_counter
                cfg_node_to_id_mapping[id(each_cfg)] = id_counter
                id_counter = id_counter + 1
                visited_table.add(id(each_cfg))
            else:
                # find id
                node_id: int = cfg_node_to_id_mapping[id(each_cfg)]

            for child in each_cfg.children:
                if id(child) not in visited_table:
                    cfg_data_nodes.append(create_cfg_data_node(child, id_counter))
                    cfg_node_to_id_mapping[id(child)] = id_counter
                    cfg_edge_nodes.append(create_cfg_edge_node(node_id, id_counter, child))
                    id_counter = id_counter + 1
                    visited_table.add(id(child))
                else:
                    child_id: int = cfg_node_to_id_mapping[id(child)]
                    cfg_edge_nodes.append(create_cfg_edge_node(node_id, child_id, child))

        id_counter: int = 0
        for each in cfg_edge_nodes:
            each.id = id_counter
            id_counter = id_counter + 1

        # build data dict
        nodes: list = []
        edges: list = []
        for each_cfg in cfg_data_nodes:
            nodes.append(str(each_cfg))

        for each_edge in cfg_edge_nodes:
            edges.append(str(each_edge))

        self.data['nodes'] = nodes
        self.data['edges'] = edges


    def _pack_ddg(self):

        def create_ddg_data_node():
            pass

        def create_ddg_edge_node():
            pass
        # main
        # visited_table: set = set()
        # # id(cfg_node) --> id_counter
        # ddg_node_to_id_mapping: dict = {}
        # ddg_data_nodes: list = []
        # ddg_edge_nodes: list = []
        # id_counter: int = 0
        # for single_ddg in self.ddg_data:
        #     for each_ddg in single_ddg:
        #         if id(each_ddg) not in visited_table:
        #             ddg_data_nodes.append(create_cfg_data_node(each_cfg, id_counter))
        #             node_id: int = id_counter
        #             ddg_node_to_id_mapping[id(each_cfg)] = id_counter
        #             id_counter = id_counter + 1
        #             visited_table.add(id(each_cfg))
        #         else:
        #             # find id
        #             node_id: int = cfg_node_to_id_mapping[id(each_cfg)]
        #
        #         for child in each_cfg.children:
        #             if id(child) not in visited_table:
        #                 cfg_data_nodes.append(create_cfg_data_node(child, id_counter))
        #                 cfg_node_to_id_mapping[id(child)] = id_counter
        #                 cfg_edge_nodes.append(create_cfg_edge_node(node_id, id_counter, child))
        #                 id_counter = id_counter + 1
        #                 visited_table.add(id(child))
        #             else:
        #                 child_id: int = cfg_node_to_id_mapping[id(child)]
        #             cfg_edge_nodes.append(create_cfg_edge_node(node_id, child_id, child))
        #
        # id_counter: int = 0
        # for each in cfg_edge_nodes:
        #     each.id = id_counter
        #     id_counter = id_counter + 1
        #
        # # build data dict
        # nodes: list = []
        # edges: list = []
        # for each_cfg in cfg_data_nodes:
        #     nodes.append(str(each_cfg))
        #
        # for each_edge in cfg_edge_nodes:
        #     edges.append(str(each_edge))
        #
        # self.data['nodes'] = nodes
        # self.data['edges'] = edges

    def __str__(self) -> str:
        """
            export json str
        :return: json format str
        """
        self.data.clear()
        base_info: dict = {
            'directed': True,
            'multigraph': False,
            'language': 'python',
        }
        target_info: dict = {}
        for key, value in base_info.items():
            target_info[key] = value
        # pack target data
        self._pack()

        # pack mermaid code
        target_info['mermaid'] = self.export_cfg_mermaid()
        target_info['ddg_mermaid'] = self.export_ddg_mermaid()

        # data is prerogative
        for key, value in self.data.items():
            target_info[key] = value

        return json.dumps(target_info)