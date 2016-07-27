from collections import Counter, deque
import math


# A class to define each of the possible goals/flashes
class Flash:

    current_identity = 0

    def __init__(self, location):

        # cached pattern
        self.cached_pattern = ("no pattern identified", 0)

        # raw bit rate
        self.raw_bits = []

        # set last_updated to an obscure value
        self.last_update = -1

        # initialize current flash location and identity
        self.x = location[0]
        self.y = location[1]
        self.identity = Flash.current_identity
        self.last_frame_count = 0

        # cache pattern tracking
        self.pattern_cache = 0
        self.count = 0

        # update Flash class identity
        Flash.current_identity += 1

        self.pattern_count = {}

    def __str__(self):
        return str(self.identity) + ": location(" + str(self.x) + ", " + str(self.y) + ") pattern(TEST" + ") rawbitrate" + str(self.raw_bits)

    def __repr__(self):
        return self.__str__()

    def push_raw_bits(self, bit, pixelIntensity):
        if len(self.raw_bits) > 0:
            bits_missed = (self.last_update - self.last_frame_count)/5.0
            last_bit = self.raw_bits[-1]
            for count in range(int(round(bits_missed)) - 1):
                # self.raw_bits.append(last_bit)
                self.raw_bits.append(0 if last_bit > pixelIntensity else 1)
        self.last_frame_count = self.last_update
        #self.raw_bits.append(bit)
        self.raw_bits.append(0 if bit > pixelIntensity else 1)

    def distance_to(self, location):
        return math.sqrt((location[0] - self.x) ** 2 + (location[1] - self.y) ** 2)

    def equals_pattern(self, pattern):

        for x in range(self.pattern_cache, len(self.raw_bits) - 8):
            print self.raw_bits[x: x + 8]
            if Flash.cyclic_equivalence(self.raw_bits[x: x + 8], map(int, list(pattern))):
                self.count += 1

        self.pattern_cache = len(self.raw_bits) - 8

        # TODO: change count limit dynamically
        return True if self.count > 10 else False

    @staticmethod
    def cyclic_equivalence(a, b):

        n, i, j = len(a), 0, 0
        if n != len(b):
            return False
        while i < n and j < n:
            k = 1
            while k <= n and a[(i + k) % n] == b[(j + k) % n]:
                k += 1
            if k > n:
                return True
            if a[(i + k) % n] > b[(j + k) % n]:
                i += k
            else:
                j += k
        return False

    def update_location(self, location):
        self.x = location[0]
        self.y = location[1]


