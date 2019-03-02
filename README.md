# Modified Merkle Paticia Trie

MPT is the data structure used in [Ethereum](https://www.ethereum.org/) as a cryptographically authenticated key-value data storage. 

This library is a Python implementation of Modified Merkle Patrica Trie with a very simple interface.

## Example

```python
storage = {}
trie = MerklePatriciaTrie(storage)

trie.update(b'do', b'verb')
trie.update(b'dog', b'puppy')
trie.update(b'doge', b'coin')
trie.update(b'horse', b'stallion')

print("Root hash is {}".format(trie.root_hash().hex()))

print(trie.get(b'doge'))

trie.delete(b'doge')
```
