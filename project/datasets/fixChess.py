def relabel(path):
    with open(path, 'r') as file:
        lines = file.readlines()

    split = [[line.split()[0], int(line.split()[1])] for line in lines]
    with open(path, 'w') as file:
        for item in split:
            file.write(item[0] + ' ' + str((1 - item[1])) + '\n')


if __name__ == '__main__':
    datasets = ['camerarot_diff1/labels.txt',
                'camerarot_diff5/labels.txt',
                'camerarot_diff10/labels.txt',
                'random_board_images_big_diff1/labels.txt',
                'random_board_images_big_diff5/labels.txt',
                'random_board_images_big_diff10/labels.txt',
                'rot_images_diff1/labels.txt',
                'rot_images_diff5/labels.txt',
                'rot_images_diff10/labels.txt',]

    for dataset in datasets:
        relabel(dataset)
