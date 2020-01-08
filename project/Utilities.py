import glob
import os.path
import random
import sys
from enum import Enum

from datasets.Dataset import Dataset

CUSTOM_EVAL_NAN = {'nan': float('nan')}


class RawDataVersion(Enum):
    TESTCALIBRATION = 1
    TRIALCALIBRATION = 2


class DatasetLoader:
    DATASET_CAMROT = 'datasets/chessboard/similarity/camerarot_diff%s/'
    DATASET_RANBOA = 'datasets/chessboard/similarity/random_board_images_big_diff%s/'
    DATASET_ROTIMA = 'datasets/chessboard/symmetry/rot_images_diff%s/'
    DATASET_SVRT = 'datasets/svrt/results_problem_%s/'
    DATASET_CATDOG = 'datasets/catdog/'
    PSVRT_SAME_H = 'datasets/psvrt/same/horizontal/'
    PSVRT_SAME_V = 'datasets/psvrt/same/vertical/'
    PSVRT_DIFF_H = 'datasets/psvrt/diff/horizontal/'
    PSVRT_DIFF_V = 'datasets/psvrt/diff/vertical/'
    PSVRT = {'sd': [[PSVRT_SAME_H, 1], [PSVRT_SAME_V, 1], [PSVRT_DIFF_H, 0], [PSVRT_DIFF_V, 0]],
             'sr': [[PSVRT_SAME_V, 1], [PSVRT_DIFF_V, 1], [PSVRT_SAME_H, 0], [PSVRT_DIFF_H, 0]]}

    IDENTIFIER_CAMROT = 'camrot'
    IDENTIFIER_RANBOA = 'ranboa'
    IDENTIFIER_ROTIMA = 'rotima'
    IDENTIFIER_SVRT = 'svrt'
    IDENTIFIER_PSVRT = 'psvrt'

    CALIBRATE_PICTURE = 'datasets/calibrate_point.png'

    @staticmethod
    def get_dataset_path(identifier='camrot', specifier=1):
        if identifier is DatasetLoader.IDENTIFIER_CAMROT:
            if specifier not in [1, 5]:
                raise Exception("Wrong number for dataset camerarot.")
            path = DatasetLoader.DATASET_CAMROT % specifier

        elif identifier is DatasetLoader.IDENTIFIER_RANBOA:
            if specifier not in [1, 5]:
                raise Exception("Wrong number for dataset random_board.")
            path = DatasetLoader.DATASET_RANBOA % specifier

        elif identifier is DatasetLoader.IDENTIFIER_ROTIMA:
            if specifier not in [1, 5]:
                raise Exception("Wrong number for dataset rot_images.")
            path = DatasetLoader.DATASET_ROTIMA % specifier

        elif identifier is DatasetLoader.IDENTIFIER_SVRT:
            if specifier not in [1, 19, 20, 21]:
                raise Exception("Wrong number for dataset svrt.")
            path = DatasetLoader.DATASET_SVRT % specifier

        elif identifier is DatasetLoader.IDENTIFIER_PSVRT:
            if specifier not in ['sd', 'sr']:
                raise Exception("Wrong identifier for dataset psvrt.")
            path = specifier
        else:
            raise Exception("Wrong dataset identifier.")

        return path

    @staticmethod
    def load_problem(path=(DATASET_CAMROT % 1), number=35, balance=True):
        if path in ['sd', 'sr']:
            return DatasetLoader._load_psvrt(path, number)

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
            half = int((number + 1) / 2)
            splitted_lines = set_false[:half] + set_true[:half]

        random.shuffle(splitted_lines)

        if number % 2 == 1:
            del splitted_lines[-1]

        return Dataset(splitted_lines, text1=button1, text2=button2)

    @staticmethod
    def _load_psvrt(type='sd', number=35):
        samples = []
        data_lines = []
        if number % 4 == 0:
            samples = [number//4]*4
        else:
            q, r = divmod(number, 4)
            samples = [q + 1] * r + [q] * (4 - r)

        for index, (dirpath, val) in enumerate(DatasetLoader.PSVRT[type]):
            files = glob.glob(dirpath + '*.png')
            random.shuffle(files)
            files = files[:samples[index]]
            data_lines += [[f, val] for f in files]

        random.shuffle(data_lines)

        return Dataset(data_lines)


def list_files(path):
    return glob.glob(path)


def read_dic(file):
    with open(file, 'r') as f:
        dic = eval(f.read(), CUSTOM_EVAL_NAN)
    return dic
