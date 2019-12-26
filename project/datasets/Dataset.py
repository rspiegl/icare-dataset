class Dataset:

    def __init__(self, data, text1='Category 1', text2='Category 2'):
        self.data = data
        self.text1 = text1
        self.text2 = text2

    def __str__(self):
        return self.__repr__

    def __repr__(self):
        return '[%s, %s, %s]' % (self.text1, self.text2, self.data)
