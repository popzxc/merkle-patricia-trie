class NibblePath:
    def __init__(self, data, offset = 0):
        self._data = data
        self._offset = offset

class Node:
    class Leaf:
        def __init__(self, path, data):
            self.path = path
            self.data = data

    class Extension:
        def __init__(self, path, next_ref):
            self.path = path
            self.next_ref = next_ref

    class Branch:
        def __init__(self, branches, data = None):
            self.branches = branches
            self.data = data

    def __init__(self, node_inner):
        self.inner = node_inner
