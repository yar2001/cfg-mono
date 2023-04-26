from enum import Enum
from typing import List, Dict

"""生成cfg过程中，用到的类的统一管理"""

class NodeKind(Enum):
    """给节点区分种类，分为Normal节点，Continue节点，Break节点，Return节点，GoTo节点"""
    Normal = 1;
    Continue = 2;
    Break = 3;
    Return = 4;
    GOTO = 5;
    Throw = 6;

class CFGNode:
    def __init__(self, id: str, text: str, kind: str):
        """参数的分别为id(clang解析出来的nodeHash值），text（该节点对应的文本内容），kind（对应的ast节点类型）"""
        self.id = id;
        self.text = text;
        self.kind = kind;

    def to_dict(self):
        return {"_id": str(self.id), "text": self.text};

class CFGEdge:

    def __init__(self, begin: str, end: str):
        """begin和end分别为CFGNode的id"""
        self.begin = str(begin);
        self.end = str(end);

    def to_dict(self):
        return {"begin": str(self.begin), "end": str(self.end)};

class SpecialAndLastNode:
    """该类为特殊节点和执行到当前语句为止的最后节点的统一管理类，特殊节点为return
    、continue这些节点"""

    def __init__(self, id:str, nodeType: NodeKind, name: str = None):
        """id为CFGNode的id值， nodeType是给ast节点的类型划分， name是为了应付goto语句这些，goto到
        一个有名字的Label，所以引入此概念"""

        self.id = str(id);
        self.nodeType = nodeType;
        self.name = name;

    def to_dict(self):
        return {"_id": str(self.id), "nodeType": str(self.nodeType), "name": self.name};

class CFGData:
    """生成的CFG数据管理类"""
    def __init__(self, nodes: List[CFGNode], edges: List[CFGEdge], specialAndLastNodes: List[SpecialAndLastNode]):
        self.nodes = nodes;
        self.edges = edges;
        self.specialAndLastNodes = specialAndLastNodes;

    def appendCFGNode(self, node: CFGNode):
        self.nodes.append(node);

    def appendCFGEdge(self, edge: CFGEdge):
        self.edges.append(edge);

    def appendSpecialAndLastNode(self, specialAndLastNode: SpecialAndLastNode):
        self.specialAndLastNodes.append(specialAndLastNode);

    def cleanSpecialAndLastNodes(self):
        """清除speialAndSpecialAndLastNodes中的Normal类型节点"""
        specialAndLastNodes = self.specialAndLastNodes;
        i:int = 0;

        # 遍历特殊和最后一个节点列表，并将其中的Normal类型节点删除
        while i < len(specialAndLastNodes):
            if (NodeKind.Normal == specialAndLastNodes[i].nodeType):
                del specialAndLastNodes[i];
            else:
                i = i + 1;

    def getCFGNode(self) -> List[CFGNode]:
        return self.nodes;

    def getCFGEdges(self) -> List[CFGEdge]:
        return self.edges;

    def getSpecialAndLastNodes(self) -> List[SpecialAndLastNode]:
        return self.specialAndLastNodes;

    def to_dict(self)-> Dict[str, List]:
        return {
            'nodes': [node.to_dict() for node in self.nodes],
            'edges': [edge.to_dict() for edge in self.edges],
            'specialAndLastNodes': [node.to_dict() for node in self.specialAndLastNodes]
        }


class CFGBlock(CFGNode):
    """一个函数看作一个CFGBlock"""
    def __init__(self, id: str, text: str, kind: str, children: CFGData):
        super().__init__(id, text, kind);
        self.children = children;

    def to_dict(self):
        return {"_id": self.id, "text": self.text, "children": self.children.to_dict()};
