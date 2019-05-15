import os.path
import random
import sys
import time


class DatasetLoader:
    DATASETS_PATH = 'datasets/problem1/'

    @staticmethod
    def load_problem(path=DATASETS_PATH, shuffle=True):
        try:
            with open(path + 'labels.txt', 'r') as file:
                lines = file.readlines()

        except FileNotFoundError as fnfe:
            print(path + 'labels.txt does not exist')
            raise fnfe
        except Exception as exc:
            print("Unexpected error:", sys.exc_info()[0])
            raise exc

        splitted_lines = [[path + line.split()[0], int(line.split()[1])] for line in lines]

        # check if all files are present
        not_existing = []
        for index, line in enumerate(splitted_lines):
            if not os.path.isfile(line[0]):
                not_existing.append(index)

        if not_existing:
            print("Files that aren't available:")
            for index in not_existing:
                print(splitted_lines[index][0])

            splitted_lines = [line for index, line in enumerate(splitted_lines) if index not in not_existing]

        if shuffle:
            random.shuffle(splitted_lines)

        return splitted_lines

    @staticmethod
    def save_to_file(data):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        with open(timestamp + '.txt', 'w') as file:
            for line in data:
                file.write(str(line) + '\n')
