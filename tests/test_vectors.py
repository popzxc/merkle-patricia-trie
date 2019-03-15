import unittest
from mpt import MerklePatriciaTrie
from mpt.hash import keccak_hash
import os
import json

CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))
BASE_FOLDER = os.path.join(CURRENT_FOLDER, 'test_vectors')


def open_testvector(name):
    return open(os.path.join(BASE_FOLDER, name))


def normalize_value(v):
    if not v:
        return v

    if v.startswith('0x'):
        return bytes.fromhex(v[2:])
    else:
        return bytes(v, 'utf-8')


def normalize_kv(k, v):
    return normalize_value(k), normalize_value(v)


class TestVectors(unittest.TestCase):
    def run_testvector(self, name, secure):
        with open_testvector(name) as f:
            data = json.load(f)
            for test in data:
                input_data = data[test]['in']
                storage = {}
                trie = MerklePatriciaTrie(storage, secure=secure)

                data_samples = input_data if isinstance(input_data, list) else input_data.items()

                for k, v in data_samples:
                    k, v = normalize_kv(k, v)

                    if v:
                        trie.update(k, v)
                    else:
                        trie.delete(k)

                expected_root = normalize_value(data[test]['root'])
                self.assertEqual(trie.root_hash(), expected_root, msg='Test {} failed'.format(test))

    def test_hex_encoded_securetrie_test(self):
        test_vector_name = 'hex_encoded_securetrie_test.json'
        secure = True

        self.run_testvector(test_vector_name, secure)

    def test_trieanyorder(self):
        test_vector_name = 'trieanyorder.json'
        secure = False

        self.run_testvector(test_vector_name, secure)

    def test_trieanyorder_secureTrie(self):
        test_vector_name = 'trieanyorder_secureTrie.json'
        secure = True

        self.run_testvector(test_vector_name, secure)

    def test_trietest(self):
        test_vector_name = 'trietest.json'
        secure = False

        self.run_testvector(test_vector_name, secure)

    def test_trietest_secureTrie(self):
        test_vector_name = 'trietest_secureTrie.json'
        secure = True

        self.run_testvector(test_vector_name, secure)
