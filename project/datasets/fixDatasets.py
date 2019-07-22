import os


def switch_label(path):
    with open(path, 'r') as file:
        lines = file.readlines()

    split = [[line.split()[0], int(line.split()[1])] for line in lines]
    with open(path, 'w') as file:
        for item in split:
            file.write(item[0] + ' ' + str((1 - item[1])) + '\n')


def label(path):
    with open(path + 'labels.txt', 'w') as labels:
        for root, directories, files in os.walk(path):
            for file in files:
                if '.jpg' in file or '.png' in file:
                    category = file[file.find('_')+1]
                    labels.write(file + ' ' + category + '\n')


def label_p(path):
    with open(path + 'labels.txt', 'w') as labels:
        for root, directories, files in os.walk(path):
            for file in files:
                if '.jpg' in file or '.png' in file:
                    category = 1 - int(file[file.find('_')+1])
                    labels.write(file + ' ' + str(category) + '\n')


datasets = [
            ('chessboard/symmetry/rot_images_diff1/labels.txt', switch_label),
            ('chessboard/symmetry/rot_images_diff5/labels.txt', switch_label),
            ('chessboard/similarity/camerarot_diff1/labels.txt', switch_label),
            ('chessboard/similarity/camerarot_diff5/labels.txt', switch_label),
            ('chessboard/similarity/camerarot_diff10/labels.txt', switch_label),
            ('chessboard/similarity/random_board_images_big_diff1/labels.txt', switch_label),
            ('chessboard/similarity/random_board_images_big_diff5/labels.txt', switch_label),
            ('chessboard/similarity/random_board_images_big_diff10/labels.txt', switch_label),
            ('svrt/results_problem_1/', label),
            ('svrt/results_problem_5/', label),
            ('svrt/results_problem_7/', label),
            ('svrt/results_problem_15/', label),
            ('svrt/results_problem_19/', label),
            ('svrt/results_problem_20/', label),
            ('svrt/results_problem_21/', label),
            ('svrt/results_problem_22/', label),
            ('psvrt/', label_p),
            ]

if __name__ == '__main__':

    for dataset, func in datasets:
        func(dataset)
