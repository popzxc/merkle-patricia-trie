class NibblePath:
    ODD_FLAG = 0x10
    LEAF_FLAG = 0x20

    def __init__(self, data, offset=0):
        self._data = data
        self._offset = offset

    def __len__(self):
        return len(self._data) * 2 - self._offset

    def __repr__(self):
        return f'<NibblePath: Data: 0x{self._data.hex()}, Offset: {self._offset}>'

    def __str__(self):
        return f'<Hex 0x{self._data.hex()} | Raw {self._data}>'

    def __eq__(self, other):
        if not isinstance(other, NibblePath):
            return NotImplemented

        if len(self) != len(other):
            return False

        return all(self.at(i) == other.at(i) for i in range(len(self)))

    def __getitem__(self, idx):
        return self.at(idx)

    def __hash__(self):
        return hash((self._data, self._offset))

    def next(self):
        first = self[0]
        self.consume(1)
        return first

    @classmethod
    def decode_with_type(cls, data):
        """Decodes NibblePath and its type from raw bytes."""
        is_odd_len = data[0] & cls.ODD_FLAG == cls.ODD_FLAG
        is_leaf = data[0] & cls.LEAF_FLAG == cls.LEAF_FLAG

        offset = 1 if is_odd_len else 2

        return cls(data, offset), is_leaf

    @classmethod
    def decode(cls, data):
        """Decodes NibblePath without its type from raw bytes."""
        return cls.decode_with_type(data)[0]

    def starts_with(self, other):
        """Checks if `other` is prefix of `self`."""
        if len(other) > len(self):
            return False

        return all(self.at(i) == other.at(i) for i in range(len(other)))

    def at(self, idx):
        """Returns nibble at the certain position."""
        idx += self._offset

        byte_idx = idx // 2
        nibble_idx = idx % 2

        byte = self._data[byte_idx]
        return byte >> 4 if nibble_idx == 0 else byte & 0x0F

    def consume(self, amount):
        """Cuts off nibbles at the beginning of the path."""
        self._offset += amount
        return self

    @classmethod
    def _create_new(cls, path, length):
        """Creates a new NibblePath from a given object with a certain length."""
        is_odd_len = length % 2 == 1
        pos, data = 0, []

        if is_odd_len:
            data.append(path.at(pos))
            pos += 1

        while pos < length:
            data.append(path.at(pos) * 16 + path.at(pos + 1))
            pos += 2

        offset = 1 if is_odd_len else 0

        return cls(data, offset)

    def common_prefix(self, other):
        """Returns common part at the beginning of both paths."""
        least_len = min(len(self), len(other))
        common_len = next(
            (i for i in range(least_len) if self.at(i) != other.at(i)), least_len
        )

        return NibblePath._create_new(self, common_len)

    def encode(self, is_leaf):
        """Encode NibblePath into bytes.

        Encoded path contains prefix with flags of type and length and also may contain
        a padding nibble so the length of encoded path is always even.
        """
        nibbles_len = len(self)
        is_odd = nibbles_len % 2 == 1

        prefix = (
            0x00
            + (self.ODD_FLAG + self.at(0) if is_odd else 0x00)
            + (self.LEAF_FLAG if is_leaf else 0x00)
        )
        output = [prefix]

        pos = nibbles_len % 2
        while pos < nibbles_len:
            byte = self.at(pos) * 16 + self.at(pos + 1)
            output.append(byte)
            pos += 2

        return bytes(output)

    class _Chained:
        """Class that chains two paths."""

        def __init__(self, first, second):
            self.first = first
            self.second = second

        def __len__(self):
            return len(self.first) + len(self.second)

        def at(self, idx):
            if idx < len(self.first):
                return self.first.at(idx)
            return self.second.at(idx - len(self.first))

    def combine(self, other):
        """Merges two paths into one."""
        chained = NibblePath._Chained(self, other)
        return NibblePath._create_new(chained, len(chained))
