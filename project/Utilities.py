import glob
import random
import time


class DatasetLoader:

    DATASETS_PATH = 'datasets/problem1/'

    @staticmethod
    def load_problem1(shuff=True):
        images_false = [[f, False] for f in glob.glob(DatasetLoader.DATASETS_PATH + '*_0_*.png')]
        images_true = [[f, True] for f in glob.glob(DatasetLoader.DATASETS_PATH + '*_1_*.png')]
        images = images_false + images_true

        if shuff:
            random.shuffle(images)

        return images

    @staticmethod
    def save_to_file(data):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

        with open(timestamp+'.txt', 'w') as file:
            for line in data:
                file.write(str(line) + '\n')
