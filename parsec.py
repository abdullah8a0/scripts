#!/usr/bin/env python

import re
import sys
import graphlib

# Usage: python parsec.py <input_file> [output_file]
# If no output file is specified, the output will be written to stdout
# The input file should be a valid c file.


class Parsec:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file

    def parse(self):
        # return dictionary of: function name -> function body
        file, line_map = self.read_input()
        [line_numbers, functions, func_name] = self.get_functions(file)
        function_bodies = self.get_function_bodies(file, line_numbers)

        func_calls = self.get_func_calls(function_bodies)
        self.func_def_line = {}
        for i, func in enumerate(func_name):
            self.func_def_line[func] = line_map[line_numbers[i]]

        self.func_name_to_sig = dict(zip(func_name, functions))

        self.undefined_func_calls = set()
        for i, func_call in enumerate(func_calls):
            for j, call in enumerate(func_call):
                if call not in func_name:
                    self.undefined_func_calls.add(call)

        self.calls = dict(zip(func_name, func_calls))

    def read_order(self):
        call_graph = self.calls
        undef = self.undefined_func_calls
        line_map = self.func_def_line

        tp = graphlib.TopologicalSorter(call_graph)
        dag, cycles = self.clean_graph(tp, call_graph)
        print(f"cycles: {' => '.join(cycles) if cycles else None}")
        print("")
        tp = graphlib.TopologicalSorter(dag)
        print("Reading order: ")
        for func in tp.static_order():
            print(f"{line_map.get(func, 'undefined')} : \
                  {self.func_name_to_sig.get(func,func)} ")
        print("")
        if undef:
            print("Undefined function calls: ", undef)

    def clean_graph(self, tp, call_graph):
        try:
            tp.prepare()
            return call_graph, None
        except graphlib.CycleError as e:
            cycles = e.args[1]
            for func in cycles:
                if func in call_graph:
                    del call_graph[func]
            return call_graph, cycles

    def get_functions(self, file):
        # return list of function names and list of line numbers
        # where the function definitions start

        func_regex = re.compile(r'(\w+\s+)+(\w+\s*)\([^!@\#$+%]*?\)')
        functions = []
        line_numbers = []
        func_name = []
        for i, line in enumerate(file):
            if func_regex.match(line):
                # append the function signature.
                sig = func_regex.match(line).group(0).strip()
                return_type = func_regex.match(line).group(1).strip()
                name = func_regex.match(line).group(2).strip()
                if return_type == 'return':
                    continue
                functions.append(sig)
                func_name.append(name)
                line_numbers.append(i)
        return [line_numbers, functions, func_name]

    def get_function_bodies(self, file, line_numbers):
        # return list of function bodies
        # line_numbers is a list of line numbers where the function
        # definitions start

        function_bodies = []
        for i, line_number in enumerate(line_numbers):
            # if the function is the last function in the file
            if i == len(line_numbers) - 1:
                function_bodies.append(file[line_number+1:])
            else:
                function_bodies.append(file[line_number+1:line_numbers[i+1]])
        return list(map(lambda x: ' '.join(x), function_bodies))

    def get_func_calls(self, function_bodies):
        # print the function calls in the function bodies
        func_call_regex = re.compile(
                r'(?!\b(if|while|for|switch|else)\b)\b(\w+)(?=\s*\()')
        func_calls = []
        for i, function_body in enumerate(function_bodies):
            func_calls.append(list(map(
                lambda x: x.group(2), func_call_regex.finditer(
                    function_body))))

        std_funcs = {
                     'scanf', 'printf', 'strlen', 'if', 'max', 'min', 'return'
                     }
        return list(map(lambda x: set(filter(
            lambda y: y not in std_funcs, x)), func_calls))

    def read_input(self):
        # return list of lines in the input file and a dictionary
        # mapping new line numbers to old line numbers
        # clean up the input file by removing comments and extra whitespace
        with open(self.input_file, 'r') as f:
            file = f.readlines()
            file = list(map(lambda x: x.strip(), file))
            line_map = {}
            new_file = []

            for i, line in enumerate(file):
                if line.startswith('//'):
                    continue
                elif '//' in line:
                    line = line[:line.index('//')]
                if line:
                    line_map[len(new_file)] = i
                    new_file.append(line)
            return [new_file, line_map]


def main():
    if len(sys.argv) < 2:
        print("Usage: python parsec.py <input_file> [output_file]")
        sys.exit(1)
    input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = None
    parsec = Parsec(input_file, output_file)
    parsec.parse()
    parsec.read_order()


if __name__ == "__main__":
    main()
