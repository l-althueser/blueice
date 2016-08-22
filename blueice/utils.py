from copy import deepcopy
import os
import pickle
from hashlib import sha1

import numpy as np
from scipy.interpolate import interp1d


def inherit_docstring_from(cls):
    """Decorator for inheriting doc strings, stolen from
    https://groups.google.com/forum/#!msg/comp.lang.python/HkB1uhDcvdk/lWzWtPy09yYJ
    """
    def docstring_inheriting_decorator(fn):
        fn.__doc__ = getattr(cls, fn.__name__).__doc__
        return fn
    return docstring_inheriting_decorator


def combine_dicts(*args, exclude=(), deep_copy=False):
    """Returns a new dict with entries from all dicts passed, with later dicts overriding earlier ones.
    :param exclude: Remove these keys from the result.
    :param deepcopy: Perform a deepcopy of the dicts before combining them.
    """
    if not len(args):
        return dict()
    result = {}
    for d in args:
        if deep_copy:
            d = deepcopy(d)
        result.update(d)
    result = {k: v for k, v in result.items() if k not in exclude}
    return result


def data_file_name(filename, data_dirs=None):
    """Returns filename if a file exists. Also checks data_dirs for the file."""
    if os.path.exists(filename):
        return filename
    if data_dirs is not None:
        return find_file_in_folders(filename, data_dirs)
    return FileNotFoundError(filename)


def find_file_in_folders(filename, folders):
    """Searches for filename in folders, then return full path or raise FileNotFoundError
    Does not recurse into subdirectories
    """
    if isinstance(folders, str):
        folders = [folders]
    for folder in folders:
        full_path = os.path.join(folder, filename)
        if os.path.exists(full_path):
            return full_path
    raise FileNotFoundError(filename)


def read_pickle(filename):
    with open(filename, mode='rb') as infile:
        result = pickle.load(infile)
    return result


def save_pickle(stuff, filename):
    """Saves stuff in a pickle at filename"""
    with open(filename, mode='wb') as outfile:
        pickle.dump(stuff, outfile)


def hashablize(obj):
    """Convert a container hierarchy into one that can be hashed.
    See http://stackoverflow.com/questions/985294
    """
    try:
        hash(obj)
    except TypeError:
        if isinstance(obj, dict):
            return tuple((k, hashablize(v)) for (k, v) in sorted(obj.items()))
        elif hasattr(obj, '__iter__'):
            return tuple(hashablize(o) for o in obj)
        else:
            raise TypeError("Can't hashablize object of type %r" % type(obj))
    else:
        return obj


def deterministic_hash(thing):
    """Return a deterministic hash of a container hierarchy using hashablize, pickle and sha1"""
    return sha1(pickle.dumps(hashablize(thing))).hexdigest()


def _events_to_analysis_dimensions(events, analysis_space):
    """Return a list of arrays of the values of events in each of the analysis dimensions specified in analysis_space"""
    return [events[x] for x, bins in analysis_space]


class InterpolateAndExtrapolate1D(object):
    """Extends scipy.interpolate.interp1d to do constant extrapolation outside of the data range
    """
    def __init__(self, points, values):
        points = np.asarray(points)
        self.interpolator = interp1d(points, values)
        self.min = points.min()
        self.max = points.max()

    def __call__(self, points):
        try:
            points[0]
        except (TypeError, IndexError):
            points = np.array([points])
        points = np.clip(points, self.min, self.max)
        return self.interpolator(points)


def arrays_to_grid(arrs):
    """Convert a list of n 1-dim arrays to an n+1-dim. array, where last dimension denotes coordinate values at point.
    """
    return np.stack(np.meshgrid(*arrs, indexing='ij'), axis=-1)
