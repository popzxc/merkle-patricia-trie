from enum import Enum
from .hash import keccak_hash
from .nibble_path import NibblePath
from .node import Node


class MerklePatriciaTrie:
    def __init__(self, storage, root=None):
        if root == Node.EMPTY_HASH:
            root = None

        self._storage = storage
        self._root = root

    def _get_node(self, node_ref):
        raw_node = None
        if len(node_ref) == 32:
            raw_node = self._storage[node_ref]
        else:
            raw_node = node_ref
        return Node.decode(raw_node)

    def root_hash(self):
        if not self._root:
            return Node.EMPTY_HASH
        elif len(self._root) == 32:
            return self._root
        else:
            return keccak_hash(self._root)

    def get(self, encoded_key):
        if not self._root:
            raise KeyError

        path = NibblePath(encoded_key)

        result_node = self._get(self._root, path)

        return result_node.data

    def _get(self, node_ref, path):
        node = self._get_node(node_ref)

        if len(path) == 0:
            return node

        if type(node) is Node.Leaf:
            if node.path == path:
                return node

        elif type(node) is Node.Extension:
            if path.starts_with(node.path):
                rest_path = path.consume(len(node.path))
                return self._get(node.next_ref, rest_path)

        elif type(node) is Node.Branch:
            branch = node.branches[path.at(0)]
            if len(branch) > 0:
                return self._get(branch, path.consume(1))

        raise KeyError

    def update(self, encoded_key, encoded_value):
        path = NibblePath(encoded_key)

        result = self._update(self._root, path, encoded_value)

        self._root = result

    def _update(self, node_ref, path, value):
        if not node_ref:
            return self._store_node(Node.Leaf(path, value))

        node = self._get_node(node_ref)

        if type(node) == Node.Leaf:
            if node.path == path:
                node.data = value
                return self._store_node(node)

            common_prefix = path.common_prefix(node.path)

            path.consume(len(common_prefix))
            node.path.consume(len(common_prefix))

            branch_reference = self._create_branch_node(path, value, node.path, node.data)

            if len(common_prefix) != 0:
                return self._store_node(Node.Extension(common_prefix, branch_reference))
            else:
                return branch_reference

        elif type(node) == Node.Extension:
            if path.starts_with(node.path):
                new_reference = self._update(node.next_ref, path.consume(len(node.path)), value)
                return self._store_node(Node.Extension(node.path, new_reference))

            common_prefix = path.common_prefix(node.path)

            path.consume(len(common_prefix))
            node.path.consume(len(common_prefix))

            branches = [b''] * 16
            branch_value = value if len(path) == 0 else b''

            self._create_branch_leaf(path, value, branches)
            self._create_branch_extension(node.path, node.next_ref, branches)

            branch_reference = self._store_node(Node.Branch(branches, branch_value))

            if len(common_prefix) != 0:
                return self._store_node(Node.Extension(common_prefix, branch_reference))
            else:
                return branch_reference

        elif type(node) == Node.Branch:
            if len(path) == 0:
                return self._store_node(Node.Branch(node.branches, value))

            idx = path.at(0)
            new_reference = self._update(node.branches[idx], path.consume(1), value)

            node.branches[idx] = new_reference

            return self._store_node(node)

    def _create_branch_node(self, path_a, value_a, path_b, value_b):
        assert len(path_a) != 0 or len(path_b) != 0

        branches = [b''] * 16

        branch_value = b''
        if len(path_a) == 0:
            branch_value = value_a
        elif len(path_b) == 0:
            branch_value = value_b

        self._create_branch_leaf(path_a, value_a, branches)
        self._create_branch_leaf(path_b, value_b, branches)

        return self._store_node(Node.Branch(branches, branch_value))

    def _create_branch_leaf(self, path, value, branches):
        if len(path) > 0:
            idx = path.at(0)

            leaf_ref = self._update(None, path.consume(1), value)
            branches[idx] = leaf_ref

    def _create_branch_extension(self, path, next_ref, branches):
        assert len(path) >= 1, "Path for extension node should contain at least one nibble"

        if len(path) == 1:
            branches[path.at(0)] = next_ref
        else:
            idx = path.at(0)
            reference = self._store_node(Node.Extension(path.consume(1), next_ref))
            branches[idx] = reference

    def _store_node(self, node):
        reference = Node.into_reference(node)
        if len(reference) == 32:
            self._storage[reference] = node.encode()
        return reference

    class DeleteAction(Enum):
        DELETED = 1,
        UPDATED = 2,
        USELESS_BRANCH = 3

    def delete(self, encoded_key):
        if self._root is None:
            return

        path = NibblePath(encoded_key)

        action, info = self._delete(self._root, path)

        if action == MerklePatriciaTrie.DeleteAction.DELETED:
            # Trie is empty
            self._root = None
        elif action == MerklePatriciaTrie.DeleteAction.UPDATED:
            new_root = info
            self._root = new_root
        elif action == MerklePatriciaTrie.DeleteAction.USELESS_BRANCH:
            _, new_root = info
            self._root = new_root

    def _delete(self, node_ref, path):
        node = self._get_node(node_ref)

        if type(node) == Node.Leaf:
            if len(path) == 0 or path == node.path:
                return MerklePatriciaTrie.DeleteAction.DELETED, None
            else:
                raise KeyError

        elif type(node) == Node.Extension:
            if not path.starts_with(node.path):
                raise KeyError

            action, info = self._delete(node.next_ref, path.consume(len(node.path)))

            if action == MerklePatriciaTrie.DeleteAction.DELETED:
                return action, None
            elif action == MerklePatriciaTrie.DeleteAction.UPDATED:
                child_ref = info
                new_ref = self._store_node(Node.Extension(node.path, child_ref))
                return action, new_ref
            elif action == MerklePatriciaTrie.DeleteAction.USELESS_BRANCH:
                stored_path, stored_ref = info

                child = self._get_node(stored_ref)

                new_reference = None
                if type(child) == Node.Leaf:
                    path = NibblePath.combine(node.path, child.path)
                    new_reference = self._store_node(Node.Leaf(path, child.data))
                elif type(child) == Node.Extension:
                    path = NibblePath.combine(node.path, child.path)
                    new_reference = self._store_node(Node.Extension(path, child.next_ref))
                elif type(child) == Node.Branch:
                    path = NibblePath.combine(node.path, stored_path)
                    new_reference = self._store_node(Node.Extension(path, node.next_ref))

                return MerklePatriciaTrie.DeleteAction.UPDATED, new_reference

        elif type(node) == Node.Branch:
            action = None
            idx = None
            info = None

            if len(path) == 0 and len(node.data) != 0:
                node.data = None
                action = MerklePatriciaTrie.DeleteAction.DELETED
            else:
                idx = path.at(0)

                if len(node.branches[idx]) == 0:
                    raise KeyError

                action, info = self._delete(node.branches[idx], path.consume(1))
                node.branches[idx] = b''

            if action == MerklePatriciaTrie.DeleteAction.DELETED:
                non_empty_count = sum(map(lambda x: 1 if len(x) > 0 else 0, node.branches))

                if non_empty_count == 0 and len(node.data) == 0:
                    # Branch node is empty, just delete it.
                    return MerklePatriciaTrie.DeleteAction.DELETED, None
                elif non_empty_count == 0 and len(node.data) != 0:
                    # No branches, just value.
                    path = NibblePath([])
                    reference = self._store_node(Node.Leaf(path, node.data))

                    return MerklePatriciaTrie.DeleteAction.USELESS_BRANCH, (path, reference)
                elif non_empty_count == 1 and len(node.data) == 0:
                    # No value and one branch
                    return self._process_branch_removal(node.branches)
                else:
                    # Branch has value and 1+ branches or no value and 2+ branches.
                    reference = self._store_node(node)
                    return MerklePatriciaTrie.DeleteAction.UPDATED, reference
            elif action == MerklePatriciaTrie.DeleteAction.UPDATED:
                next_ref = info
                node.branches[idx] = next_ref
                reference = self._store_node(node)
                return MerklePatriciaTrie.DeleteAction.UPDATED, reference
            elif action == MerklePatriciaTrie.DeleteAction.USELESS_BRANCH:
                _, next_ref = info
                node.branches[idx] = next_ref
                reference = self._store_node(node)
                return MerklePatriciaTrie.DeleteAction.UPDATED, reference

    def _process_branch_removal(self, branches):

        # Find the index of the only stored branch.
        idx = 0
        for i in range(len(branches)):
            if len(branches[i]) > 0:
                idx = i
                break

        # Path in leaf will contain one nibble (at this step).
        prefix_nibble = NibblePath([idx], offset=1)

        child = self._get_node(branches[idx])

        path = None
        reference = None
        if type(child) == Node.Leaf:
            path = NibblePath.combine(prefix_nibble, child.path)
            reference = self._store_node(Node.Leaf(path, child.data))
        elif type(child) == Node.Extension:
            path = NibblePath.combine(prefix_nibble, child.path)
            reference = self._store_node(Node.Extension(path, child.next_ref))
        elif type(child) == Node.Branch:
            path = prefix_nibble
            reference = self._store_node(Node.Extension(path, branches[idx]))

        return MerklePatriciaTrie.DeleteAction.USELESS_BRANCH, (path, reference)
