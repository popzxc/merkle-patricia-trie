from Crypto.Hash import keccak


def hash(data):
    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(data)
    return keccak_hash.digest()


def hex_hash(data):
    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(data)
    return keccak_hash.hexdigest()
