class Dataset:

    def __init__(self, data, text1, text2, description):
        self.data = data
        self.text1 = text1
        self.text2 = text2
        self.description = description

    def __str__(self):
        return self.__repr__

    def __repr__(self):
        return '[%s, %s, %s, %s]' % (self.description, self.text1, self.text2, self.data)


