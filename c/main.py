import os
import sys
from pathlib import Path

sys.path.append(rf"{Path(__file__).resolve().parent.parent}/disposeCFG")
print("main:", sys.path)
print(sys.path)
from clang.cindex import *
from nameClass import *
from parse import DisposeCFGController
import json

file_name = "code.cpp"

Config.set_library_file(os.getenv("library_file"))

stringT = '#include <iostream>\n\n//int addNumbers(int a, int b);\n\nint main()\n{\n//   for(int i=0;i<4;i++)\n//   {\n//       std::cout<<i<<std::endl;\n//   }\n\n//    int i = 0;\n//    do\n//    {\n//        i++;\n//    }while(i < 4);\n\n      int  i = 0;\n      for(int j = 0; j < 4; j++)\n      {\n           switch(i)\n          {\n    //        if(i==3)\n    //        {\n    //            std::cout<<"0"<<std::endl;\n    //        }\n            case 1:\n                std::cout<<"1"<<std::endl;\n                break;\n            case 2:\n                std::cout<<"2"<<std::endl;\n                return;\n            case 4:\n                std::cout<<"4"<<std::endl;\n                continue;\n            case 3:\n                std::cout<<"3"<<std::endl;\n                break;\n            default:\n                std::cout<<"other"<<std::endl;\n          }\n      }\n\n//      int a[5];\n//      for(int i = 0; i<5;i++)\n//      {\n//        a[i]= i;\n//      }\n//\n//      for(item:a)\n//      {\n//        std::cout<<"num is "<<item<<std::endl;\n//      }\n\n\n\n//    std::cout<<"start"<<std::endl;\n//    auto test = [](int x, int y){ return x < y ; };\n//    test(10,20);\n//    int ans[20] = {0,};\n//\n//    if(ans[1]== 0)\n//    std::cout<<"good"<<std::endl;\n//\n//    if(ans[2]==0);\n//    int *p = new int(3);\n//    if(*p == 3)\n//    {\n//        std::cout<<"is 3"<<std::endl;\n//    }\n//\n//    if(p)\n//    {\n//        std::cout<<"exist"<<std::endl;\n//    }\n//    int flag = 0;\n//            while(flag < 4)\n//            {\n//                flag++;\n//                if(flag == 3)\n//                {\n//                    break;\n//                }\n//                else\n//                std::cout<<"error"<<std::endl;\n//                std::cout<<"error"<<std::endl;\n//            }\n//\n//            do\n//            {\n//                flag--;\n//                continue;\n//            }while(flag>0);\n//    for(int i = 0; i < 4;i++)\n//    {\n//        for(int j = 0; j < 5;j++)\n//        {\n//            std::cout<<i<<j<<std::endl;\n//\n//            int flag = 0;\n//            while(flag < 4)\n//            {\n//                flag++;\n//            }\n//\n//            do\n//            {\n//                flag--;\n//            }while(flag>0)\n//        }\n//    }\n  return 0;\n}\n\n//int addNumbers(int a,int b)\n//{\n//    int result;\n//    result = a+b;\n//    return result;\n//}'


def add_escape_chars(string: str) -> str:
    string = string.replace('"', "'")
    return string


def getMermaid(cfgData: CFGData):
    answer = "stateDiagram-v2\n"
    print("node.length:", len(cfgData.nodes))
    for node in cfgData.nodes:
        if type(node) == CFGBlock:
            answer += "state"
            answer = (
                answer
                + ' "'
                + add_escape_chars(node.text)
                + '" '
                + "as "
                + str(node.id)
            )
            answer += "{\n"

            # 处理节点
            for children_node in node.children.nodes:
                answer = (
                    answer
                    + "state"
                    + ' "'
                    + add_escape_chars(children_node.text)
                    + ' "'
                    + " as "
                    + str(children_node.id)
                    + "\n"
                )

            # 处理边
            for children_edge in node.children.edges:
                answer = (
                    answer
                    + str(children_edge.begin)
                    + "-->"
                    + str(children_edge.end)
                    + "\n"
                )

            answer += "}\n"
            continue
        if type(node) == CFGNode:
            answer += f'state "{add_escape_chars(node.text)}" as {str(node.id)}\n'

    for edge in cfgData.edges:
        answer += f"{str(edge.begin)}-->{str(edge.end)}\n"

    if len(cfgData.nodes) > 0:
        answer += f"[*]-->{cfgData.nodes[0].id}\n"
        answer += f"{cfgData.nodes[-1].id}-->[*]\n"

    return answer


def generateAST(code: str):
    index = Index.create()

    tu = index.parse(
        "code.cpp", args=["-std=c++11"], unsaved_files=[("code.cpp", code)]
    )
    return tu.cursor


def getCFG(code: str):
    root_cursor = generateAST(code)
    disposeCFGController = DisposeCFGController()
    cfgData = disposeCFGController.startGenerateCFG(root_cursor)
    mermaid = getMermaid(cfgData)
    # 获取mermaid

    return {"mermaid": mermaid, "CSN": {"cfg_dependency": cfgData.to_dict()}}
    # cfg = {};
    # cfg["nodes"] = test.nodes;
    # cfg["edges"] = test.edges;
    # return test.to_dict();


from flask import Flask, request, jsonify

# write flask server that will execute getCFG
app = Flask(__name__)


@app.route("/getCFG", methods=["POST"])
def getCFGFromCode():
    code = request.json.get("code")
    print(code)
    answer = getCFG(code)
    return jsonify(answer)


@app.route("/", methods=["GET"])
def index():
    return "API is working.\n"


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
