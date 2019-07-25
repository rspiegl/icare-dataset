import math


class GazePoint:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def get(self):
        middle = ((self.left[0] + self.right[0])/2.0, (self.left[1] + self.right[1])/2.0)
        return middle

    def has_nan(self):
        return math.isnan(self.left[0] + self.left[1] + self.right[0] + self.right[1])

    def __str__(self):
        return "{} {}".format(self.left, self.right)

    def __repr__(self):
        return self.__str__()
