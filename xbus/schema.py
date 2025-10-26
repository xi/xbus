import xml.etree.ElementTree as ET
from collections import namedtuple

Property = namedtuple('Property', ['type', 'access'])
Method = namedtuple('Method', ['args', 'returns'])
Signal = namedtuple('Signal', ['args', 'returns'])
Interface = namedtuple('Interface', ['properties', 'methods', 'signals'])
Schema = namedtuple('Schema', ['interfaces', 'nodes'])


def get_all(node, tag, parse):
    return {n.get('name'): parse(n) for n in node.findall(tag)}


def parse_arg(node):
    return node.get('type')


def parse_property(node):
    return Property(
        type=node.get('type'),
        access=node.get('access'),
    )

def parse_method(node):
    return Method(
        get_all(node, './/arg[@direction="in"]', parse_arg),
        get_all(node, './/arg[@direction="out"]', parse_arg),
    )

def parse_signal(node):
    return Signal(
        get_all(node, './/arg[@direction="in"]', parse_arg),
        get_all(node, './/arg[@direction="out"]', parse_arg),
    )

def parse_interface(node):
    return Interface(
        properties=get_all(node, 'property', parse_property),
        methods=get_all(node, 'method', parse_method),
        signals=get_all(node, 'signal', parse_signal),
    )


def parse_schema(s):
    tree = ET.fromstring(s)
    return Schema(
        interfaces=get_all(tree, 'interface', parse_interface),
        nodes=[n.get('name') for n in tree.findall('node')],
    )
