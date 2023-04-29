import ast
import astor


class CFGNode:
    def __init__(self, line, content):
        self.line = line
        self.content = content.strip()
        self.children = []
        self.function_calls = []
        self.used_vars = set()
        self.defined_vars = set()
        self._extract_vars()
        self._extract_function_calls()

    def add_function_call(self, func) -> None:
        if func not in self.function_calls:
            self.function_calls.append(func)

    def clear_children(self):
        self.children.clear()

    def _extract_vars(self):
        try:
            stmt = ast.parse(self.content).body[0]
        except SyntaxError:
            return

        if isinstance(stmt, ast.Assign):
            self.defined_vars = set(t.id for t in stmt.targets if isinstance(t, ast.Name))
            self.used_vars = set(t.id for t in ast.walk(stmt.value) if isinstance(t, ast.Name))

        elif isinstance(stmt, ast.Expr) or isinstance(stmt, ast.If) or isinstance(stmt, ast.While):
            if isinstance(stmt, ast.BinOp):
                self.used_vars = set(t.id for t in ast.walk(stmt.left) if isinstance(t, ast.Name))
                self.used_vars |= set(t.id for t in ast.walk(stmt.right) if isinstance(t, ast.Name))
            else:
                if hasattr(stmt, 'test'):
                    self.used_vars = set(t.id for t in ast.walk(stmt.test) if isinstance(t, ast.Name))
                elif hasattr(stmt, 'value'):
                    for t in ast.walk(stmt.value):
                        if isinstance(t, ast.Name) and not isinstance(t.ctx, ast.Store):
                            self.used_vars.add(t.id)

            if isinstance(stmt, ast.If) or isinstance(stmt, ast.While):
                for n in ast.walk(stmt):
                    if isinstance(n, ast.Assign):
                        self.defined_vars |= set(t.id for t in n.targets if isinstance(t, ast.Name))
                        self.used_vars |= set(t.id for t in ast.walk(n.value) if isinstance(t, ast.Name))
                    elif isinstance(n, ast.Expr):
                        self.used_vars |= set(t.id for t in ast.walk(n.value) if isinstance(t, ast.Name))

    def _extract_function_calls(self):
        try:
            stmt = ast.parse(self.content).body[0]
        except SyntaxError:
            return

        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            func_name = astor.to_source(stmt.value.func).strip()
            if func_name in self.used_vars:
                self.used_vars.remove(func_name)
            args = []
            for arg in stmt.value.args:
                if isinstance(arg, ast.Name):
                    args.append(arg.id)
                # else:
            self.add_function_call(func_name)
            for each_arg in args:
                if each_arg not in self.used_vars:
                    self.used_vars.add(each_arg)

    def add_child(self, child):
        if type(child) is list:
            self.children += child
        else:
            self.children.append(child)

    def __repr__(self):
        return f'Node(line={self.line}, content="{self.content}", used_vars={sorted(self.used_vars)}, ' \
               f'defined_vars={sorted(self.defined_vars)}, function_calls={self.function_calls})'

    def __str__(self) -> str:
        content = self.content.replace('\n', '\\n')
        return f'["{content}\n(line: {self.line})"]\n'


class EndNode(CFGNode):

    def __str__(self) -> str:
        return f'["{self.content}"]\n'


class WhileNode(CFGNode):
    def __init__(self, line, content):
        super().__init__(line, content)
        self.content = 'while ' + self.content


class EndWhileNode(EndNode):

    def __init__(self, line, content=None):
        content = 'end-while'
        super().__init__(line, content)


class IfNode(CFGNode):

    def __init__(self, line, content):
        super().__init__(line, content)
        self.content = 'if ' + self.content


class EndIfNode(EndNode):

    def __init__(self, line, content=None):
        content = 'end-if'
        super().__init__(line, content)

class JumpNode(CFGNode):

    def __init__(self, line, content=None):
        super().__init__(line, content)

class ContinueNode(JumpNode):

    def __init__(self, line, content=None):
        content = 'continue'
        super().__init__(line, content)

class BreakNode(JumpNode):

    def __init__(self, line, content=None):
        content = 'break'
        super().__init__(line, content)

class FunctionNode(CFGNode):

    def __init__(self, line, content):
        super().__init__(line, content)
        self.cfg_nodes = []

class ForNode(CFGNode):
    def __init__(self, line, content):
        super().__init__(line, content)
        self.content = self.content.split('\n')[0]

    def _extract_vars(self):
        try:
            stmt = ast.parse(self.content).body[0]
        except SyntaxError:
            return

        if not isinstance(stmt, ast.For):
            return

        # Get the target variables of the for loop, which may be a single variable,
        # a tuple of variables, or a starred expression
        targets = []
        if isinstance(stmt.target, ast.Name):
            # If target is a single variable, get its name directly
            targets.append(stmt.target.id)
        elif isinstance(stmt.target, ast.Tuple):
            # If target is a tuple, get the names of all variables in it
            for elt in ast.walk(stmt.target):
                if isinstance(elt, ast.Name):
                    targets.append(elt.id)

        elif isinstance(stmt.target, ast.Starred):
            # If target is a starred expression, get the name of the variable it represents
            targets.append(stmt.target.value.id)
        # merge it
        for each in targets:
            self.defined_vars.add(each)


    def _extract_function_calls(self):
        try:
            stmt = ast.parse(self.content).body[0]
        except SyntaxError:
            return

        if not isinstance(stmt, ast.For):
            return
        # Get the iter part of the for loop, which may be a function call or a variable
        iter_node = stmt.iter
        if isinstance(iter_node, ast.Call):
            # If iter is a function call, get the function name, object name (if any), and arguments
            func_node = iter_node.func
            # if hasattr(func_node, 'attr') and hasattr(func_node, 'value'):
            #     func_name = func_node.attr
            #     obj_node = func_node.value
            #     obj_name = obj_node.id

            if hasattr(func_node, 'id'):
                func_name = func_node.id
                self.add_function_call(func_name)

            # collect args
            for each in iter_node.args:
                if isinstance(each, ast.Name):
                    self.used_vars.add(each)

        elif isinstance(iter_node, ast.Name):
            # If iter is a variable, get its name and save it
            self.used_vars.add(iter_node.id)


class EndForNode(EndNode):

    def __init__(self, line, content=None):
        content = 'end-for'
        super().__init__(line, content)


class ReturnNode(CFGNode):

    def __init__(self, line, content=None):
        super().__init__(line, content)

    def _extract_vars(self):
        try:
            stmt = ast.parse(self.content).body[0]
        except SyntaxError:
            return

        if not isinstance(stmt, ast.Return) or stmt.value is None:
            return

        for node in ast.walk(stmt.value):
            if isinstance(node, ast.Name):
                self.used_vars.add(node.id)
            # var function depends
            if isinstance(node, ast.Call):
                for each_arg in node.args:
                    if isinstance(each_arg, ast.Name):
                        self.used_vars.add(each_arg.id)

    def _extract_function_calls(self):
        try:
            stmt = ast.parse(self.content).body[0]
        except SyntaxError:
            return

        if not isinstance(stmt, ast.Return) or stmt.value is None:
            return

        for node in ast.walk(stmt.value):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    self.add_function_call(func.id)
