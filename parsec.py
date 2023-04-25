#!/usr/bin/env python

import sys
import graphlib
from typing import Callable, Dict, List, Set, Tuple
import tree_sitter

# Usage: python parsec.py <input_file> [output_file]
# If no output file is specified, the output will be written to stdout
# The input file should be a valid c file.


class SyntaxTree:
    """
    Monadic syntax tree
    to simplify tree-sitter queries
    """

    def make(self, nodes: List[tree_sitter.Node] |
             tree_sitter.Node) -> 'SyntaxTree':
        if isinstance(nodes, tree_sitter.Node):
            self.nodes = [nodes]
        else:
            self.nodes = nodes[:]
        return self

    def __len__(self):
        return len(self.nodes)

    def __getitem__(self, i):
        return self.nodes[i]

    def __iter__(self):
        return iter(self.nodes)

    def __rshift__(self, q: str | Callable[[tree_sitter.Node], 'SyntaxTree']) \
            -> 'SyntaxTree':
        """
        Sumplify using __rshift__ operator
        self.unit() >> q1 >> q2 >> q3
        """
        if isinstance(q, str):
            return self.bind(q, self)
        return self.flat_map(q, self)

    def __init__(self, file):

        self.nodes: List[tree_sitter.Node] = []
        # migrate to tree-sitter
        parser = tree_sitter.Parser()
        # To C
        tree_sitter.Language.build_library(
            # Store the library in the `build` directory
            '/home/abdullah/.scripts/build/my-languages.so',
            # Include one or more languages
            ["/home/abdullah/.scripts/tree-sitter-c"]
        )
        self.lang = tree_sitter.Language(
            "/home/abdullah/.scripts/build/my-languages.so", "c")
        parser.set_language(self.lang)
        self.tree = parser.parse(bytes('\n'.join(file), 'utf-8'))

    def flat_map(self, f: Callable[[tree_sitter.Node], 'SyntaxTree'],
                 xs: 'SyntaxTree') -> 'SyntaxTree':

        y: List[tree_sitter.Node] = []
        for x in xs.nodes:
            nodes = f(x)
            if isinstance(nodes, SyntaxTree):
                y.extend(nodes.nodes)
            elif isinstance(nodes, list):
                y.extend(nodes)
            elif isinstance(nodes, str):
                y.append(nodes)
        return self.make(y)

    def unit(self, n: List[tree_sitter.Node] | tree_sitter.Node = []) \
            -> 'SyntaxTree':
        if not n:
            return self.make(self.tree.root_node)
        return self.make(n)

    def bind(self, q: str, ns: 'SyntaxTree') -> 'SyntaxTree':
        query = self.lang.query(q)
        return self.flat_map(
            lambda n: self.make([
                node for node, _ in query.captures(n)]), ns)


class Parsec:
    def __init__(self, input_file):
        self.input_file = input_file
        self.common_funcs = {
            "printf", "scanf", "malloc", "free", "strcpy", "strcat", "strlen",
            "strcmp", "strchr", "strstr", "strtok", "strncpy", "strncat",
            "calloc", "realloc", "memcpy", "memmove", "memcmp", "memset",
            "abort", "exit", "atexit", "getenv", "system", "bsearch",
            "fprintf", "fscanf", "fopen", "fclose", "fgetc", "fputc",
            "panic", "BIT", "assert", "max", "min"}

    def parse(self):

        with open(self.input_file, 'r') as f:
            file = f.readlines()
            file = list(map(lambda x: x.strip(), file))
            self.file = file

        self.st = SyntaxTree(file)

        names_query = """(function_definition
                            (function_declarator
                             (identifier) @name))"""

        body_query = """(function_definition
                         (function_declarator
                          (identifier))
                         body:
                         (compound_statement) @body)"""

        call_query = """(call_expression
                         function: (_) @f)"""

        func_name: List[tree_sitter.Node] = (
            self.st.unit()
            >> names_query
            >> (lambda n: n.text.decode('utf-8'))).nodes

        self.def_loc = dict(zip(
            func_name, map(lambda n: n.start_point[0] + 1,
                           self.st.unit() >> body_query)))

        func_calls = [set([
            call.text.decode('utf-8') for call in
            self.st.unit(body) >> call_query])
            for body in self.st.unit() >> body_query]

        self.undefined_func_calls: Set[str] = set(
            call for body in func_calls for call in body
            if call not in func_name and call not in self.common_funcs)

        self.calls: Dict[str, str] = dict(zip(func_name, func_calls))
        return self

    def read_order(self):
        dag, cycles = self.clean_graph(self.calls)
        for cycle in cycles:
            print(f"cycle: {' => '.join(cycle)}")
        print("")
        tp = graphlib.TopologicalSorter(dag)
        print("Reading order: ")
        # TODO:hide undefined functions
        for func in tp.static_order():
            if func in self.def_loc:
                print(f"{self.def_loc.get(func, 'UD')} : \
                  {func}")
        print("")
        if self.undefined_func_calls:
            print("Undefined function calls: ", self.undefined_func_calls)

    def clean_graph(self, call_graph: Dict[str, str]) \
            -> Tuple[Dict[str, str], List[List[str]]]:

        tp = graphlib.TopologicalSorter(call_graph)

        cycles: List[List[str]] = []
        while True:
            try:
                tp.prepare()
                return (call_graph, cycles)
            except graphlib.CycleError as e:
                cycle: List[str] = list(e.args[1])
                for func in cycle:
                    if func in call_graph:
                        del call_graph[func]
                cycles.append(cycle)
                tp = graphlib.TopologicalSorter(call_graph)


def main():
    if len(sys.argv) < 2:
        print("Usage: python parsec.py <input_file> [output_file]")
        sys.exit(1)
    input_file = sys.argv[1]
    if input_file == "demo":
        return

    if len(sys.argv) >= 2:
        for input_file in sys.argv[1:]:
            print(f"Input file: {input_file}")
            Parsec(input_file).parse().read_order()
            print("")


if __name__ == "__main__":
    main()
