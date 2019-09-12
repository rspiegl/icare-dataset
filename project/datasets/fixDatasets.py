import os


def switch_label(path):
    with open(path, 'r') as file:
        lines = file.readlines()

    split = [[line.split()[0], int(line.split()[1])] for line in lines]
    with open(path, 'w') as file:
        for item in split:
            file.write(item[0] + ' ' + str((1 - item[1])) + '\n')


def label_svrt(path):
    with open(path + 'labels.txt', 'w') as labels:
        for root, directories, files in os.walk(path):
            for file in files:
                if '.jpg' in file or '.png' in file:
                    category = file[file.find('_') + 1]
                    labels.write(file + ' ' + category + '\n')


def label_psvrt(path):
    with open(path + 'labels.txt', 'w') as labels:
        for root, directories, files in os.walk(path):
            for file in files:
                if '.jpg' in file or '.png' in file:
                    category = file[file.find('.') - 1]
                    labels.write(file + ' ' + category + '\n')


datasets = [
    ('chessboard/symmetry/rot_images_diff1/labels.txt', switch_label),
    ('chessboard/symmetry/rot_images_diff5/labels.txt', switch_label),
    ('chessboard/similarity/camerarot_diff1/labels.txt', switch_label),
    ('chessboard/similarity/camerarot_diff5/labels.txt', switch_label),
    ('chessboard/similarity/random_board_images_big_diff1/labels.txt', switch_label),
    ('chessboard/similarity/random_board_images_big_diff5/labels.txt', switch_label),
    ('svrt/results_problem_1/', label_svrt),
    ('svrt/results_problem_19/', label_svrt),
    ('svrt/results_problem_20/', label_svrt),
    ('svrt/results_problem_21/', label_svrt),
    ('psvrt/sd/', label_psvrt),
    ('psvrt/sr/', label_psvrt),
]

if __name__ == '__main__':

    to_fix = ['psvrt/sd/', 'psvrt/sr/']

    for dataset, func in datasets:
        if dataset in to_fix:
            func(dataset)
