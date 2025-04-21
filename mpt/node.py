from abc import ABC, abstractmethod

import rlp

from .hash import keccak_hash
from .nibble_path import NibblePath

NODE_REF_LENGTH = 32


def _prepare_reference_for_usage(ref):
    """Encodes reference into RLP so stored references will appear as bytes."""
    if not isinstance(ref, bytes):
        return rlp.encode(ref)

    return ref


def _prepare_reference_for_encoding(ref):
    """Decodes RLP-encoded reference so the full node will be encoded correctly."""
    if 0 < len(ref) < NODE_REF_LENGTH:
        return rlp.decode(ref)

    return ref


class Node:
    EMPTY_HASH = keccak_hash(rlp.encode(b''))

    class AnyNode(ABC):
        @abstractmethod
        def raw(self) -> bytes:
            raise NotImplementedError

    class Leaf(AnyNode):
        def __init__(self, path, data):
            self.path = path
            self.data = data

        def encode(self):
            return rlp.encode([self.path.encode(True), self.data])

        def raw(self):
            return [self.path.encode(True), self.data]

    class Extension:
        def __init__(self, path, next_ref):
            self.path = path
            self.next_ref = next_ref

        def encode(self):
            next_ref = _prepare_reference_for_encoding(self.next_ref)
            return rlp.encode([self.path.encode(False), next_ref])

        def raw(self):
            return [self.path.encode(False), self.data]

    class Branch:
        def __init__(self, branches, data=None):
            self.branches = branches
            self.data = data

        def encode(self):
            branches = list(map(_prepare_reference_for_encoding, self.branches))
            return rlp.encode([*branches, self.data])

        def raw(self):
            return [*self.branches, self.data]

    @classmethod
    def decode(cls, encoded_data):
        """Decodes node from RLP."""
        data = rlp.decode(encoded_data)

        if len(data) not in {17, 2}:
            raise ValueError('Unknown data format.')

        if len(data) == 17:  # noqa: PLR2004
            branches = list(map(_prepare_reference_for_usage, data[:16]))
            node_data = data[16]
            return Node.Branch(branches, node_data)

        path, is_leaf = NibblePath.decode_with_type(data[0])
        if is_leaf:
            return Node.Leaf(path, data[1])
        ref = _prepare_reference_for_usage(data[1])
        return Node.Extension(path, ref)

    @classmethod
    def into_reference(cls, node):
        """Returns reference to the given node.

        If length of encoded node is less than 32 bytes, the reference is encoded node
        itself (In-place reference).
        Otherwise reference is keccak hash of encoded node.
        """
        encoded_node = node.encode()
        if len(encoded_node) < NODE_REF_LENGTH:
            return encoded_node
        return keccak_hash(encoded_node)
