import torch
import torch.utils.data as data
import os
import matplotlib.pyplot as plt
import numpy as np
from augmentations.transforms import Denormalize
import albumentations as A
import cv2
import csv


class CassavaDataset(data.Dataset):
    """
    Reads a folder of images
    """

    def __init__(self, config, csv_file, img_dir, transforms=None):

        self.config = config
        self.dir = img_dir
        self.df = csv_file
        self.transforms = transforms
        self.fns = self.load_images()
        self.labels = self.df['label']
        self.num_classes = len(self.labels.unique().tolist())
        self.classes = self.labels.unique().tolist()

    def load_images(self):
        with open(self.config.train_csv, 'r') as f:
            data_list = list(csv.reader(f))

        return data_list[1:]

    def __getitem__(self, index):
        img_path, label = self.fns[index]
        img_path = os.path.join(self.dir, img_path)
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.uint8)

        if self.transforms:
            item = self.transforms(image=img)
            img = item['image']
        label = torch.LongTensor([int(label)])

        return {
            "img": img,
            "target": label}

    def count_dict(self):
        cnt_dict = {}
        labels = self.labels.unique().tolist()
        label_list = self.labels.tolist()
        for i in labels:
            freq = 0
            for j in label_list:
                if i == j:
                    freq += 1
            cnt_dict[i] = freq
        return cnt_dict

    def visualize_item(self, index=None, figsize=(15, 15)):
        """
        Visualize an image with its bouding boxes by index
        """

        if index is None:
            index = np.random.randint(0, len(self.fns))
        item = self.__getitem__(index)
        img = item['img']
        label = item['target']

        # Denormalize and reverse-tensorize
        normalize = False
        if self.transforms is not None:
            for x in self.transforms.transforms:
                if isinstance(x, A.Normalize):
                    normalize = True
                    denormalize = Denormalize(mean=x.mean, std=x.std)

        # Denormalize and reverse-tensorize
        if normalize:
            img = denormalize(img=img)

        label = label.numpy().item()
        self.visualize(img, label, figsize=figsize)

    def visualize(self, img, label, figsize=(15, 15)):
        """
        Visualize an image with its bouding boxes
        """
        fig, ax = plt.subplots(figsize=figsize)

        # Display the image
        ax.imshow(img)
        plt.title(self.classes[int(label)])
        plt.show()

    def plot(self, figsize=(8, 8), types=["freqs"]):

        ax = plt.figure(figsize=figsize)

        if "freqs" in types:
            cnt_dict = self.count_dict()
            plt.title("Classes Distribution")
            bar1 = plt.bar(list(cnt_dict.keys()), list(cnt_dict.values()), color=[
                           np.random.rand(3,) for i in range(len(self.classes))])
            for rect in bar1:
                height = rect.get_height()
                plt.text(rect.get_x() + rect.get_width()/2.0, height,
                         '%d' % int(height), ha='center', va='bottom')

        plt.show()

    def __len__(self):
        return len(self.fns)

    def __str__(self):
        s1 = "Number of samples: " + str(len(self.fns)) + '\n'
        s2 = "Number of classes: " + str(len(self.classes)) + '\n'
        return s1 + s2

    def collate_fn(self, batch):
        """
         - Note: this need not be defined in this Class, can be standalone.
            + param batch: an iterable of N sets from __getitem__()
            + return: a tensor of images, lists of  labels
        """

        images = torch.stack([b['img'] for b in batch], dim=0)
        labels = torch.LongTensor([b['target'] for b in batch])

        return {
            'imgs': images,
            'targets': labels}
