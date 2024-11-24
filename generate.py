import json
import sys


def get_output(mod_api):
    output = ""

    output += "#define PY_SSIZE_T_CLEAN\n"
    output += "#include <Python.h>\n"
    output += "\n"
    output += "#include <assert.h>\n"
    output += "\n"
    output += "typedef char* string;\n"
    output += "typedef int32_t i32;\n"
    output += "typedef uint64_t id;\n"
    output += "\n"
    output += "static PyObject *main_module;\n"

    output += "\n"

    for entity in mod_api["entities"].keys():
        output += f"static PyObject *game_fn_define_{entity}_handle;\n"

    for fn in mod_api["game_functions"].keys():
        output += f"static PyObject *game_fn_{fn}_handle;\n"

    output += "\n"

    output += "#define CHECK_PYTHON_ERROR() {\\\n"
    output += "    if (PyErr_Occurred()) {\\\n"
    output += "        PyErr_Print();\\\n"
    output += (
        '        fprintf(stderr, "Error detected in adapter.c:%d\\n", __LINE__);\\\n'
    )
    output += "        exit(EXIT_FAILURE);\\\n"
    output += "    }\\\n"
    output += "}\n"

    output += "\n"

    output += "void init(void) {\n"

    output += '    PyObject *modules = PySys_GetObject("modules");\n'
    output += "    CHECK_PYTHON_ERROR();\n"
    output += "    assert(modules);\n"

    output += "\n"

    output += '    main_module = PyDict_GetItemString(modules, "__main__");\n'
    output += "    CHECK_PYTHON_ERROR();\n"
    output += "    assert(main_module);\n"

    output += "\n"

    for entity in mod_api["entities"].keys():
        output += f'    game_fn_define_{entity}_handle = PyObject_GetAttrString(main_module, "game_fn_define_{entity}");\n'
        output += f"    CHECK_PYTHON_ERROR();\n"
        output += f"    assert(game_fn_define_{entity}_handle);\n"
        output += "\n"

    for i, fn in enumerate(mod_api["game_functions"].keys()):
        output += f'    game_fn_{fn}_handle = PyObject_GetAttrString(main_module, "game_fn_{fn}");\n'
        output += f"    CHECK_PYTHON_ERROR();\n"
        output += f"    assert(game_fn_{fn}_handle);\n"

        if i < len(mod_api["game_functions"].keys()) - 1:
            output += "\n"

    output += "}\n"

    output += "\n"

    for name, entity in mod_api["entities"].items():
        output += f"void game_fn_define_{name}("

        for i, field in enumerate(entity["fields"]):
            if i > 0:
                output += ", "

            output += field["type"]
            output += " "
            output += field["name"]

        output += ") {\n"

        arg_count = len(entity["fields"])

        if arg_count > 0:
            for field_index, field in enumerate(entity["fields"]):
                output += f"    PyObject *arg{field_index + 1} = "

                typ = field["type"]

                # TODO: Test all these!
                if typ == "bool" or typ == "i32":
                    output += "PyLong_FromLong"
                elif typ == "id":
                    output += "PyLong_FromUnsignedLongLong"
                elif typ == "f32":
                    output += "PyFloat_FromDouble"
                elif typ == "string" or typ == "resource" or typ == "entity":
                    output += "PyUnicode_FromString"

                output += "("
                output += field["name"]
                output += ");\n"

                output += "    CHECK_PYTHON_ERROR();\n"
                output += f"    assert(arg{field_index + 1});\n"

            output += "\n"

            output += f"    PyObject *args = PyTuple_Pack({arg_count}"

            for field_index in range(arg_count):
                output += f", arg{field_index + 1}"

            output += ");\n"

            output += "    CHECK_PYTHON_ERROR();\n"
            output += "    assert(args);\n"

            output += "\n"

        output += (
            f"    PyObject *result = PyObject_CallObject(game_fn_define_{name}_handle, "
        )
        output += "args" if arg_count > 0 else "NULL"
        output += ");\n"
        output += "    CHECK_PYTHON_ERROR();\n"
        output += "    assert(result);\n"

        output += "}\n"

        output += "\n"

    for i, (name, fn) in enumerate(mod_api["game_functions"].items()):
        output += fn.get("return_type", "void")

        output += f" game_fn_{name}("

        for arg_index, arg in enumerate(fn["arguments"]):
            if arg_index > 0:
                output += ", "

            output += arg["type"]
            output += " "
            output += arg["name"]

        output += ") {\n"

        arg_count = len(fn["arguments"])

        if arg_count > 0:
            for arg_index, arg in enumerate(fn["arguments"]):
                output += f"    PyObject *arg{arg_index + 1} = "

                typ = arg["type"]

                # TODO: Test all these!
                if typ == "bool" or typ == "i32":
                    output += "PyLong_FromLong"
                elif typ == "id":
                    output += "PyLong_FromUnsignedLongLong"
                elif typ == "f32":
                    output += "PyFloat_FromDouble"
                elif typ == "string" or typ == "resource" or typ == "entity":
                    output += "PyUnicode_FromString"

                output += "("
                output += arg["name"]
                output += ");\n"

                output += "    CHECK_PYTHON_ERROR();\n"
                output += f"    assert(arg{arg_index + 1});\n"

            output += "\n"

            output += f"    PyObject *args = PyTuple_Pack({arg_count}"

            for arg_index in range(arg_count):
                output += f", arg{arg_index + 1}"

            output += ");\n"

            output += "    CHECK_PYTHON_ERROR();\n"
            output += "    assert(args);\n"

            output += "\n"

        output += f"    PyObject *result = PyObject_CallObject(game_fn_{name}_handle, "
        output += "args" if arg_count > 0 else "NULL"
        output += ");\n"
        output += "    CHECK_PYTHON_ERROR();\n"
        output += "    assert(result);\n"

        if "return_type" in fn:
            return_type = fn["return_type"]

            output += "\n"

            # TODO: Test all these!
            if return_type == "bool" or return_type == "i32":
                output += "    return PyLong_AsLong(result);\n"
            elif return_type == "id":
                output += "    return PyLong_AsUnsignedLongLong(result);\n"
            elif return_type == "f32":
                output += "    return PyFloat_AsDouble(result);\n"
            elif (
                return_type == "string"
                or return_type == "resource"
                or return_type == "entity"
            ):
                output += "    return PyUnicode_AsUTF8(result);\n"

        output += "}\n"

        if i < len(mod_api["game_functions"].keys()) - 1:
            output += "\n"

    return output


def main(mod_api_path, output_path):
    with open(mod_api_path) as f:
        mod_api = json.load(f)

    with open(output_path, "w") as f:
        f.write(get_output(mod_api))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])