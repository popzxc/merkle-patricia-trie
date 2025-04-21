from Crypto.Hash import keccak  # noqa: S413


def keccak_hash(data: bytes) -> bytes:
    hasher = keccak.new(digest_bits=256)
    hasher.update(data)
    return hasher.digest()
