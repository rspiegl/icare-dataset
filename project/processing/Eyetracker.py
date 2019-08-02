import math


class GazePoint:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def get(self):
        if math.isnan(self.left[0]):
            middle = self.right
        elif math.isnan(self.right[0]):
            middle = self.left
        else:
            middle = ((self.left[0] + self.right[0])//2, (self.left[1] + self.right[1])//2)
        return middle

    def is_nan(self):
        return (math.isnan(self.left[0]) and
                math.isnan(self.left[1]) and
                math.isnan(self.right[0]) and
                math.isnan(self.left[1]))

    def __str__(self):
        return "{} {}".format(self.left, self.right)

    def __repr__(self):
        return self.__str__()
