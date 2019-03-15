import unittest
from mpt import MerklePatriciaTrie
from mpt.nibble_path import NibblePath
from mpt.node import Node
import rlp
import random


class TestNibblePath(unittest.TestCase):
    def test_at(self):
        nibbles = NibblePath([0x12, 0x34])
        self.assertEqual(nibbles.at(0), 0x1)
        self.assertEqual(nibbles.at(1), 0x2)
        self.assertEqual(nibbles.at(2), 0x3)
        self.assertEqual(nibbles.at(3), 0x4)

    def test_at_with_offset(self):
        nibbles = NibblePath([0x12, 0x34], offset=1)
        self.assertEqual(nibbles.at(0), 0x2)
        self.assertEqual(nibbles.at(1), 0x3)
        self.assertEqual(nibbles.at(2), 0x4)
        with self.assertRaises(IndexError):
            nibbles.at(3)

    def test_encode(self):
        nibbles = NibblePath([0x12, 0x34])
        self.assertEqual(nibbles.encode(False), b'\x00\x12\x34')
        self.assertEqual(nibbles.encode(True), b'\x20\x12\x34')

        nibbles = NibblePath([0x12, 0x34], offset=1)
        self.assertEqual(nibbles.encode(False), b'\x12\x34')
        self.assertEqual(nibbles.encode(True), b'\x32\x34')

    def test_common_prefix(self):
        nibbles_a = NibblePath([0x12, 0x34])
        nibbles_b = NibblePath([0x12, 0x56])
        common = nibbles_a.common_prefix(nibbles_b)
        self.assertEqual(common, NibblePath([0x12]))

        nibbles_a = NibblePath([0x12, 0x34])
        nibbles_b = NibblePath([0x12, 0x36])
        common = nibbles_a.common_prefix(nibbles_b)
        self.assertEqual(common, NibblePath([0x01, 0x23], offset=1))

        nibbles_a = NibblePath([0x12, 0x34], offset=1)
        nibbles_b = NibblePath([0x12, 0x56], offset=1)
        common = nibbles_a.common_prefix(nibbles_b)
        self.assertEqual(common, NibblePath([0x12], offset=1))

        nibbles_a = NibblePath([0x52, 0x34])
        nibbles_b = NibblePath([0x02, 0x56])
        common = nibbles_a.common_prefix(nibbles_b)
        self.assertEqual(common, NibblePath([]))

    def test_combine(self):
        nibbles_a = NibblePath([0x12, 0x34])
        nibbles_b = NibblePath([0x56, 0x78])
        common = nibbles_a.combine(nibbles_b)
        self.assertEqual(common, NibblePath([0x12, 0x34, 0x56, 0x78]))

        nibbles_a = NibblePath([0x12, 0x34], offset=1)
        nibbles_b = NibblePath([0x56, 0x78], offset=3)
        common = nibbles_a.combine(nibbles_b)
        self.assertEqual(common, NibblePath([0x23, 0x48]))


class TestNode(unittest.TestCase):
    def assertRoundtrip(self, raw_node, expected_type):
        decoded = Node.decode(raw_node)
        encoded = decoded.encode()

        self.assertEqual(type(decoded), expected_type)
        self.assertEqual(raw_node, encoded)

    def test_leaf(self):
        # Path 0xABC. 0x3_ at the beginning: 0x20 (for leaf type) + 0x10 (for odd len)
        nibbles_path = bytearray([0x3A, 0xBC])
        data = bytearray([0xDE, 0xAD, 0xBE, 0xEF])
        raw_node = rlp.encode([nibbles_path, data])
        self.assertRoundtrip(raw_node, Node.Leaf)


class TestMPT(unittest.TestCase):
    def test_insert_get_one_short(self):
        storage = {}
        trie = MerklePatriciaTrie(storage)

        key = rlp.encode(b'key')
        value = rlp.encode(b'value')
        trie.update(key, value)
        gotten_value = trie.get(key)

        self.assertEqual(value, gotten_value)

        with self.assertRaises(KeyError):
            trie.get(rlp.encode(b'no_key'))

    def test_insert_get_one_long(self):
        storage = {}
        trie = MerklePatriciaTrie(storage)

        key = rlp.encode(b'key_0000000000000000000000000000000000000000000000000000000000000000')
        value = rlp.encode(b'value_0000000000000000000000000000000000000000000000000000000000000000')
        trie.update(key, value)
        gotten_value = trie.get(key)

        self.assertEqual(value, gotten_value)

    def test_insert_get_many(self):
        storage = {}

        trie = MerklePatriciaTrie(storage)

        trie.update(b'do', b'verb')
        trie.update(b'dog', b'puppy')
        trie.update(b'doge', b'coin')
        trie.update(b'horse', b'stallion')

        self.assertEqual(trie.get(b'do'), b'verb')
        self.assertEqual(trie.get(b'dog'), b'puppy')
        self.assertEqual(trie.get(b'doge'), b'coin')
        self.assertEqual(trie.get(b'horse'), b'stallion')

    def test_insert_get_lots(self):
        random.seed(42)
        storage = {}
        rand_numbers = [random.randint(1, 1000000) for _ in range(100)]
        keys = list(map(lambda x: bytes('{}'.format(x), 'utf-8'), rand_numbers))

        trie = MerklePatriciaTrie(storage)

        for kv in keys:
            trie.update(kv, kv * 2)

        for kv in keys:
            self.assertEqual(trie.get(kv), kv * 2)

    def test_delete_one(self):
        storage = {}
        trie = MerklePatriciaTrie(storage)

        trie.update(b'key', b'value')
        trie.delete(b'key')

        with self.assertRaises(KeyError):
            trie.get(b'key')

    def test_delete_many(self):
        storage = {}

        trie = MerklePatriciaTrie(storage)

        trie.update(b'do', b'verb')
        trie.update(b'dog', b'puppy')
        trie.update(b'doge', b'coin')
        trie.update(b'horse', b'stallion')

        root_hash = trie.root_hash()

        trie.update(b'a', b'aaa')
        trie.update(b'some_key', b'some_value')
        trie.update(b'dodog', b'do_dog')

        trie.delete(b'a')
        trie.delete(b'some_key')
        trie.delete(b'dodog')

        new_root_hash = trie.root_hash()

        self.assertEqual(root_hash, new_root_hash)

    def test_delete_lots(self):
        random.seed(42)
        storage = {}
        rand_numbers = set([random.randint(1, 1000000) for _ in range(100)])  # Unique only.
        keys = list(map(lambda x: bytes('{}'.format(x), 'utf-8'), rand_numbers))

        trie = MerklePatriciaTrie(storage)

        for kv in keys:
            trie.update(kv, kv * 2)

        for kv in keys:
            trie.delete(kv)

        self.assertEqual(trie.root_hash(), Node.EMPTY_HASH)

    def test_root_hash(self):
        storage = {}

        trie = MerklePatriciaTrie(storage)

        trie.update(b'do', b'verb')
        trie.update(b'dog', b'puppy')
        trie.update(b'doge', b'coin')
        trie.update(b'horse', b'stallion')

        root_hash = trie.root_hash()

        self.assertEqual(root_hash, bytes.fromhex('5991bb8c6514148a29db676a14ac506cd2cd5775ace63c30a4fe457715e9ac84'))

    def test_root_hash_after_updates(self):
        storage = {}

        trie = MerklePatriciaTrie(storage)

        trie.update(b'do', b'verb')
        trie.update(b'dog', b'puppy1')
        trie.update(b'doge', b'coin1')
        trie.update(b'horse', b'stallion1')

        trie.update(b'dog', b'puppy')
        trie.update(b'doge', b'coin')
        trie.update(b'horse', b'stallion')

        root_hash = trie.root_hash()

        self.assertEqual(root_hash, bytes.fromhex('5991bb8c6514148a29db676a14ac506cd2cd5775ace63c30a4fe457715e9ac84'))

    def test_root_hash_after_deletes(self):
        storage = {}

        trie = MerklePatriciaTrie(storage)

        trie.update(b'do', b'verb')
        trie.update(b'dog', b'puppy')
        trie.update(b'doge', b'coin')
        trie.update(b'horse', b'stallion')

        trie.update(b'dodo', b'pizza')
        trie.update(b'hover', b'board')
        trie.update(b'capital', b'Moscow')
        trie.update(b'a', b'b')

        trie.delete(b'dodo')
        trie.delete(b'hover')
        trie.delete(b'capital')
        trie.delete(b'a')

        root_hash = trie.root_hash()

        self.assertEqual(root_hash, bytes.fromhex('5991bb8c6514148a29db676a14ac506cd2cd5775ace63c30a4fe457715e9ac84'))

    def test_trie_from_old_root(self):
        storage = {}

        trie = MerklePatriciaTrie(storage)

        trie.update(b'do', b'verb')
        trie.update(b'dog', b'puppy')

        root_hash = trie.root()

        trie.delete(b'dog')
        trie.update(b'do', b'not_a_verb')

        trie_from_old = MerklePatriciaTrie(storage, root_hash)

        # Old.
        self.assertEqual(trie_from_old.get(b'do'), b'verb')
        self.assertEqual(trie_from_old.get(b'dog'), b'puppy')

        # New.
        self.assertEqual(trie.get(b'do'), b'not_a_verb')
        with self.assertRaises(KeyError):
            trie.get(b'dog')
