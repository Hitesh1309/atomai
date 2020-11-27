"""
preproc.py
======

Helper functions for prerocessing training/validation data.

Created by Maxim Ziatdinov (email: maxim.ziatdinov@ai4microscopy.com)
"""

from typing import Tuple, Optional, Union, List, Type
import warnings
import numpy as np
import torch


def num_classes_from_labels(labels: np.ndarray) -> int:
    """
    Gets number of classes from labels (aka ground truth aka masks)

    Args:
        labels (numpy array):
            ground truth (aka masks aka labels) for semantic segmentation
    
    Returns:
        number of classes
    """
    uval = np.unique(labels)
    if min(uval) != 0:
        raise AssertionError("Labels should start from 0")
    for i, j in zip(uval, uval[1:]):
        if j - i != 1:
            raise AssertionError("Mask values should be in range between "
                                 "0 and total number of classes "
                                 "with an increment of 1")
    num_classes = len(uval)
    if num_classes == 2:
        num_classes = num_classes - 1
    return num_classes


def check_image_dims(X_train: np.ndarray,
                     y_train: np.ndarray,
                     X_test: np.ndarray,
                     y_test: np.ndarray,
                     num_classes: int
                     ) -> Tuple[np.ndarray]:
    """
    Adds if necessary pseudo-dimension of 1 (channel dimensions)
    to images and masks
    """
    if X_train.ndim == 3:
        warnings.warn(
            'Adding a channel dimension of 1 to training images',
            UserWarning)
        X_train = X_train[:, np.newaxis]
    if X_test.ndim == 3:
        warnings.warn(
            'Adding a channel dimension of 1 to test images',
            UserWarning)
        X_test = X_test[:, np.newaxis]
    if num_classes == 1 and y_train.ndim == 3:
        warnings.warn(
            'Adding a channel dimension of 1 to training labels',
            UserWarning)
        y_train = y_train[:, np.newaxis]
    if num_classes == 1 and y_test.ndim == 3:
        warnings.warn(
            'Adding a channel dimension of 1 to test labels',
            UserWarning)
        y_test = y_test[:, np.newaxis]

    return X_train, y_train, X_test, y_test


def check_signal_dims(X_train: np.ndarray,
                      y_train: np.ndarray,
                      X_test: np.ndarray,
                      y_test: np.ndarray) -> Tuple[np.ndarray]:
    """
    Adds if necessary a pseudo-dimension of 1 (channel dimensions)
    to images and spectra
    """
    if X_train.ndim > y_train.ndim:
        if X_train.ndim == 3:
            warnings.warn(
                'Adding a channel dimension of 1 to training images',
                UserWarning)
            X_train = np.expand_dims(X_train, axis=1)
        if X_test.ndim == 3:
            warnings.warn(
                'Adding a channel dimension of 1 to test images',
                UserWarning)
            X_test = np.expand_dims(X_test, axis=1)
        if y_train.ndim == 2:
            warnings.warn(
                'Adding a channel dimension of 1 to training spectra',
                UserWarning)
            y_train = np.expand_dims(y_train, axis=1)
        if y_test.ndim == 2:
            warnings.warn(
                'Adding a channel dimension of 1 to test spectra',
                UserWarning)
            y_test = np.expand_dims(y_test, axis=1)

    elif X_train.ndim < y_train.ndim:
        if X_train.ndim == 2:
            warnings.warn(
                'Adding a channel dimension of 1 to training images',
                UserWarning)
            X_train = np.expand_dims(X_train, axis=1)
        if X_test.ndim == 2:
            warnings.warn(
                'Adding a channel dimension of 1 to test images',
                UserWarning)
            X_test = np.expand_dims(X_test, axis=1)
        if y_train.ndim == 3:
            warnings.warn(
                'Adding a channel dimension of 1 to training spectra',
                UserWarning)
            y_train = np.expand_dims(y_train, axis=1)
        if y_test.ndim == 3:
            warnings.warn(
                'Adding a channel dimension of 1 to test spectra',
                UserWarning)
            y_test = np.expand_dims(y_test, axis=1)

    return X_train, y_train, X_test, y_test


def ndarray2list(X_train: np.ndarray, y_train: np.ndarray,
                 X_test: np.ndarray, y_test: np.ndarray,
                 batch_size: int) -> Tuple[List[np.ndarray]]:
    """
    Splits train and test ndarrays arrays into lists of ndarrays of
    a specified size. The remainders are not included.
    """
    n_train_batches, _ = np.divmod(X_train.shape[0], batch_size)
    n_test_batches, _ = np.divmod(X_test.shape[0], batch_size)
    X_train = np.split(
        X_train[:n_train_batches*batch_size], n_train_batches)
    y_train = np.split(
        y_train[:n_train_batches*batch_size], n_train_batches)
    X_test = np.split(
        X_test[:n_test_batches*batch_size], n_test_batches)
    y_test = np.split(
        y_test[:n_test_batches*batch_size], n_test_batches)
    return X_train, y_train, X_test, y_test


def preprocess_training_image_data(images_all: np.ndarray,
                                   labels_all: np.ndarray,
                                   images_test_all: np.ndarray,
                                   labels_test_all: np.ndarray,
                                   batch_size: int
                                   ) -> Tuple[List[np.ndarray], int]:
    """
    Preprocess training and test data

    Args:
        images_all (numpy array):
            4D numpy array (3D image tensors stacked along the first dim)
            representing training images
        labels_all (numpy array):
            4D (binary) / 3D (multiclass) numpy array
            where 3D / 2D images stacked along the first array dimension
            represent training labels (aka masks aka ground truth)
        images_test_all (numpy array):
            4D numpy array (3D image tensors stacked along the first dim)
            representing test images
        labels_test_all (numpy array):
            4D (binary) / 3D (multiclass) numpy array
            where 3D / 2D images stacked along the first array dimension
            represent test labels (aka masks aka ground truth)
        batch_size (int):
            Size of training and test batches

    Returns:
        5-element tuple containing lists of numpy arrays with
        training and test data, and an integer corresponding to
        the number of classes inferred from the data.
    """
    all_data = (images_all, labels_all, images_test_all, labels_test_all)
    if not all([isinstance(i, np.ndarray) for i in all_data]):
        raise TypeError(
            "Provide training and test data in the form of numpy arrays")
    num_classes = num_classes_from_labels(labels_all)
    (images_all, labels_all,
     images_test_all, labels_test_all) = check_image_dims(*all_data, num_classes)
    images_all, labels_all, images_test_all, labels_test_all = ndarray2list(
        images_all, labels_all, images_test_all, labels_test_all, batch_size)

    return (images_all, labels_all, images_test_all,
            labels_test_all, num_classes)


def init_fcnn_dataloaders(X_train: np.ndarray,
                          y_train: np.ndarray,
                          X_test: np.ndarray,
                          y_test: np.ndarray,
                          batch_size: int,
                          num_classes: Optional[int] = None,
                          ) -> Tuple[Type[torch.utils.data.DataLoader]]:
    """
    Returns two pytorch dataloaders for training and test data
    """
    if num_classes is None:
        num_classes = num_classes_from_labels(y_train)
    device_ = 'cuda' if torch.cuda.is_available() else 'cpu'
    tor = lambda x: torch.from_numpy(x)
    X_train, y_train = tor(X_train).float().to(device_), tor(y_train)
    X_test, y_test = tor(X_test).float().to(device_), tor(y_test)
    if num_classes > 1:
        y_train = y_train.long().to(device_)
        y_test = y_test.long().to(device_)
    else:
        y_train = y_train.float().to(device_)
        y_test = y_test.float().to(device_)
    train_loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(X_train, y_train),
        batch_size=batch_size, shuffle=True, drop_last=True)
    test_loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(X_test, y_test),
        batch_size=batch_size, drop_last=True)
    return train_loader, test_loader


def init_imspec_dataloaders(X_train: np.ndarray,
                            y_train: np.ndarray,
                            X_test: np.ndarray,
                            y_test: np.ndarray,
                            batch_size: int
                            ) -> Tuple[Type[torch.utils.data.DataLoader]]:
    """
    Returns train and test dataloaders for training images
    in a native PyTorch format
    """
    device_ = 'cuda' if torch.cuda.is_available() else 'cpu'
    X_train = torch.from_numpy(X_train).float().to(device_)
    y_train = torch.from_numpy(y_train).float().to(device_)
    X_test = torch.from_numpy(X_test).float().to(device_)
    y_test = torch.from_numpy(y_test).float().to(device_)

    data_train = torch.utils.data.TensorDataset(X_train, y_train)
    data_test = torch.utils.data.TensorDataset(X_test, y_test)
    train_iterator = torch.utils.data.DataLoader(
        data_train, batch_size=batch_size, shuffle=True)
    test_iterator = torch.utils.data.DataLoader(
        data_test, batch_size=batch_size)
    return train_iterator, test_iterator


def init_vae_dataloaders(X_train: np.ndarray,
                         X_test: np.ndarray,
                         y_train: Optional[np.ndarray] = None,
                         y_test: Optional[np.ndarray] = None,
                         batch_size: int = 100,
                         ) -> Tuple[Type[torch.utils.data.DataLoader]]:
    """
    Returns train and test dataloaders for training images
    in a native PyTorch format
    """
    labels_ = y_train is not None and y_test is not None
    X_train = torch.from_numpy(X_train).float()
    X_test = torch.from_numpy(X_test).float()
    if labels_:
        y_train = torch.from_numpy(y_train)
        y_test = torch.from_numpy(y_test)

    if torch.cuda.is_available():
        X_train = X_train.cuda()
        X_test = X_test.cuda()
    if labels_:
        y_train = y_train.cuda()
        y_test = y_test.cuda()

    if labels_:
        data_train = torch.utils.data.TensorDataset(X_train, y_train)
        data_test = torch.utils.data.TensorDataset(X_test, y_test)
    else:
        data_train = torch.utils.data.TensorDataset(X_train)
        data_test = torch.utils.data.TensorDataset(X_test)
    train_iterator = torch.utils.data.DataLoader(
        data_train, batch_size=batch_size, shuffle=True)
    test_iterator = torch.utils.data.DataLoader(
        data_test, batch_size=batch_size)
    return train_iterator, test_iterator


def torch_format_image(image_data: np.ndarray) -> torch.Tensor:
    """
    Reshapes (if needed), normalizes and converts image data
    to pytorch format for model training and prediction

    Args:
        image_data (3D or 4D numpy array):
            Image stack with dimensions (n_batches x height x width)
            or (n_batches x 1 x height x width)
    """
    if image_data.ndim not in [3, 4]:
        raise AssertionError(
            "Provide image(s) as 3D (n, h, w) or 4D (n, 1, h, w) tensor")
    if np.ndim(image_data) == 3:
        image_data = np.expand_dims(image_data, axis=1)
    elif np.ndim(image_data) == 4 and image_data.shape[1] != 1:
        raise AssertionError(
            "4D image tensor must have (n, 1, h, w) dimensions")
    else:
        pass
    image_data = (image_data - np.amin(image_data))/np.ptp(image_data)
    image_data = torch.from_numpy(image_data).float()
    return image_data


def torch_format_spectra(spectra: np.ndarray) -> torch.Tensor:
    """
    Reshapes (if needed), normalizes and converts image data
    to pytorch format for model training and prediction

    Args:
        image_data (3D or 4D numpy array):
            Image stack with dimensions (n_batches x height x width)
            or (n_batches x 1 x height x width)
    """
    if spectra.ndim not in [2, 3]:
        raise AssertionError(
            "Provide spectrum(s) as 2D (n, length) or 3D (n, 1, length) tensor")
    if np.ndim(spectra) == 2:
        spectra = np.expand_dims(spectra, axis=1)
    elif np.ndim(spectra) == 3 and spectra.shape[1] != 1:
        raise AssertionError(
            "3D spectra tensor must have (n, 1, length) dimensions")
    else:
        pass
    spectra = (spectra - np.amin(spectra))/np.ptp(spectra)
    spectra = torch.from_numpy(spectra).float()
    return spectra


def torch_format(image_data: np.ndarray) -> torch.Tensor:
    """
    Reshapes (if needed), normalizes and converts image data
    to pytorch format for model training and prediction

    Args:
        image_data (3D or 4D numpy array):
            Image stack with dimensions (n_batches x height x width)
            or (n_batches x 1 x height x width)
    """
    warnings.warn("torch_format is deprecated. Use torch_format_image instead",
                  UserWarning)
    return torch_format_image(image_data)