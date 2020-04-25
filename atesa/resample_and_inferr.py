"""
Helper file to call utilities.resample and then information_error.main in sequence in a single process.
"""

import pickle
from atesa import utilities
from atesa import information_error
from atesa.main import Thread

def main():
    # Read settings from pickle file
    try:
        settings = pickle.load(open('settings.pkl', 'rb'))
    except FileNotFoundError:   # replace with more informative error message
        raise FileNotFoundError('the working directory must contain a valid settings.pkl file, which is generated '
                                'automatically when running ATESA, but one was not found in the working directory: '
                                + os.getcwd())

    # Call resample and then information_error
    print('running utilities.resample()')
    open('this_is_a_debug_file.out', 'w').close()
    utilities.resample(settings, partial=True)
    print('running information_error.main()')
    open('this_is_another_debug_file.out', 'w').close()
    information_error.main()


if __name__ == "__main__":
    main()
