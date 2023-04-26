import src.CFGBuilder
import src.DDGBuilder
import json
import src.Utils
import flask

debug_counter: int = 0


def debug_specific(file_name: str, counter: int) -> None:
    with open(file_name, "r") as src_file:
        json_codes: list = src_file.readlines()
    build_once(json.loads(json_codes[counter])["code"])
    src_file.close()


def build_once(src_code: str) -> str:
    # print('\n' + src_code)
    cfg = src.CFGBuilder.CFGVisitor(src_code)
    cfg.build_cfg()
    # code = cfg.export_cfg_to_mermaid()

    # main
    ddg = src.DDGBuilder.DDGVisitor(cfg.cfg_nodes)
    ddg.build_ddg()

    # function
    ddgs: list = [ddg]
    for key, value in cfg.function_def_node.items():
        ddgs.append(src.DDGBuilder.DDGVisitor(value.cfg_nodes, key))
        ddgs[-1].build_ddg()
    data = src.Utils.DataContainer(cfg, ddgs, True)
    return str(data)


def sample_test():
    with open("target.py", "r") as src_file:
        src_code = src_file.read()
    src_file.close()
    return build_once(src_code)


def test_main(file_name: str):
    global debug_counter
    with open(file_name, "r") as src_file:
        json_codes: list = src_file.readlines()
    succ_counter: int = 0
    for each_json_raw_code in json_codes:
        json_code = json.loads(each_json_raw_code)
        try:
            build_once(json_code["code"])
            succ_counter = succ_counter + 1
        except Exception:
            pass
        debug_counter = debug_counter + 1
        print(debug_counter)
    print(succ_counter)
    src_file.close()


def interface_main(src_code: str) -> str:
    return build_once(src_code)


app = flask.Flask(__name__)


@app.route("/getCFG", methods=["POST"])
def index():
    code = flask.request.get_json()["code"]
    return build_once(code)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
