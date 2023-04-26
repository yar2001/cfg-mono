import sys
from pathlib import Path
sys.path.append(fr"{Path(__file__).resolve().parent.parent}");

import clang.cindex
from clang.cindex import *
import copy
from nameClass import *
import re

file_name = "code.cpp"
# -*- coding: utf-8 -*-
"""解析CFG节点，生成CFG的相关函数"""
def getStatements(tu_cursor: clang.cindex.Cursor):
    """获取当前节点迭代器里的所有children"""
    tu_child = tu_cursor.get_children();
    statements = [c for c in tu_child];
    return statements;

def getContent(node_cur: clang.cindex.Cursor):
    """获取当前stmt节点对应的代码语句"""
    cursor_content :str = "";
    for token in node_cur.get_tokens():
        # 针对一个节点，调用get_tokens的方法。
        cursor_content = f"{cursor_content}{token.spelling} ";
    return cursor_content;

def testChildren(node: clang.cindex.Cursor):
    """输出当前节点所有子节点的相关信息"""
    print("start---------------------------------------")
    children_statements = getStatements(node);
    for node in children_statements:
        nodeId = node.hash;
        kind = node.kind;
        spelling = node.spelling;
        print("hash:", node.hash);
        print("kind:", node.kind);
        print("content", getContent(node));
        print("spelling:", node.spelling);
        print("fileName:", node.location.file.name);
    print("end--------------------------------------");

class DisposeCFGController:
    def __init__(self):
        return;

    def disposeIF_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        """处理IFSTMT节点的函数"""
        # 获取孩子节点
        children_statements = getStatements(node);

        testChildren(node);
        length = len(children_statements);

        condition = children_statements[0];

        # 处理condition
        cfgData.appendCFGNode(CFGNode(str(condition.hash), "if:(" + getContent(condition) + ")", condition.kind));
        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();

        for specialAndLastNode in specialAndLastNodes:
            if (specialAndLastNode.nodeType == NodeKind.Normal):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, condition.hash));

        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(condition.hash, NodeKind.Normal));

        # 处理true分支
        trueStmt = [];
        trueStmt.append(children_statements[1]);
        trueStmt_children = self.generateCFG(trueStmt);

        # 该compound_stmt第一个节点的nodeId
        trueStmt_firstNodeId = trueStmt_children.nodes[0].id;

        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();

        for specialAndLastNode in specialAndLastNodes:
            if (NodeKind.Normal == specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, trueStmt_firstNodeId));

        for child_node in trueStmt_children.nodes:
            cfgData.appendCFGNode(child_node);

        for child_edge in trueStmt_children.edges:
            cfgData.appendCFGEdge(child_edge);

        if (length >= 3):
            # 处理false分支
            falseStmt = [];
            falseStmt.append(children_statements[2]);
            falseStmt_children = self.generateCFG(falseStmt);

            # 该compound_stmt第一个节点的nodeId
            falseStmt_firstNodeId = falseStmt_children.nodes[0].id;

            for specialAndLastNode in specialAndLastNodes:
                if (NodeKind.Normal == specialAndLastNode.nodeType):
                    cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, falseStmt_firstNodeId));

            for child_node in falseStmt_children.nodes:
                cfgData.appendCFGNode(child_node);

            for child_edge in falseStmt_children.edges:
                cfgData.appendCFGEdge(child_edge);

            # 推入false分支的SpecialAndLastNodes节点
            for child_specialAndLastNode in falseStmt_children.specialAndLastNodes:
                cfgData.appendSpecialAndLastNode(child_specialAndLastNode);

        # 推入true分支的SpecialAndLastNodes节点
        for child_specialAndLastNode in trueStmt_children.specialAndLastNodes:
            cfgData.appendSpecialAndLastNode(child_specialAndLastNode);

        # if-end
        cfgData.appendCFGNode(CFGNode(str(condition.hash) + "end", "if-end", "if-end"));

        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();

        for specialAndLastNode in specialAndLastNodes:
            if (NodeKind.Normal == specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, str(condition.hash) + "end"));

        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(str(condition.hash) + "end", NodeKind.Normal));

    def disposeRETURN_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        """处理RETURN_STMT节点的函数"""
        nodeId = node.hash;
        source_text = getContent(node);
        print("source_text:", source_text);

        cfgData.appendCFGNode(CFGNode(nodeId, source_text, node.kind));

        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        for specialAndLastNode in specialAndLastNodes:
            if (specialAndLastNode.nodeType == NodeKind.Normal):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));

        # cfgData.appendCFGSpecialAndLastNode(SpecialAndLastNode(node.hash, NodeKind.Return));
        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(node.hash, NodeKind.Return));

    def disposeCOMPOUND_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        """处理COMPOUND_STMT节点的函数"""
        statements = getStatements(node);
        testChildren(node);

        children = self.generateCFG(statements);

        # 该compound_stmt第一个节点的nodeId
        if(len(children.nodes) <= 0):
            return;

        firstNodeId = children.nodes[0].id;

        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();

        for specialAndLastNode in specialAndLastNodes:
            if (specialAndLastNode.nodeType == NodeKind.Normal):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, firstNodeId));

        for child_node in children.nodes:
            cfgData.appendCFGNode(child_node);

        for child_edge in children.edges:
            cfgData.appendCFGEdge(child_edge);

        for specialAndLastNode in children.specialAndLastNodes:
            cfgData.appendSpecialAndLastNode(specialAndLastNode);

    def disposeFUNCTION_DECL(self, node: clang.cindex.Cursor, cfgData: CFGData):
        """处理FUNCTION_DECL节点的函数"""

        if (CursorKind.FUNCTION_DECL == node.kind and node.location.file.name == file_name):

            children_statements = getStatements(node);
            specialAndLastNodes = cfgData.getSpecialAndLastNodes();

            if (len(children_statements) != 0):
                if (CursorKind.COMPOUND_STMT == children_statements[-1].kind):
                    testChildren(children_statements[-1]);
                    # disposeCOMPOUND_STMT(children_statements[-1]);
                    # 这个暂时作过度用，获取compound_stmt的children节点
                    temp_statements = getStatements(children_statements[-1]);
                    children = self.generateCFG(temp_statements);

                    if (len(children.nodes) > 0):
                        children.edges.append(CFGEdge("[*]", children.nodes[0].id));

                        for specialAndLastNode in children.specialAndLastNodes:
                            if(specialAndLastNode.nodeType == NodeKind.GOTO or (specialAndLastNode.nodeType == NodeKind.Throw and specialAndLastNode.name == None)):
                                continue;

                            children.edges.append(CFGEdge(specialAndLastNode.id, "[*]"));

                    block = CFGBlock(node.hash, node.spelling, node.kind, children);
                    cfgData.appendCFGNode(block);

                    for specialAndLastNode in specialAndLastNodes:
                        cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));

                    cfgData.cleanSpecialAndLastNodes();
                    cfgData.appendSpecialAndLastNode(SpecialAndLastNode(node.hash, NodeKind.Normal));

    def disposeOther_Node(self, node: clang.cindex.Cursor, cfgData: CFGData):
        """处理非特殊AST节点的函数"""

        nodeId = node.hash;
        source_text = getContent(node);
        print("source_text:", source_text);

        cfgData.appendCFGNode(CFGNode(nodeId, source_text, node.kind));

        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        for specialAndLastNode in specialAndLastNodes:
            if (specialAndLastNode.nodeType == NodeKind.Normal):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));

        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(node.hash, NodeKind.Normal));

    def getFOR_STMT_STRUCT(self, node: clang.cindex.Cursor) -> []:
        # 获取for循环的结构(因为有for(;;i++)这种的情况
        # 判断是否存在
        struct_judge = [False, False, False];
        index = 0;
        tokens = node.get_tokens();
        it = node.get_tokens();
        it_iterator = iter(it);
        next(it_iterator);
        for i in tokens:
            try:
                nextToken = next(it_iterator);
            except StopIteration:
                pass;
            if (index == 0):
                if (str(i.spelling) == '('):
                    if (str(nextToken.spelling) != ';'):
                        struct_judge[index] = True;
                        index += 1;
                    else:
                        index += 1;
            if (index == 1 or index == 2):
                if (str(i.spelling) == ';'):
                    if (str(nextToken.spelling) != ';' and str(nextToken.spelling) != ')'):
                        struct_judge[index] = True;
                        index += 1;
                    else:
                        index += 1;
            if (str(i.spelling) == '{'):
                break;

        return struct_judge;

    def disposeFOR_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        """处理FOR_STMT节点的函数"""
        testChildren(node);
        statements = getStatements(node);
        testChildren(statements[-1]);
        length = len(statements);

        initializer = None;
        condition = None;
        incrementor = None;

        struct_judge = self.getFOR_STMT_STRUCT(node);

        # 获取initializer
        if (struct_judge[0] == True):
            initializer = statements[0];

        # 获取condition
        if (struct_judge[1] == True):
            if (struct_judge[0] == True):
                condition = statements[1];
            else:
                condition = statements[0];

        # 获取increamentor
        if (struct_judge[2] == True):
            if (struct_judge[1] == True and struct_judge[0] == True):
                incrementor = statements[2];
            elif ((struct_judge[0] == False and struct_judge[1] == True) or
                  (struct_judge[0] == True and struct_judge[1] == False)):
                incrementor = statements[1];
            elif (struct_judge[0] == False and struct_judge[1] == False):
                incrementor = statements[0];

        # 获取body
        compound_statements = statements[-1];

        # 推入for-begin
        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        cfgData.appendCFGNode(CFGNode(node.hash, 'for-begin', node.kind));
        for specialAndLastNode in specialAndLastNodes:
            if (NodeKind.Normal == specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));
        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(node.hash, NodeKind.Normal));

        # 推入initializer
        if (initializer is not None):
            specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
            cfgData.cleanSpecialAndLastNodes();
            spelling = getContent(initializer);
            cfgData.appendCFGNode(
                CFGNode(initializer.hash, 'for initializer:' + getContent(initializer), initializer.kind));
            for specialAndLastNode in specialAndLastNodes:
                if (NodeKind.Normal == specialAndLastNode.nodeType):
                    cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, initializer.hash));
            cfgData.appendSpecialAndLastNode(SpecialAndLastNode(initializer.hash, NodeKind.Normal));

        # 推入condition
        if (condition is not None):
            specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
            cfgData.cleanSpecialAndLastNodes();
            cfgData.appendCFGNode(CFGNode(condition.hash, 'for condition:' + getContent(condition), condition.kind));
            for specialAndLastNode in specialAndLastNodes:
                if (NodeKind.Normal == specialAndLastNode.nodeType):
                    cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, condition.hash));
            cfgData.appendSpecialAndLastNode(SpecialAndLastNode(condition.hash, NodeKind.Normal));

        self.disposeLoop(compound_statements, cfgData, incrementor);

        # 推入incrementor
        if (incrementor is not None):
            cfgData.appendCFGNode(
                CFGNode(incrementor.hash, 'for incrementor:' + getContent(incrementor), incrementor.kind));

        # increamentor到condition的边
        cfgData.appendCFGEdge(CFGEdge(incrementor.hash, condition.hash));

        # 推入condition到last_nodes
        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(condition.hash, NodeKind.Normal));

        # for-end
        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        cfgData.appendCFGNode(CFGNode(f"{node.hash}end", "for-end", "FOR_END"));

        for specialAndLastNode in specialAndLastNodes:
            if(specialAndLastNode.nodeType == NodeKind.Normal):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, f"{node.hash}end"));

        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(f"{node.hash}end", NodeKind.Normal));

    def disposeBREAK_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        """处理BREAK_STMT节点的函数"""
        nodeId = node.hash;
        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        for specialAndLastNode in specialAndLastNodes:
            if (specialAndLastNode.nodeType == NodeKind.Normal):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));

        cfgData.cleanSpecialAndLastNodes();
        cfgData.appendCFGNode(CFGNode(nodeId, 'BREAK', node.kind));
        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(nodeId, NodeKind.Break));

    def disposeCONTINUE_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        """处理CONTINUE_STMT节点的函数"""
        nodeId = node.hash;
        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        for specialAndLastNode in specialAndLastNodes:
            if (specialAndLastNode.nodeType == NodeKind.Normal):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));

        cfgData.appendCFGNode(CFGNode(nodeId, 'CONTINUE', node.kind));
        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(nodeId, NodeKind.Continue));

    def disposeLoop(self, node: clang.cindex.Cursor, cfgData: CFGData, nextDoNode: clang.cindex.Cursor):
        """处理所有跟循环有关的body"""
        statements = [];
        statements.append(node);
        children = self.generateCFG(statements);

        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();

        if (len(children.nodes) > 0):
            for specialAndLastNode in specialAndLastNodes:
                if (NodeKind.Normal == specialAndLastNode.nodeType):
                    cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, children.nodes[0].id));

            for node in children.nodes:
                cfgData.appendCFGNode(node);

            for edge in children.edges:
                cfgData.appendCFGEdge(edge);

            for specialAndLastNode in children.specialAndLastNodes:
                if (NodeKind.Break == specialAndLastNode.nodeType):
                    continue;

                if (NodeKind.Return == specialAndLastNode.nodeType):
                    continue;

                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, nextDoNode.hash));

            for specialAndLastNode in children.specialAndLastNodes:
                if (NodeKind.Break == specialAndLastNode.nodeType):
                    cfgData.appendSpecialAndLastNode(SpecialAndLastNode(specialAndLastNode.id, NodeKind.Normal));
                elif (NodeKind.Return == specialAndLastNode.nodeType):
                    cfgData.appendSpecialAndLastNode(SpecialAndLastNode(specialAndLastNode.id, NodeKind.Return));
                # elif(NodeKind.Break != specialAndLastNode.nodeType and NodeKind.Continue != specialAndLastNode.nodeType and NodeKind.Normal != specialAndLastNode.nodeType):
                #     cfgData.appendSpecialAndLastNode(specialAndLastNode);

    def disposeWHILE_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        testChildren(node);
        statements = getStatements(node);

        # 获取条件
        condition = statements[0];

        # 获取body
        compound_body = statements[-1];

        # condition
        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        for specialAndLastNode in specialAndLastNodes:
            if (NodeKind.Normal == specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, condition.hash));

        cfgData.appendCFGNode(CFGNode(condition.hash, 'while(' + getContent(condition) + ')', condition.kind));
        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(condition.hash, NodeKind.Normal));

        # 处理循环
        self.disposeLoop(compound_body, cfgData, condition);

        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(condition.hash, NodeKind.Normal));

        # while-end
        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        for specialAndLastNode in specialAndLastNodes:
            if (NodeKind.Normal == specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(str(specialAndLastNode.id), str(node.hash) + "end"));
        cfgData.appendCFGNode(CFGNode(str(node.hash) + "end", "while-end", "while-end"));

        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(str(node.hash) + "end", NodeKind.Normal));

    def disposeDO_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        """处理do_while节点的函数"""
        statements = getStatements(node);

        condition = statements[-1];
        compound_body = statements[0];

        # do
        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        for specialAndLastNode in specialAndLastNodes:
            if (NodeKind.Normal == specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));
        cfgData.appendCFGNode(CFGNode(node.hash, 'do', node.kind));
        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(node.hash, NodeKind.Normal));

        # 处理condition
        cfgData.appendCFGNode(CFGNode(condition.hash, 'while(' + getContent(condition) + ')', condition.kind));
        cfgData.appendCFGEdge(CFGEdge(condition.hash, node.hash));

        # 处理body
        self.disposeLoop(compound_body, cfgData, condition);

        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(condition.hash, NodeKind.Normal));

        # do-end
        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        for specialAndLastNode in specialAndLastNodes:
            if (NodeKind.Normal == specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(str(specialAndLastNode.id), str(node.hash) + "end"));
        cfgData.appendCFGNode(CFGNode(str(node.hash) + "end", "do-end", "do-end"));

        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(str(node.hash) + "end", NodeKind.Normal));

    def disposeCXX_FOR_RANGE_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        statements = getStatements(node);

        # for(x:y)
        cfgData.appendCFGNode(
            CFGNode(node.hash, f"{getContent(statements[0])} {getContent(statements[1])}", node.kind));

        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        for specialAndLastNode in specialAndLastNodes:
            if (NodeKind.Normal == specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));

        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(node.hash, NodeKind.Normal));
        self.disposeLoop(statements[-1], cfgData, node);

        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(node.hash, NodeKind.Normal));

    def disposeCASE_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        testChildren(node);

        statements = getStatements(node);
        real_statements = [];

        for i in range(len(statements)):
            if i != 0:
                real_statements.append(statements[i]);

        testChildren(node);
        children = self.generateCFG(real_statements);

        # 处理并标记成case：xx
        cfgData.appendCFGNode(CFGNode(node.hash, f"case {getContent(statements[0])}", node.kind));

        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        for specialAndLastNode in specialAndLastNodes:
            if (NodeKind.Normal == specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));

        cfgData.appendCFGEdge(CFGEdge(node.hash, children.nodes[0].id));

        for children_node in children.nodes:
            cfgData.appendCFGNode(children_node);

        for children_edge in children.edges:
            cfgData.appendCFGEdge(children_edge);

        # # 推入case_end
        # cfgData.appendCFGNode(CFGNode(f"{firstNode.hash}end", f"case {getContent(firstNode)} -end", "case-end"));

        for children_specialAndLastNode in children.specialAndLastNodes:
            # if(NodeKind.Break == children_specialAndLastNode.nodeType or NodeKind.Normal == children_specialAndLastNode.nodeType):
            #     cfgData.appendCFGEdge(CFGEdge(f"{children_specialAndLastNode.id}", f"{firstNode.hash}end"));
            #     continue;
            cfgData.appendSpecialAndLastNode(children_specialAndLastNode);

        # cfgData.appendSpecialAndLastNode(SpecialAndLastNode(f"{firstNode.hash}end", NodeKind.Normal));

        print(32);

    def disposeDEFAULT_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        testChildren(node);

        statements = getStatements(node);
        children = self.generateCFG(statements);

        # 处理并标记成default-begin

        cfgData.appendCFGNode(CFGNode(node.hash, "default", node.kind));

        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        for specialAndLastNode in specialAndLastNodes:
            if (NodeKind.Normal == specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));

        # 与返回来的children nodes首节点链接
        cfgData.appendCFGEdge(CFGEdge(node.hash, children.nodes[0].id));

        for children_node in children.nodes:
            cfgData.appendCFGNode(children_node);

        for children_edge in children.edges:
            cfgData.appendCFGEdge(children_edge);

        # 推入default_end
        cfgData.appendCFGNode(CFGNode(f"{node.hash}end", f"default-end", "default-end"));

        for children_specialAndLastNode in children.specialAndLastNodes:
            if (
                    NodeKind.Break == children_specialAndLastNode.nodeType or NodeKind.Normal == children_specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(f"{children_specialAndLastNode.id}", f"{node.hash}end"));
                continue;
            cfgData.appendSpecialAndLastNode(children_specialAndLastNode);

        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(f"{node.hash}end", NodeKind.Normal));

    def disposeSWITCH_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        statements = getStatements(node);
        testChildren(node);
        # switch-begin
        cfgData.appendCFGNode(CFGNode(node.hash, f"switch ( {getContent(statements[0])} )", node.kind));
        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        for specialAndLastNode in specialAndLastNodes:
            if (NodeKind.Normal == specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));

        # switch的body
        switch_body = [];
        switch_body.append(statements[-1]);
        children = self.generateCFG(switch_body);

        for children_node in children.nodes:
            if (CursorKind.CASE_STMT == children_node.kind or CursorKind.DEFAULT_STMT == children_node.kind):
                cfgData.appendCFGEdge(CFGEdge(node.hash, children_node.id));
            cfgData.appendCFGNode(children_node);

        for children_edge in children.edges:
            cfgData.appendCFGEdge(children_edge);

        for specialAndLastNode in children.specialAndLastNodes:
            if (NodeKind.Continue == specialAndLastNode.nodeType or NodeKind.Return == specialAndLastNode.nodeType):
                cfgData.appendSpecialAndLastNode(specialAndLastNode);
                continue;

            cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, f"{node.hash}end"));

        # 推入switch-end
        cfgData.appendCFGNode(CFGNode(f"{node.hash}end", "switch-end", "switch-end"));
        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(f"{node.hash}end", NodeKind.Normal));

    def disposeCXX_TRY_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        testChildren(node);
        statements = getStatements(node);
        # try-begin
        cfgData.appendCFGNode(CFGNode(f"{node.hash}", "try-begin", "try-begin"));

        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();

        for specialAndLastNode in specialAndLastNodes:
            if (NodeKind.Normal == specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));

        cfgData.appendSpecialAndLastNode(SpecialAndLastNode(f"{node.hash}", NodeKind.Normal));


        # 包含throw的statements
        throw_statements = [statements[0]];
        throw_cfgData = self.generateCFG(throw_statements);

        if(len(throw_cfgData.nodes) > 0):
            specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
            cfgData.cleanSpecialAndLastNodes();

            for specialAndLastNode in specialAndLastNodes:
                if(specialAndLastNode.nodeType == NodeKind.Normal):
                    cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, throw_cfgData.nodes[0].id));

            for child_node in throw_cfgData.nodes:
                cfgData.appendCFGNode(child_node);

            for child_edge in throw_cfgData.edges:
                cfgData.appendCFGEdge(child_edge);

            for child_specialAndLastNode in throw_cfgData.specialAndLastNodes:
                cfgData.appendSpecialAndLastNode(child_specialAndLastNode);

        # # try-end
        # cfgData.appendCFGNode(CFGNode(f"{node.hash}end", "try-end", "try-end"));
        #
        # specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        # cfgData.cleanSpecialAndLastNodes();
        #
        # for specialAndLastNode in specialAndLastNodes:
        #     if(NodeKind.Normal == specialAndLastNode.nodeType):
        #         cfgData.appendCFGEdge(CFGEdge(f"{node.hash}end", specialAndLastNode.id));
        #
        # cfgData.appendSpecialAndLastNode(SpecialAndLastNode(f"{node.hash}end", NodeKind.Normal));

        for i in range(len(statements)):
            if(0 == i):
                continue;
            self.disposeCXX_CATCH_STMT(statements[i], cfgData);





    def disposeCXX_CATCH_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        testChildren(node);

        statements = getStatements(node);
        catch_name = get_exception_name(getContent(statements[0]));

        specialAndLastNodes = cfgData.getSpecialAndLastNodes();
        for specialAndLastNode in specialAndLastNodes:
            if(specialAndLastNode.nodeType == NodeKind.Throw and specialAndLastNode.name == catch_name):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));
                specialAndLastNode.name = None;
                break;

        cfgData.appendCFGNode(CFGNode(node.hash, f"catch {catch_name}", node.kind));

        # catch分为catch住的错误和body
        catch_bodyStatements = [statements[1]];
        catch_body_cfgData = self.generateCFG(catch_bodyStatements);

        if(0 < len(catch_body_cfgData.nodes)):
            cfgData.appendCFGEdge(CFGEdge(node.hash, catch_body_cfgData.nodes[0].id));

            for child_node in catch_body_cfgData.nodes:
                cfgData.appendCFGNode(child_node);

            for child_edge in catch_body_cfgData.edges:
                cfgData.appendCFGEdge(child_edge);

            # catch-end
            cfgData.appendCFGNode(CFGNode(f"{node.hash}end", "catch-end", "catch-end"));

            for specialAndLastNode in catch_body_cfgData.specialAndLastNodes:
                if(specialAndLastNode.nodeType == NodeKind.Normal):
                    cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, f"{node.hash}end"));
                    continue;

                cfgData.appendSpecialAndLastNode(specialAndLastNode);

            cfgData.appendSpecialAndLastNode(SpecialAndLastNode(f"{node.hash}end", NodeKind.Normal));





    def disposeLABEL_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):

        cfgData.appendCFGNode(CFGNode(node.hash, f"Label: {node.spelling}", node.kind));

        specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
        cfgData.cleanSpecialAndLastNodes();
        for specialAndLastNode in specialAndLastNodes:
            spelling = node.spelling;
            name = specialAndLastNode.name;
            if (NodeKind.Normal == specialAndLastNode.nodeType):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));
                continue;
            if (NodeKind.GOTO == specialAndLastNode.nodeType and str(node.spelling) == str(specialAndLastNode.name)):
                cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));
                specialAndLastNode.name = None;
                continue;

        # 处理这个label的body
        statements = getStatements(node);
        children = self.generateCFG(statements);

        if (len(children.nodes) > 0):
            cfgData.appendCFGEdge(CFGEdge(node.hash, children.nodes[0].id));

        for children_node in children.nodes:
            cfgData.appendCFGNode(children_node);

        for children_edge in children.edges:
            cfgData.appendCFGEdge(children_edge);

        for specialAndLastNode in children.specialAndLastNodes:
            cfgData.appendSpecialAndLastNode(specialAndLastNode);

    def disposeGOTO_STMT(self, node: clang.cindex.Cursor, cfgData: CFGData):
        statements = getStatements(node);

        if (len(statements) > 0):
            if (CursorKind.LABEL_REF == statements[0].kind):
                cfgData.appendCFGNode(CFGNode(statements[0].hash, f"goto {getContent(statements[0])}", node.kind));

                specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
                cfgData.cleanSpecialAndLastNodes();
                for specialAndLastNode in specialAndLastNodes:
                    if (NodeKind.Normal == specialAndLastNode.nodeType):
                        cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, statements[0].hash));

                goto_name = getContent(statements[0]).replace(" ", "");
                cfgData.appendSpecialAndLastNode(SpecialAndLastNode(statements[0].hash, NodeKind.GOTO, goto_name));

    def disposeUNEXPOSED_EXPR(self, node: clang.cindex.Cursor, cfgData: CFGData):
        variable_name = analyzeIsOrThrow(getContent(node));
        if(None == variable_name):
            self.disposeOther_Node(node, cfgData);
            return;
        else:
            cfgData.appendCFGNode(CFGNode(node.hash, getContent(node), node.kind));

            specialAndLastNodes = copy.deepcopy(cfgData.getSpecialAndLastNodes());
            cfgData.cleanSpecialAndLastNodes();
            for specialAndLastNode in specialAndLastNodes:
                if (specialAndLastNode.nodeType == NodeKind.Normal):
                    cfgData.appendCFGEdge(CFGEdge(specialAndLastNode.id, node.hash));

            cfgData.appendSpecialAndLastNode(SpecialAndLastNode(node.hash, NodeKind.Throw, variable_name));
            return;



    def visit(self, node: clang.cindex.Cursor, cfgData: CFGData):

        if (CursorKind.IF_STMT == node.kind):
            self.disposeIF_STMT(node, cfgData);
            return;

        # if(CursorKind.BINARY_OPERATOR == node.kind):
        #     disposeBINARY_OPERATOR(node, cfgData);
        #
        # if (CursorKind.UNEXPOSED_EXPR == node.kind):
        #     disposeUNEXPOSED_EXPR(node, cfgData);

        if (CursorKind.RETURN_STMT == node.kind):
            self.disposeRETURN_STMT(node, cfgData);
            return;

        if (CursorKind.BREAK_STMT == node.kind):
            self.disposeBREAK_STMT(node, cfgData);
            return;

        if (CursorKind.CONTINUE_STMT == node.kind):
            self.disposeCONTINUE_STMT(node, cfgData);
            return;
        # if (CursorKind.DECL_STMT == node.kind):
        #     disposeDECL_STMT(node, cfgData);
        if (CursorKind.SWITCH_STMT == node.kind):
            self.disposeSWITCH_STMT(node, cfgData);
            return;

        if (CursorKind.CASE_STMT == node.kind):
            self.disposeCASE_STMT(node, cfgData);
            return;

        if (CursorKind.DEFAULT_STMT == node.kind):
            self.disposeDEFAULT_STMT(node, cfgData);
            return;

        if (CursorKind.COMPOUND_STMT == node.kind):
            self.disposeCOMPOUND_STMT(node, cfgData);
            return;

        if (CursorKind.FUNCTION_DECL == node.kind):
            self.disposeFUNCTION_DECL(node, cfgData);
            return;

        if (CursorKind.CXX_FOR_RANGE_STMT == node.kind):
            self.disposeCXX_FOR_RANGE_STMT(node, cfgData);
            return;
        # if(CursorKind.NULL_STMT == node.kind):
        #     disposeNULL_STMT(node, cfgData);

        if (CursorKind.FOR_STMT == node.kind):
            self.disposeFOR_STMT(node, cfgData);
            return;

        if (CursorKind.WHILE_STMT == node.kind):
            self.disposeWHILE_STMT(node, cfgData);
            return;

        if (CursorKind.DO_STMT == node.kind):
            self.disposeDO_STMT(node, cfgData);
            return;

        if (CursorKind.CXX_TRY_STMT == node.kind):
            self.disposeCXX_TRY_STMT(node, cfgData);
            return;

        if (CursorKind.CXX_CATCH_STMT == node.kind):
            self.disposeCXX_CATCH_STMT(node, cfgData);
            return;

        if (CursorKind.LABEL_STMT == node.kind):
            self.disposeLABEL_STMT(node, cfgData);
            return;

        if (CursorKind.GOTO_STMT == node.kind):
            self.disposeGOTO_STMT(node, cfgData);
            return;
        # if(CursorKind.VAR_DECL == node.kind):
        #     type = clang.getTypeDeclaration(node);
        #     print(clang.getTypeSpelling(type));

        if(CursorKind.UNEXPOSED_EXPR == node.kind):
            self.disposeUNEXPOSED_EXPR(node, cfgData);
            return;
        # if(CursorKind.DECL_STMT == node.kind):
        #     testChildren(node);
        #     statements = getStatements(node);
        #     testChildren(statements[0]);
        #     return;
        # if(CursorKind.VAR_DECL == node.kind):
        #     testChildren(node);
        #     return;
        if (node.location.file.name == file_name):
            self.disposeOther_Node(node, cfgData);

    def generateCFG(self, statements):
        print("len：", len(statements));

        # if(len(statements) == 0):
        #     return answer(nodes = [], edges":[], "last_nodes":[], "specialAndLastNodes");

        nodes: List[CFGNode] = [];
        edges: List[CFGEdge] = [];
        specialAndLastNodes: List[SpecialAndLastNode] = [];

        # 储存CFG数据
        cfgData = CFGData(nodes, edges, specialAndLastNodes);

        for node in statements:
            nodeId = node.hash;
            kind = node.kind;
            spelling = node.spelling;
            print("hash:", node.hash);
            print("kind:", node.kind);
            print("spelling:", node.spelling);
            print("fileName:", node.location.file.name);

            # if(CursorKind.COMPOUND_STMT == node.kind):

            self.visit(node, cfgData);

        return cfgData;

    def startGenerateCFG(self, root_cursor: clang.cindex.Cursor):
        statements = getStatements(root_cursor);
        return self.generateCFG(statements);

def analyzeIsOrThrow(string: str)-> str:
    """解析unexposed_expr是否含有throw关键字，并返回其throw出的变量名字"""

    match = re.search(r"throw\s+(\w+)\s*\(", string);

    if match:
        variable_name = match.group(1);
        print(f"The variable name is {variable_name}.");
        return variable_name;
    else:
        print("No match found.");
        return None;

def get_exception_name(string: str)-> str:
    """解析catch错误变量的名字，比如对于MyException & e 这样一个语句，返回前面的MyException"""
    pattern = r"\b([A-Za-z_]\w*)\s*&\s*([A-Za-z_]\w*)";
    match = re.search(pattern, string);
    if match:
        return match.group(1)
    else:
        return None;
