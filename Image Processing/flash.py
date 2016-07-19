from collections import Counter, deque
import math


# A class to define each of the possible goals/flashes
class Flash:
    def __init__(self, location, identity):

        # cached pattern
        self.cached_pattern = ("no pattern identified", 0)

        # raw bit rate
        self.raw_bits = []

        # set last_updated to an obscure value
        self.last_update = -1

        # initialize current flash location and identity
        self.x = location[0]
        self.y = location[1]
        self.identity = identity
        self.last_frame_count = 0

    def __str__(self):
        return str(self.identity) + ": location(" + str(self.x) + ", " + str(self.y) + ") pattern(" + self.pattern() + ") rawbitrate" + str(self.raw_bits)

    def __repr__(self):
        return self.__str__()

    def push_raw_bits(self, bit):
        if len(self.raw_bits) > 0:
            bits_missed = (self.last_update - self.last_frame_count)/5.0
            last_bit = self.raw_bits[-1]
            for count in range(int(round(bits_missed)) - 1):
                self.raw_bits.append(last_bit)
        self.last_frame_count = self.last_update
        self.raw_bits.append(bit)

    def pattern(self):
        if len(self.raw_bits) - self.cached_pattern[1] > 7:

            # split the raw bits into sub-lists of 8 bits each
            chunks = [pattern_to_binary(self.raw_bits[x:x + 8]) for x in xrange(0, len(self.raw_bits), 8) if len(pattern_to_binary(self.raw_bits[x:x + 8])) == 8]
            data = Counter(tuple(chunks))

            if len(data) > 0:
                self.cached_pattern = (str(data.most_common()[0][0]), len(self.raw_bits))
                return str(data.most_common()[0][0])
            return "no pattern identified"
        else:
            return self.cached_pattern[0]

    def distance_to(self, location):
        return math.sqrt((location[0] - self.x) ** 2 + (location[1] - self.y) ** 2)

    def equals_pattern(self, pattern):
        if self.pattern() != "no pattern identified":
            # print self.pattern()
            input_list = list(pattern)
            pattern_list = deque(self.pattern())
            for i in range(0, 8):
                pattern_list.rotate(1)
                if list(pattern_list) == input_list:
                    return True
        return False

    def update_location(self, location):
        self.x = location[0]
        self.y = location[1]


def pattern_to_binary(pattern):
    string_pattern = ""
    for i in pattern:
        string_pattern += ("1" if i > 100 else "0")
    return string_pattern
