import os.path
import random
import sys

from datasets.Dataset import Dataset


class DatasetLoader:
    DATASETS_PATH = 'datasets/chessboard/similarity/camerarot_diff1/'

    @staticmethod
    def load_problem(path=DATASETS_PATH, number=50, balance=True):
        button1 = 'Category 1'
        button2 = 'Category 2'
        try:
            with open(path + 'labels.txt', 'r') as file:
                lines = file.readlines()

        except FileNotFoundError as fnfe:
            print(path + 'labels.txt does not exist')
            raise fnfe
        except Exception as exc:
            print("Unexpected error:", sys.exc_info()[0])
            raise exc

        if '[config]' in lines[0]:
            button1 = lines[1].split('=')[1].strip()
            button2 = lines[2].split('=')[1].strip()
            lines = lines[4:]

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

        if balance:
            set_false = [x for x in splitted_lines if x[1] == 0]
            set_true = [x for x in splitted_lines if x[1] == 1]
            random.shuffle(set_false)
            random.shuffle(set_true)
            half = int(number/2)
            splitted_lines = set_false[:half] + set_true[:half]

        random.shuffle(splitted_lines)

        return Dataset(splitted_lines, text1=button1, text2=button2)
