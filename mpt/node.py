import rlp
from .nibble_path import NibblePath
from .hash import keccak_hash


def _prepare_reference_for_usage(ref):
    if isinstance(ref, list):
        return rlp.encode(ref)

    return ref


def _prepare_reference_for_encoding(ref):
    if 0 < len(ref) < 32:
        return rlp.decode(ref)

    return ref


class Node:
    class Leaf:
        def __init__(self, path, data):
            self.path = path
            self.data = data

        def encode(self):
            return rlp.encode([self.path.encode(True), self.data])

    class Extension:
        def __init__(self, path, next_ref):
            self.path = path
            self.next_ref = next_ref

        def encode(self):
            next_ref = _prepare_reference_for_encoding(self.next_ref)
            return rlp.encode([self.path.encode(False), next_ref])

    class Branch:
        def __init__(self, branches, data=None):
            self.branches = branches
            self.data = data

        def encode(self):
            branches = list(map(_prepare_reference_for_encoding, self.branches))
            return rlp.encode(branches + [self.data])

    def decode(encoded_data):
        data = rlp.decode(encoded_data)

        assert len(data) == 17 or len(data) == 2   # TODO throw exception

        if len(data) == 17:
            branches = list(map(_prepare_reference_for_usage, data[:16]))
            node_data = data[16]
            return Node.Branch(branches, node_data)

        path, is_leaf = NibblePath.decode_with_type(data[0])
        if is_leaf:
            return Node.Leaf(path, data[1])
        else:
            ref = _prepare_reference_for_usage(data[1])
            return Node.Extension(path, ref)

    def into_reference(node):
        encoded_node = node.encode()
        if len(encoded_node) < 32:
            return encoded_node
        else:
            return keccak_hash(encoded_node)
