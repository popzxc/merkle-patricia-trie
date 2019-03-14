class NibblePath:
    ODD_FLAG = 0x10
    LEAF_FLAG = 0x20

    def __init__(self, data, offset=0):
        self._data = data
        self._offset = offset

    def __len__(self):
        return len(self._data) * 2 - self._offset

    def __repr__(self):
        return "<NibblePath object with Data: {}, Offset: {}>".format(list(map(hex, self._data)), self._offset)

    def __eq__(self, other):
        if len(self) != len(other):
            return False

        for i in range(len(self)):
            if self.at(i) != other.at(i):
                return False

        return True

    def decode_with_type(data):
        is_odd_len = data[0] & NibblePath.ODD_FLAG == NibblePath.ODD_FLAG
        is_leaf = data[0] & NibblePath.LEAF_FLAG == NibblePath.LEAF_FLAG

        offset = 1 if is_odd_len else 2

        return NibblePath(data, offset), is_leaf

    def decode(data):
        return NibblePath.decode_with_type(data)[0]

    def starts_with(self, other):
        if len(other) > len(self):
            return False

        for i in range(len(other)):
            if self.at(i) != other.at(i):
                return False

        return True

    def consume(self, n_nibbles):
        self._offset += n_nibbles

    def at(self, idx):
        idx = idx + self._offset

        byte_idx = idx // 2
        nibble_idx = idx % 2

        byte = self._data[byte_idx]

        nibble = byte >> 4 if nibble_idx == 0 else byte & 0x0F

        return nibble

    def consume(self, amount):
        self._offset += amount
        return self

    def _create_new(path, length):
        bytes_len = (length + 1) / 2
        data = []

        is_odd_len = length % 2 == 1
        pos = 0

        if is_odd_len:
            data.append(path.at(pos))
            pos += 1

        while pos < length:
            data.append(path.at(pos) * 16 + path.at(pos + 1))
            pos += 2

        offset = 1 if is_odd_len else 0

        return NibblePath(data, offset)

    def common_prefix(self, other):
        least_len = min(len(self), len(other))
        common_len = 0
        for i in range(least_len):
            if self.at(i) != other.at(i):
                break
            common_len += 1

        return NibblePath._create_new(self, common_len)

    def encode(self, is_leaf):
        output = []

        nibbles_len = len(self)
        is_odd = nibbles_len % 2 == 1

        prefix = 0x00
        prefix += self.ODD_FLAG + self.at(0) if is_odd else 0x00
        prefix += self.LEAF_FLAG if is_leaf else 0x00

        output.append(prefix)

        pos = nibbles_len % 2

        while pos < nibbles_len:
            byte = self.at(pos) * 16 + self.at(pos + 1)
            output.append(byte)
            pos += 2

        return bytes(output)

    class _Chained:
        def __init__(self, first, second):
            self.first = first
            self.second = second

        def __len__(self):
            return len(self.first) + len(self.second)

        def at(self, idx):
            if idx < len(self.first):
                return self.first.at(idx)
            else:
                return self.second.at(idx - len(self.first))

    def combine(self, other):
        chained = NibblePath._Chained(self, other)
        return NibblePath._create_new(chained, len(chained))
