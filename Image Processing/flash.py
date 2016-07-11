from collections import Counter


# A class to define each of the possible goals/flashes
class Flash:

    # TODO: pass in matrix/planar coordinates of flash location
    def __init__(self):

        # processed bit patterns
        self.patterns = []

        # raw bit rate
        self.raw_bit_rate = []


    def push_raw_bits(self, bit):
        self.raw_bit_rate.append(bit)

    def add_pattern(self, pattern):
        self.patterns.append(self.__pattern_to_binary(pattern))

    def get_pattern(self):
        pattern_data = Counter(tuple(self.patterns))
        most_common_pattern = pattern_data.most_common(1)

        if len(most_common_pattern) > 0:
            return most_common_pattern[0][0]
        return ""

    def __pattern_to_binary(self, pattern):
        string_pattern = ""
        for i in pattern:
            string_pattern += ("1" if i is not 0 else "0")
        return string_pattern