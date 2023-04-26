"""
    Data dependence graph builder, for building Graph use
"""
# Gadia, 2023
import src.Model.CFGNode
import ast
import astor


class CFGVisitor(ast.NodeVisitor):
    def __init__(self, source_code, base_line=0):
        self.source_code = source_code
        self.cfg_nodes = []
        self.cfg_exit_nodes = []
        self.function_def_node: dict = {}
        self.function_doc_string: dict = {}
        self.base_line: int = base_line

    def build_cfg(self):
        self.visit(ast.parse(self.source_code))
        self.cfg_nodes += self.cfg_exit_nodes
        return self.cfg_nodes

    def visit_Module(self, node):
        for item in node.body:
            self.visit(item)

    def visit_FunctionDef(self, node):
        cfg_visitor = CFGVisitor('')

        # get docstring, @TODO
        doc_string = ast.get_docstring(node)

        # get args
        args: list = []
        for each_arg in node.args.args:
            args.append(each_arg.arg)

        # parse body
        for item in node.body:
            if isinstance(item, ast.Expr) and isinstance(item.value, ast.Str):
                continue
            cfg_visitor.visit(item)

        cfg_nodes = cfg_visitor.cfg_nodes
        if not cfg_nodes:
            return
        # concat args and function name
        func_node_name: str = f'def {node.name}'
        args_str: str = ''
        for each_arg in args:
            args_str += f'{each_arg}, '
        if len(args) > 0:
            args_str = args_str[:-2]
        # create cfg node
        entry_node = src.Model.CFGNode.FunctionNode(node.lineno + self.base_line, f'{func_node_name}({args_str})')

        # add variable info
        for each_arg in args:
            entry_node.defined_vars.add(each_arg)

        entry_node.add_child(cfg_nodes[0])
        entry_node.cfg_nodes += cfg_nodes
        self.function_def_node[f'{node.name}'] = entry_node
        self.function_doc_string[f'{node.name}'] = doc_string

    def visit_ClassDef(self, node):
        pass

    def visit_Try(self, node: ast.Try):
        # body
        cfg_visitor = CFGVisitor('')
        for item in node.body:
            cfg_visitor.visit(item)

        # exception
        for eachException in node.handlers:
            cfg_visitor = CFGVisitor('')
            for item in eachException.body:
                if isinstance(item, ast.Expr) and isinstance(item.value, ast.Str):
                    continue
                cfg_visitor.visit(item)
        # final
        cfg_visitor = CFGVisitor('')
        for item in node.finalbody:
            cfg_visitor.visit(item)




    def visit_Return(self, node):
        content = astor.to_source(node).strip()
        temp = src.Model.CFGNode.ReturnNode(node.lineno + self.base_line, content)
        if len(self.cfg_nodes) > 1:
            self.cfg_nodes[-1].add_child(temp)
        self.cfg_exit_nodes.append(temp)

    def visit_Assign(self, node):
        content = astor.to_source(node).strip()
        temp = src.Model.CFGNode.CFGNode(node.lineno + self.base_line, content)
        if len(self.cfg_nodes) > 1:
            self.cfg_nodes[-1].add_child(temp)
        self.cfg_nodes.append(temp)

    def visit_Expr(self, node):
        content = astor.to_source(node).strip()
        temp = src.Model.CFGNode.CFGNode(node.lineno + self.base_line, content)
        if len(self.cfg_nodes) > 1:
            self.cfg_nodes[-1].add_child(temp)
        self.cfg_nodes.append(temp)

    def visit_If(self, node):
        content = astor.to_source(node.test).strip()
        if_stmt = src.Model.CFGNode.IfNode(node.lineno + self.base_line, content.split('\n')[0])
        if len(self.cfg_nodes) > 0:
            self.cfg_nodes[-1].add_child(if_stmt)
        self.cfg_nodes.append(if_stmt)
        end_if = src.Model.CFGNode.EndIfNode(node.lineno + self.base_line)

        if_body = node.body
        else_body = node.orelse if node.orelse else []

        current = None
        for stmt in if_body:
            child = CFGVisitor(astor.to_source(stmt).strip(), stmt.lineno + self.base_line).build_cfg()
            if_stmt.add_child(child)
            if current is not None:
                current += child
            else:
                current = child
            # self.visit(stmt)

        if current is not None and len(current) > 0:
            if not isinstance(current[-1], src.Model.CFGNode.ReturnNode):
                current[-1].add_child(end_if)
            self.cfg_nodes += current

        if not if_stmt.children:
            if_stmt.add_child(end_if)

        # elif ?? @TODO
        if len(else_body) > 0:
            else_nodes = []
            for stmt in else_body:
                child = CFGVisitor(astor.to_source(stmt).strip(), stmt.lineno + self.base_line).build_cfg()
                else_nodes += child
                # self.visit(stmt)
            if len(else_nodes) > 0:
                else_nodes[-1].add_child(end_if)
                if_stmt.add_child(else_nodes[0])
                self.cfg_nodes += else_nodes
            else:
                if_stmt.add_child(end_if)
        else:
            if_stmt.add_child(end_if)

        self.cfg_nodes.append(end_if)

    def visit_While(self, node):
        content = astor.to_source(node.test).strip()
        end_while = src.Model.CFGNode.EndWhileNode(node.lineno + self.base_line)
        cfg_node = src.Model.CFGNode.WhileNode(node.lineno + self.base_line, content.split('\n')[0])
        cfg_node.add_child(end_while)
        if len(self.cfg_nodes) > 0:
            self.cfg_nodes[-1].add_child(cfg_node)

        # test_node = src.Model.CFGNode(node.test.lineno + self.base_line, astor.to_source(node.test).strip())
        # cfg_node.add_child(test_node)

        if hasattr(node, 'body'):
            current = []
            for stmt in node.body:
                child = CFGVisitor(astor.to_source(stmt).strip(), node.lineno + self.base_line).build_cfg()
                if len(current) > 0 and len(child) > 0:
                    current[-1].add_child(child[0])
                current += child

            if len(current) > 0:
                current[-1].add_child(end_while)
                cfg_node.add_child(current[0])
            else:
                cfg_node.add_child(end_while)

            self.cfg_nodes += current

        elif hasattr(node, 'orelse'):
            current = []
            for stmt in node.orelse:
                child = CFGVisitor(astor.to_source(stmt).strip(), stmt.lineno + self.base_line).build_cfg()
                current += child

            if len(current) > 0:
                current[-1].add_child(end_while)
                cfg_node.add_child(current[0])
            else:
                cfg_node.add_child(end_while)

            self.cfg_nodes += current

        self.cfg_nodes.append(cfg_node)
        self.cfg_nodes.append(end_while)

    def visit_For(self, node):
        content = astor.to_source(node).strip()
        cfg_node = src.Model.CFGNode.ForNode(node.lineno + self.base_line, content)
        end_for = src.Model.CFGNode.EndForNode(node.lineno + self.base_line)
        cfg_node.add_child(end_for)
        if len(self.cfg_nodes) > 0:
            self.cfg_nodes[-1].add_child(cfg_node)

        if hasattr(node, 'body'):
            current = []
            for stmt in node.body:
                child = CFGVisitor(astor.to_source(stmt).strip(), node.lineno + self.base_line).build_cfg()
                if len(current) > 0 and len(child) > 0:
                    current[-1].add_child(child[0])
                current += child

            if len(current) > 0:
                current[-1].add_child(end_for)
                cfg_node.add_child(current[0])
            else:
                cfg_node.add_child(end_for)

            self.cfg_nodes += current

        elif hasattr(node, 'orelse'):
            current = []
            for stmt in node.orelse:
                child = CFGVisitor(astor.to_source(stmt).strip(), stmt.lineno + self.base_line).build_cfg()
                current += child

            if len(current) > 0:
                current[-1].add_child(end_for)
                cfg_node.add_child(current[0])
            else:
                cfg_node.add_child(end_for)

            self.cfg_nodes += current

        self.cfg_nodes.append(cfg_node)
        self.cfg_nodes.append(end_for)

    def export_cfg_to_mermaid(self):
        ret = "graph TD;\n"

        node_instance = {}
        id_counter: int = 1

        # build nodes
        for each in self.cfg_nodes:
            if id(each) not in node_instance:
                node_instance[id(each)] = id_counter
                id_counter = id_counter + 1
                ret += f'{node_instance[id(each)]}{str(each)}'
            for child in each.children:
                if id(child) not in node_instance:
                    node_instance[id(child)] = id_counter
                    id_counter = id_counter + 1
                    ret += f'{node_instance[id(child)]}{str(child)}'

        # Add edges
        for each in self.cfg_nodes:
            node_id = id(each)
            for child in each.children:
                child_id = id(child)
                ret += f'{node_instance[node_id]}-->{node_instance[child_id]}\n'

        return ret

    @staticmethod
    def __build_mermaid_once(cfg_nodes: list, after_fix: int) -> str:
        ret = f'subgraph \"{after_fix}\";\n'

        node_instance = {}
        id_counter: int = 1

        # build nodes
        for each in cfg_nodes:
            if id(each) not in node_instance:
                node_instance[id(each)] = id_counter
                id_counter = id_counter + 1
                ret += f'{node_instance[id(each)]}{str(each)}'
            for child in each.children:
                if id(child) not in node_instance:
                    node_instance[id(child)] = id_counter
                    id_counter = id_counter + 1
                    ret += f'{node_instance[id(child)]}{str(child)}'

        # Add edges
        for each in cfg_nodes:
            node_id = id(each)
            for child in each.children:
                child_id = id(child)
                ret += f'{node_instance[node_id]}-->{node_instance[child_id]}\n'

        return ret