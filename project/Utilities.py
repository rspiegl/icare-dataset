import random
import sys
import time


class DatasetLoader:
    DATASETS_PATH = 'datasets/problem1/'

    @staticmethod
    def load_problem(path=DATASETS_PATH, shuffle=True):
        try:
            file = open(path + 'labels.txt', 'r')
        except FileNotFoundError as fnfe:
            print(path + 'labels.txt does not exist')
            raise fnfe
        except Exception as exc:
            print("Unexpected error:", sys.exc_info()[0])
            raise exc

        lines = file.readlines()
        images = [[path + item.split()[0], int(item.split()[1])] for item in lines]

        if shuffle:
            random.shuffle(images)

        return images

    @staticmethod
    def save_to_file(data):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        with open(timestamp + '.txt', 'w') as file:
            for line in data:
                file.write(str(line) + '\n')
