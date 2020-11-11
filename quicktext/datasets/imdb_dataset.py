import re
import tarfile
import urllib.request
from quicktext.imports import *

from quicktext.utils.data import load_from_directory, convert_to_x_y


def _download_imdb_dataset(dataset_dir):
    """
    Downloads IMDB dataset to target dir
    Args:
        dataset_dir (str): The folder where data will be stored
    Returns:
        None
    """

    target_dir = "imdb"

    if not os.path.exists(dataset_dir):
        os.mkdir(dataset_dir)

    download_url = "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"

    tar_dir = os.path.join(dataset_dir, f"{target_dir}.tar.gz")
    urllib.request.urlretrieve(download_url, tar_dir)

    tar_file = tarfile.open(tar_dir)
    tar_file.extractall(dataset_dir)
    tar_file.close()


def parse_aclimdb_dataset(target_dir):
    """
    The aclImdb dataset downloaded from stanford.edu has 
    an interesting directory structure. 

    The directory is of form
    aclImdb
        - train
            -neg
            -pos
        test
            -neg
            -pos
    
    The data will be read using data_from_directory from train and test folders
    
    Args:
        target_dir (str): Directory which contains train and test folder
    Returns:
        easydict: Contains both train and test files
    """

    labels = ["neg", "pos"]
    train_dir = os.path.join(target_dir, "train")
    test_dir = os.path.join(target_dir, "test")

    train_data = []
    train_target = []

    test_data = []
    test_target = []

    for idx, label in enumerate(labels):
        data = bulk_read_files(os.path.join(train_dir, label))
        train_data += [text.decode("utf-8") for text in data]
        train_target += [idx] * len(data)

        data = bulk_read_files(os.path.join(test_dir, label))
        test_data += [text.decode("utf-8") for text in data]
        test_target += [idx] * len(data)

    data = EasyDict(
        {
            "train": {"data": train_data, "target": train_target},
            "test": {"data": test_data, "target": test_target},
        }
    )

    return data


def bulk_read_files(target_dir):
    """
    Bulk reads files in target directory
    Args:
        target_dir: Directory whose files will be read
    Return:
        list: List of text
    """

    data = []

    for file in os.listdir(target_dir):
        text_file = open(os.path.join(target_dir, file), "rb")
        text = text_file.read()
        text_file.close()

        data.append(text)

    return data


def get_imdb(subset="train", shuffle=True, random_state=42, return_x_y=False):
    """
    Loads aclImdb dataset 
    This dataset has 25,000 samples in training and validation 
    And 25,000 samples for test
    Args:
        subset (str): The subset of data to return
        shuffle (boolean): Shuffles data if set to True
        random_state (int): Random state kept while splitting data into train val and test
        remove (list): List of metadata to remove from the 20newsgroups dataset
        return_x_y (bool): If True returns data in form (text, label)
    Returns:
        dict: With keys data, target, target_names
        or it could return a list of tuples of form (text, label)
    """

    dataset_dir = "qt_dataset"
    target_dir = os.path.join(dataset_dir, "aclImdb")

    _download_imdb_dataset(dataset_dir)

    imdb_data = parse_aclimdb_dataset(target_dir)

    if subset == "train":
        text = imdb_data.train.data
        target = imdb_data.train.target

        train_data, val_data, train_target, val_target = train_test_split(
            text, target, test_size=0.2, random_state=random_state
        )

        data = EasyDict(
            {
                "train": {"data": train_data, "target": train_target},
                "val": {"data": val_data, "target": val_target},
            }
        )

        if return_x_y:
            train_data = convert_to_x_y(data.train)
            val_data = convert_to_x_y(data.val)
            data = EasyDict({"train": {"data": train_data}, "val": {"data": val_data}})

    elif subset == "test":
        test_data = imdb_data.test.data
        test_target = imdb_data.test.target

        data = EasyDict({"test": {"data": test_data, "target": test_target}})

        if return_x_y:
            test_data = convert_to_x_y(data.test)
            data = EasyDict({"test": {"data": test_data}})

    else:
        print("No such subset exists")

    return data