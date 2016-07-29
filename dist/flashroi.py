import math


class FlashROI:
    """ Flash class that defines each possible flash object """

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
        self.identity = FlashROI.current_identity
        self.last_frame_count = 0

        # cache pattern tracking
        self.pattern_cache = 0
        self.patterns_found = 0

        # update Flash class identity
        FlashROI.current_identity += 1

        self.pattern_count = {}

    def __repr__(self):
        return str(self.identity) + ": location(" + str(self.x) + ", " + str(self.y) + ") rawbitrate" + str(self.raw_bits)

    def push_raw_bits(self, bit, pixel_intensity):
        if len(self.raw_bits) > 0:
            bits_missed = (self.last_update - self.last_frame_count)/5.0
            last_bit = self.raw_bits[-1]
            for count in range(int(round(bits_missed)) - 1):
                self.raw_bits.append(0 if last_bit > pixel_intensity else 1)
        self.last_frame_count = self.last_update
        self.raw_bits.append(0 if bit > pixel_intensity else 1)

    def distance_to(self, location):
        return math.sqrt((location[0] - self.x) ** 2 + (location[1] - self.y) ** 2)

    def equals_pattern(self, pattern, limit):

        for x in range(self.pattern_cache, len(self.raw_bits) - 8):
            if FlashROI.cyclic_equivalence(self.raw_bits[x: x + 8], map(int, list(pattern))):
                self.patterns_found += 1

        self.pattern_cache = len(self.raw_bits) - 8

        # TODO: change count limit dynamically
        return True if self.patterns_found > limit else False

    def update_location(self, location):
        self.x = location[0]
        self.y = location[1]

    @staticmethod
    def cyclic_equivalence(a, b):
        """ Algorithm of cyclic equivalence used to determine whether 2 lists are rotated versions of each other

        Args:
            a:
            b:

        Returns:

        """

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
