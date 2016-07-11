from collections import Counter, deque
import math


# A class to define each of the possible goals/flashes
class Flash:
    def __init__(self, location, identity):

        # cached pattern
        self.cached_pattern = ("no pattern identified", 0)

        # raw bit rate
        self.raw_bit_rate = []

        # initialize current flash location and identity
        self.x = location[0]
        self.y = location[1]
        self.identity = identity

    def __str__(self):
        return str(self.pattern)

    def __repr__(self):
        return str(self.pattern)

    def push_raw_bits(self, bit):
        self.raw_bit_rate.append(bit)

    @property
    def pattern(self):
        if len(self.raw_bit_rate) - self.cached_pattern[1] > 7:

            chunks = [pattern_to_binary(self.raw_bit_rate[x:x + 8]) for x in xrange(0, len(self.raw_bit_rate), 8)]
            if len(chunks[-1]) != 8:
                del chunks[-1]
            data = Counter(tuple(chunks))

            if len(data) > 0:
                self.cached_pattern = (str(data.most_common()[0][0]), len(self.raw_bit_rate))
                return str(data.most_common()[0][0])
            return "no pattern identified"
        else:
            return self.cached_pattern[0]

    def distance_to(self, location):
        return math.sqrt((location[0] - self.x) ** 2 + (location[1] - self.y) ** 2)

    def equals_pattern(self, pattern):
        if self.pattern != "no pattern identified":
            input_list = list(pattern)
            pattern_list = deque(self.pattern)
            for i in range(0, 8):
                pattern_list.rotate(1)
                if list(pattern_list) == input_list:
                    return True
        return False


def pattern_to_binary(pattern):
    string_pattern = ""
    for i in pattern:
        string_pattern += ("1" if i != 0 and i != "0" else "0")
    return string_pattern
