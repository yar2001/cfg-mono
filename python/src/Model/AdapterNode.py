import src.Model.CFGNode
import src.Model.DDGNode
import json

class DataEdge:
    def __init__(self, id: int, source: int, target: int):
        self.id = id
        self.source = source
        self.target = target

    def __str__(self) -> str:
        data: dict = {
            'id': self.id,
            'source': self.source,
            'target': self.target
        }

        return json.dumps(data)

class DataNode:

    def __init__(self, node, id: int):
        self.id: int = id
        self.line: int = node.line
        self.lable: str = node.content

    def __str__(self) -> str:
        data: dict = {
            'id': self.id,
            'Line': self.line,
            'label': self.lable
        }

        return json.dumps(data)

class CFGDataNode(DataNode):
    def __init__(self, cfg_node: src.Model.CFGNode, id: int):
        super().__init__(cfg_node, id)

class CFGDataEdge(DataEdge):

    def __init__(self, id: int, source: int, target: int):
        super().__init__(id, source, target)


class DDGDataNode(DataNode):

    def __init__(self, ddg_node: src.Model.DDGNode.DDGNode, id: int):
        super().__init__(ddg_node, id)


class DDGDataEdge(DataEdge):

    def __init__(self, id: int, source: int, target: int):
        super().__init__(id, source, target)