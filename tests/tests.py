import unittest
import mpt
import rlp


class TestNibblePath(unittest.TestCase):
    def test_at(self):
        nibbles = mpt.NibblePath([0x12, 0x34])
        self.assertEqual(nibbles.at(0), 0x1)
        self.assertEqual(nibbles.at(1), 0x2)
        self.assertEqual(nibbles.at(2), 0x3)
        self.assertEqual(nibbles.at(3), 0x4)

    def test_at_with_offset(self):
        nibbles = mpt.NibblePath([0x12, 0x34], offset=1)
        self.assertEqual(nibbles.at(0), 0x2)
        self.assertEqual(nibbles.at(1), 0x3)
        self.assertEqual(nibbles.at(2), 0x4)
        with self.assertRaises(IndexError):
            nibbles.at(3)

    def test_encode(self):
        nibbles = mpt.NibblePath([0x12, 0x34])
        self.assertEqual(nibbles.encode(False), b'\x00\x12\x34')
        self.assertEqual(nibbles.encode(True), b'\x20\x12\x34')

        nibbles = mpt.NibblePath([0x12, 0x34], offset=1)
        self.assertEqual(nibbles.encode(False), b'\x12\x34')
        self.assertEqual(nibbles.encode(True), b'\x32\x34')

    def test_common_prefix(self):
        nibbles_a = mpt.NibblePath([0x12, 0x34])
        nibbles_b = mpt.NibblePath([0x12, 0x56])
        common = nibbles_a.common_prefix(nibbles_b)
        self.assertEqual(common, mpt.NibblePath([0x12]))

        nibbles_a = mpt.NibblePath([0x12, 0x34])
        nibbles_b = mpt.NibblePath([0x12, 0x36])
        common = nibbles_a.common_prefix(nibbles_b)
        self.assertEqual(common, mpt.NibblePath([0x01, 0x23], offset=1))

        nibbles_a = mpt.NibblePath([0x12, 0x34], offset=1)
        nibbles_b = mpt.NibblePath([0x12, 0x56], offset=1)
        common = nibbles_a.common_prefix(nibbles_b)
        self.assertEqual(common, mpt.NibblePath([0x12], offset=1))

        nibbles_a = mpt.NibblePath([0x52, 0x34])
        nibbles_b = mpt.NibblePath([0x02, 0x56])
        common = nibbles_a.common_prefix(nibbles_b)
        self.assertEqual(common, mpt.NibblePath([]))

    def test_combine(self):
        nibbles_a = mpt.NibblePath([0x12, 0x34])
        nibbles_b = mpt.NibblePath([0x56, 0x78])
        common = nibbles_a.combine(nibbles_b)
        self.assertEqual(common, mpt.NibblePath([0x12, 0x34, 0x56, 0x78]))

        nibbles_a = mpt.NibblePath([0x12, 0x34], offset=1)
        nibbles_b = mpt.NibblePath([0x56, 0x78], offset=3)
        common = nibbles_a.combine(nibbles_b)
        self.assertEqual(common, mpt.NibblePath([0x23, 0x48]))


class TestNode(unittest.TestCase):
    def assertRoundtrip(self, raw_node, expected_type):
        decoded = mpt.Node.decode(raw_node)
        encoded = decoded.encode()

        self.assertEqual(type(decoded), expected_type)
        self.assertEqual(raw_node, encoded)

    def test_serde(self):
        # TODO test that serialization/deserialization is correct via hard-coded example.
        pass

    def test_leaf(self):
        # Path 0xABC. 0x3_ at the beginning: 0x20 (for leaf type) + 0x10 (for odd len)
        nibbles_path = bytearray([0x3A, 0xBC])
        data = bytearray([0xDE, 0xAD, 0xBE, 0xEF])
        raw_node = rlp.encode([nibbles_path, data])
        self.assertRoundtrip(raw_node, mpt.Node.Leaf)


class TestMPT(unittest.TestCase):
    def test_insert_get_one_short(self):
        storage = {}
        trie = mpt.MerklePatriciaTrie(storage)

        key = rlp.encode(b'key')
        value = rlp.encode(b'value')
        trie.update(key, value)
        gotten_value = trie.get(key)

        self.assertEqual(value, gotten_value)

        with self.assertRaises(KeyError):
            trie.get(rlp.encode(b'no_key'))

    def test_insert_get_one_long(self):
        storage = {}
        trie = mpt.MerklePatriciaTrie(storage)

        key = rlp.encode(b'key_0000000000000000000000000000000000000000000000000000000000000000')
        value = rlp.encode(b'value_0000000000000000000000000000000000000000000000000000000000000000')
        trie.update(key, value)
        gotten_value = trie.get(key)

        self.assertEqual(value, gotten_value)

    def test_insert_get_many(self):
        def v(value):
            return rlp.encode(value)

        storage = {}

        trie = mpt.MerklePatriciaTrie(storage)

        trie.update(b'do', b'verb')
        trie.update(b'dog', b'puppy')
        trie.update(b'doge', b'coin')
        trie.update(b'horse', b'stallion')

        self.assertEqual(trie.get(b'do'), b'verb')
        self.assertEqual(trie.get(b'dog'), b'puppy')
        self.assertEqual(trie.get(b'doge'), b'coin')
        self.assertEqual(trie.get(b'horse'), b'stallion')
