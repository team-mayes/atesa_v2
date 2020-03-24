"""
Standalone script for converting equilibrium path sampling output files into free energy profiles via Boltzmann
weighting.
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import sys
import os

def main(input_file, output_file, bootstrapCyc=0, bootstrapN=0, nbins=4, temp=300, exclude_fract=0, noplot=False):
    """
    Process equilibrium path sampling output file input_file to obtain free energy profile.

    This is the main function of boltzmann_weight.py, which converts each EPS window into a stretch of the energy
    profile and stitches these stretches together into a continuous plot. Simply put, this function descretizes and
    reweights the data according to the Boltzmann weight (E = kT*ln(p), where p is the probability of a given state).

    Parameters
    ----------
    input_file : str
        Name of input file containing raw EPS data
    output_file : str
        Name of output file to write results to; will be overwritten if extant
    bootstrapCyc : int
        Number of cycles of bootstrapping to run; if zero, bootstrapping is not performed
    bootstrapN : int
        Number of bootstrapping samples to include (used only if bootstrap == True)
    nbins : int
        Number of bins to divide each EPS window into for constructing the PMF
    temp : float
        Temperature in Kelvin at which to assess the PMF
    exclude_fract : float
        Fraction of data from the beginning of each window to exclude from the calculations
    noplot : bool
        If True, suppress output of matplotlib plots; still writes output to output_file

    Returns
    -------
    None

    """

    if bootstrapCyc > 0:
        bootstrap = True
        allpmfs = []    # each PMF calculated during bootstrapping, for evaluating error
    else:
        bootstrap = False
        bootstrapCyc = 0

    kT = temp * 0.001987    # kcal/mol-K

    file = open(input_file, 'r').readlines()[1:]    # skip header line
    open(input_file, 'r').close()

    windows = []    # nested list of format [[lower0, upper0], [lower1, upper1], ...]
    data = []       # nested list with indices corresponding windows, format [[x00, x01, ...], [x10, x11,...], ...]
    this_data = []  # object to store subsampled data for bootstrapping
    alldata = []    # simple list [x00, x01, ... x0N, x10, x11, ...]

    # Determine the window boundaries
    for line in file:
        line = line.strip('\n')
        split = line.split()
        if [float('%.3f' % float(split[0])), float('%.3f' % (float(split[1])))] not in windows:
            windows.append([float('%.3f' % (float(split[0]))), float('%.3f' % (float(split[1])))])
            data.append([])
            this_data.append([])

    windows.sort(key=lambda x: x[0])    # need to be sorted for building the PMF

    for line in file:
        line = line.strip('\n')
        split = line.split(' ')
        if float('%.3f' % float(split[0])) <= float(split[2]) <= float('%.3f' % float(split[1])):
            data[windows.index([float('%.3f' % float(split[0])),float('%.3f' % float(split[1]))])].append(float(split[2]))
            alldata.append(float(split[2]))

    # Exclude fraction of data
    for window_index in range(len(windows)):
        data[window_index] = data[window_index][int(len(data[window_index])*exclude_fract):]

    fullPMF = []
    fullRC = []

    # Set up figures outside of loop
    if not noplot:
        fig = plt.figure()
        ax0 = fig.add_subplot(111)
        fig = plt.figure()
        ax4 = fig.add_subplot(111)

    for cyc in range(bootstrapCyc + 1):     # last cycle plots PMF
        # Get a random subsampling of data in each window (with replacement)
        if cyc < bootstrapCyc:
            for i in range(len(windows)):
                this_data[i] = np.random.choice(data[i], bootstrapN)
        else:
            this_data = data

        for window_index in range(len(windows)):

            RC_values = np.linspace(windows[window_index][0], windows[window_index][1], nbins)  # list RC value of each bin

            probs = [0 for null in range(nbins)]    # initialize probabilities by bin
            thismin = min(this_data[window_index])       # obtain min and max values within the window
            thismax = max(this_data[window_index])

            # Experimental
            # RC_values = [windows[window_index][0] + (windows[window_index][1] - windows[window_index][0]) * np.mean([i / nbins, (i + 1) / nbins]) for i in range(nbins)]

            if min(this_data[window_index]) == max(this_data[window_index]):
                raise RuntimeError('Found a window containing only a single sampled value. The boundaries of the offending '
                                   'window are: ' + str(windows[window_index]) + '. Sample more in this window or remove '
                                   'it from the input file.')

            for value in this_data[window_index]:
                reduced = (value - thismin)/(thismax - thismin)     # reduce to between 0 and 1
                local_index = int(np.floor(reduced * nbins))        # sort into bin within window
                if local_index == nbins:            # this can't handle RC values outside the bounds. Not a problem?
                    local_index = nbins - 1         # handle case where reduced == 1
                probs[local_index] += 1     # increment probability count in the appropriate window

            for i in range(len(probs)):
                probs[i] = probs[i]/len(this_data[window_index])     # scale probability counts to get fractions

            local_index = 0                     # initialize index for bins within this window
            U = [0 for null in range(nbins)]    # initialize energy values for this window
            offset = 0      # initialize vertical offset of energy to help stitch adjacent windows together

            # Calculate energy corresponding to each probability in this window
            for prob in probs:
                if local_index == 0 and not bootstrap:
                    offset = -1 * kT * np.log(prob)
                if not prob == 0:
                    U[local_index] = -1 * kT * np.log(prob) - offset
                local_index += 1

            # Adjust energy values uniformly up or down to stitch adjacent windows together smoothly
            if window_index == 0 or bootstrap: # turn off boundary value matching during bootstrapping to avoid propagating errors in this step into PMF error in final step
                left_boundary = 0
            else:   # calculate the adjustment
                f1 = (RC_values[0] - boundary_values[3]) / (boundary_values[2] - boundary_values[3])     # fraction between 0 and 1 corresponding to distance first point of next window falls between last two points of previous window
                left_boundary1 = ((boundary_values[0] - boundary_values[1]) * f1) + boundary_values[1]   # shift to lower next window to intersect last one
                f2 = (boundary_values[2] - RC_values[0]) / (RC_values[1] - RC_values[0])
                left_boundary2 = boundary_values[0] - ((U[1] - U[0]) * f2) + U[0]                       # shift to lower next window so that previous one intersects it
                left_boundary = np.mean([left_boundary1,left_boundary2])                                # average of shift amounts
            for Uindex in range(len(U)):    # apply the adjustment
                U[Uindex] += left_boundary
            boundary_values = [U[-1], U[-2], RC_values[-1], RC_values[-2]]  # [x2, x1, r2, r1]; store data for this step to calculate left_boundary for next step

            fullPMF += U    # append the just-calculated data to the full energy profile

            if cyc < bootstrapCyc:
                allpmfs.append(fullPMF)
            else:
                if bootstrapCyc > 0:
                    error = # todo: get standard error of each index in allpmfs
                fullRC += list(RC_values)

                # Do the plotting
                if not noplot:
                    error_index = 0
                    ax0.errorbar(RC_values, U, error[error_index:error_index + len(U)])
                    fig.canvas.draw()
                    nextcolor = list(colors.to_rgb(next(ax4._get_patches_for_fill.prop_cycler).get('color'))) + [0.75]
                    ax4.bar(np.linspace(windows[window_index][0],windows[window_index][1],len(probs)),probs,width=0.2,color=nextcolor)
                    fig.canvas.draw()
                    error_index += len(U)

    if not noplot:   # in this case, we want to display the result
        plt.show()

    # For smoothing the PMF into a single continuous line
    smoothPMF = []
    smoothRC = []
    smoothErr = []
    i = 0
    while i < len(fullPMF):
        if (i+1) % nbins == 0 and i + 1 < len(fullPMF):
            i += 1  # skip next point
        else:
            smoothPMF.append(fullPMF[i])
            smoothRC.append(fullRC[i])
            smoothErr.append(error[i])
        i += 1

    with open(output_file, 'w') as f:
        for i in range(len(smoothRC)):
            f.write(str(smoothRC[i]) + ' ' + str(smoothPMF[i]) + ' ' + str(smoothErr[i]) + '\n')

    if not noplot:
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1.plot(smoothRC,smoothPMF,color='#0072BD',lw=2)
        plt.fill_between(np.asarray(smoothRC), np.asarray(smoothPMF) - np.asarray(smoothErr), np.asarray(smoothPMF) + np.asarray(smoothErr),
                       alpha=0.5, facecolor='#0072BD')
        plt.ylabel('Free Energy (kcal/mol)', weight='bold')
        plt.xlabel('Reaction Coordinate', weight='bold')
        fig.canvas.draw()
        plt.show()

    # Section for writing WHAM input files, if desired (deprecated)
    # open('eps.meta','w').close()
    # for window_index in range(len(windows)):
    #     open('eps' + str(window_index) + '.data','w').close()
    #     count = 0
    #     for value in data[window_index]:
    #         count += 1
    #         open('eps' + str(window_index) + '.data','a').write(str(count) + ' ' + str(value) + '\n')
    #     open('eps' + str(window_index) + '.data', 'a').close()
    #     open('eps.meta','a').write('eps' + str(window_index) + '.data ' + str(np.mean(windows[window_index])) + ' 0\n')

    # Plot a normalized histogram of each window (deprecated)
    # fig = plt.figure()
    # ax2 = fig.add_subplot(111)
    # for window_index in range(len(windows)):
    #     # To build nextcolor, we access the default color cycle object and then append an alpha value
    #     nextcolor = list(colors.to_rgb(next(ax2._get_patches_for_fill.prop_cycler).get('color'))) + [0.75]
    #     n, bins, rectangles = ax2.hist(np.asarray(data[window_index]), nbins, normed=True, color=nextcolor)
    #     fig.canvas.draw()
    # plt.show()


def update_progress(progress, message='Progress'):
    """
    Print a dynamic progress bar to stdout.

    Credit to Brian Khuu from stackoverflow, https://stackoverflow.com/questions/3160699/python-progress-bar

    Parameters
    ----------
    progress : float
        A number between 0 and 1 indicating the fractional completeness of the bar. A value under 0 represents a 'halt'.
        A value at 1 or bigger represents 100%.
    message : str
        The string to precede the progress bar (so as to indicate what is progressing)

    Returns
    -------
    None

    """
    barLength = 10  # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done!\r\n"
    block = int(round(barLength * progress))
    text = "\r" + message + ": [{0}] {1}% {2}".format(
        "#" * block + "-" * (barLength - block), round(progress * 100, 2), status)
    sys.stdout.write(text)
    sys.stdout.flush()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Perform LMAX on the given input data')
    parser.add_argument('-i', metavar='input_file', type=str, nargs=1, default=['eps.out'],
                        help='input filename (output from equilibrium path sampling). Default=eps.out')
    parser.add_argument('-o', metavar='output_file', type=str, nargs=1, default=['fep.out'],
                        help='output filename. Default=fep.out')
    parser.add_argument('-t', metavar='temp', type=int, nargs=1, default=[300],
                        help='temperature in Kelvin to evaluate energy at. Default=300')
    parser.add_argument('-n', metavar='nbins', type=int, nargs=1, default=[5],
                        help='number of bins to divide each window into. Default=5')
    parser.add_argument('-b', metavar='bootstrapN', type=int, nargs=1, default=[25],
                        help='number of bootstrapping samples to include in each window. Default=25')
    parser.add_argument('-c', metavar='bootstrapCyc', type=int, nargs=1, default=[100],
                        help='number of bootstrapping cycles to average over. Default=100')
    parser.add_argument('-e', metavar='exclude_fract', type=float, nargs=1, default=[0],
                        help='fraction of data from each window to exclude from calculations for decorrelation. Must be'
                             ' between 0 and 1. Default=0')
    parser.add_argument('--noplot', action='store_true', default=False,
                        help='suppress free energy profile and window histogram plots')

    arguments = vars(parser.parse_args())  # Retrieves arguments as a dictionary object
    input_file = arguments['i'][0]
    output_file = arguments['o'][0]
    temp = arguments['t'][0]
    nbins = arguments['n'][0]
    bootstrapN = arguments['b'][0]
    bootstrapCyc = arguments['c'][0]
    exclude_fract = arguments['e'][0]
    noplot = arguments['noplot']

    main(input_file, output_file, bootstrapCyc=bootstrapCyc, bootstrapN=bootstrapN, nbins=nbins, temp=temp, exclude_fract=exclude_fract, noplot=noplot)

    # Implement bootstrapping if needed; I wrote this a long time ago and it's sloppy as hell, but it works
    # if bootstrapCyc:
    #     means = []          # initialize list of bootstrapping results
    #     std = []            # initialize list of standard error values
    #     for i in range(bootstrapCyc):
    #         means.append(main(input_file, output_file, bootstrap=True, bootstrapN=bootstrapN, nbins=nbins, temp=temp, noplot=noplot))
    #         update_progress((i+1)/bootstrapCyc, message='Bootstrapping')
    #     for j in range(len(means[0])):
    #         this_window = [u[j] for u in means]                     # j'th value from each bootstrapping iteration
    #         std.append(np.std(this_window))                         # standard deviation for this window
    #     main(input_file, output_file, bootstrap=False, error=std, nbins=nbins, temp=temp, noplot=noplot)
    # else:
    #     main(input_file, output_file, bootstrap=False, nbins=nbins, temp=temp, noplot=noplot)
