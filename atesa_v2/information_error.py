"""
Script to evaluate and store information error in support of the information error convergence criterion in aimless
shooting. Implemented as a separate script to facilitate multiprocessing.
"""

import sys
import os
import time
import re
from statsmodels.tsa.stattools import kpss

def main(as_raw):
    """
    Evaluate the information error during aimless shooting and output results to info_err.out.

    Reads as_raw.out from the present directory to evaluate the information error of the aimless shooting process as
    well as the likelihood that the series of information error values represents a trend stationary process
    (informally, is converged) using the Kwiatkowski-Phillips-Schmidt-Shin (KPSS) test.

    This function depends on lmax.py for evaluations of the information error.

    Parameters
    ----------
    as_raw : str
        Name of the raw aimless shooting file to operate on

    Returns
    -------
    None

    """

    # Read settings from pickle file
    try:
        settings = pickle.load(open('settings.pkl', 'rb'))
    except FileNotFoundError:   # replace with more informative error message
        raise FileNotFoundError('the working directory must contain a valid settings.pkl file, which is generated '
                                'automatically when running ATESA, but one was not found in the working directory: '
                                + os.getcwd())

    # Run resampling to get as_decorr.out
    utilities.resample(settings, write_raw=False)

    # Exit if as_decorr.out has no content
    if len(open('as_decorr.out', 'r').readlines()) == 0:
        return None

    # Run likelihood maximization on current as_decorr.out
    if settings.include_qdot:
        q_str = 'present'
    else:
        q_str = 'absent'
    command = sys.executable + ' lmax.py -i as_decorr.out -q ' + q_str + ' --automagic -o ' + as_raw + '_lmax.out'
    process = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE, preexec_fn=os.setsid)

    # Wait for the output file to get written
    while not os.path.exists(as_raw + '_lmax.out'):
        time.sleep(10)
    time.sleep(10)  # just to give the file time to be written to if needed

    # Now that the output file exists, obtain the information error from the last line
    pattern = re.compile('[0-9.]+')  # pattern to match information error number, and also amount of data in as_raw
    inf_err = float(pattern.findall(open(as_raw + '_lmax.out', 'r').readlines()[-1])[0])

    # Write to info_err.out (and make it, if it doesn't yet exist)
    if not os.path.exists('info_err.out'):
        open('info_err.out', 'w').close()
    open('info_err.out', 'a').write(pattern.findall(as_raw)[0] + ' ' + str(inf_err))


if __name__ == "__main__":
    main(sys.argv[1])