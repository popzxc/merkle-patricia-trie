import rlp
from hash import hash


class NibblePath:
    def __init__(self, data, offset=0):
        self._data = data
        self._offset = offset

    def __len__(self):
        return self._data.len() * 2 - self._offset

    def __eq__(self, other):
        if len(self) != len(other):
            return False

        for i in range(len(self)):
            if self.at(i) != other.at(i):
                return False

        return True

    def starts_with(self, other):
        if len(other) > len(self):
            return False

        for i in range(len(other)):
            if self.at(i) != other.at(i):
                return False

        return True

    def consume(self, n_nibbles):
        self._offset += n_nibbles

    def is_leaf(self):
        return ord(self._data[0]) & 0x20 == 0x20

    def at(self, idx):
        idx = idx + self._offset

        byte_idx = idx // 2
        nibble_idx = idx % 2

        byte = self._data[byte_idx]

        nibble = byte >> 4 if nibble_idx == 0 else byte & 0x0F

        return nibble

    def consume(self, amount):
        self._offset += amount
        return self

    def common_prefix(self):
        pass


class Node:
    class Leaf:
        def __init__(self, path, data):
            self.path = path
            self.data = data

        def encode(self):
            return rlp.encode([self.path, self.data])

    class Extension:
        def __init__(self, path, next_ref):
            self.path = path
            self.next_ref = next_ref

        def encode(self):
            return rlp.encode([self.path, self.next_ref])

    class Branch:
        def __init__(self, branches, data=None):
            self.branches = branches
            self.data = data

        def encode(self):
            return rlp.encode([self.branches, self.data])

    def decode(encoded_data):
        data = rlp.decode(encoded_data)

        assert len(data) == 17 or len(data) == 2   # TODO throw exception

        if len(data) == 17:
            branches = data[:16]
            node_data = data[16]
            return Node.Branch(branches, node_data)

        path = NibblePath(data[0])
        if path.is_leaf():
            return Node.Leaf(data[0], data[1])
        else:
            return Node.Extension(data[0], data[1])

    def into_reference(node):
        encoded_node = node.encode()
        if len(encoded_node) < 32:
            return encoded_node
        else:
            return hash(encoded_node)


class MerklePatriciaTrie:
    def __init__(self, storage, root=None):
        self._storage = storage
        self._root = root

    def _get_node(self, node_ref):
        raw_node = None
        if len(node_ref) == 32:
            raw_node = self._storage[node_ref]
        else:
            raw_node = node_ref
        return Node.decode(raw_node)

    def get(self, encoded_key):
        path = NibblePath(encoded_key)

        result_node = self._get(self._root, path)

        return result_node.data

    def _get(self, node_ref, path):
        node = self._get_node(node_ref)

        if len(path) == 0:
            return node

        if type(node) is Node.Leaf:
            if NibblePath(node.path) == path:
                return node
        elif type(node) is Node.Extension:
            if path.starts_with(NibblePath(node.path)):
                rest_path = path.consume(len(node.path))
                return self._get(node.next_ref, rest_path)
        elif type(node) is Node.Branch:
            branch = node.branches[path.at(0)]
            if len(branch) > 0:
                return self._get(branch, path.consume(1))

        raise KeyError

    def update(self, encoded_key, encoded_value):
        pass

    def delete(self, encoded_key):
        if self._root is None:
            return
