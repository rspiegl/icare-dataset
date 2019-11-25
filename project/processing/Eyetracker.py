import math


class GazePoint:
    def __init__(self, left, right, timestamp=None):
        self.left = left
        self.right = right
        self.timestamp = timestamp

    def get(self):
        if math.isnan(self.left[0]):
            middle = self.right
        elif math.isnan(self.right[0]):
            middle = self.left
        else:
            middle = ((self.left[0] + self.right[0]) // 2, (self.left[1] + self.right[1]) // 2)
        return middle

    def is_nan(self):
        return (math.isnan(self.left[0]) and
                math.isnan(self.left[1]) and
                math.isnan(self.right[0]) and
                math.isnan(self.left[1]))

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'x': self.get()[0],
            'y': self.get()[1],
            'left_x': self.left[0],
            'left_y': self.left[1],
            'right_x': self.right[0],
            'right_y': self.right[1]
        }

    def __str__(self):
        return "{} {} {}".format(self.timestamp, self.left, self.right)

    def __repr__(self):
        return self.__str__()
