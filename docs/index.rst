Welcome to Merkle Patricia Trie's documentation!
================================================

MPT is the data structure used in `Ethereum`_ as a cryptographically authenticated key-value data storage. 

This library is a Python implementation of Modified Merkle Patrica Trie with a very simple interface.

.. _Ethereum: https://www.ethereum.org/

Example
-------

::

    storage = {}
    trie = MerklePatriciaTrie(storage)

    trie.update(b'do', b'verb')
    trie.update(b'dog', b'puppy')
    trie.update(b'doge', b'coin')
    trie.update(b'horse', b'stallion')

    old_root = trie.root()
    old_root_hash = trie.root_hash()

    print("Root hash is {}".format(old_root_hash.hex()))

    trie.delete(b'doge')

    print("New root hash is {}".format(trie.root_hash().hex()))

    trie_from_old_hash = MerklePatriciaTrie(storage, root=old_root)

    print(trie_from_old_hash.get(b'doge'))

    try:
        print(trie.get(b'doge'))
    except KeyError:
        print('Not accessible in a new trie.')

.. toctree::
   :maxdepth: 2
   :caption: API documentation:

   modules


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
