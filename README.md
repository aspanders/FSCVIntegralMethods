# FSCV data analysis software

Author: Leonardo Espı́n

espin.leonardo@mayo.edu



Documentation of the set of Matlab functions written by Leonardo Espı́n
for analyzing cyclic-voltammogram data recorded with harmoni. This
document assumes that the reader has a basic familiarity with Matlab and
James Trevathan's Matlab WincsWare class.

The starting point for using any of the data analysis code is a
wincsware object, which is defined in Matlab as:

`>>object=WincsWare('example file.hdat');`

where *"example file.hdat"* is a harmoni recording.

-   Functions for computing background subtracted voltammograms:

    -   `dynamicSubtract.m` is for simple, manual calculation of
        background subtracted voltammograms. An example of usage is

        `>>[voltammogram, vtime]=dynamicSubtract(object,cursorA,cursorB,varargin);`

        where `object` is our wincsware object,
        `cursorA` is a matlab cursor object which points
        the time coordinates of the voltammogram of interest, and
        `cursorB` points the time coordinates of the
        background current. The optional argument tells the function if
        time indices are passed in the cursor objects, instead of times.

        The function returns the background subtracted voltammogram as a
        column vector, and its corresponding time. The number of
        voltammograms to be used for averaging can be modified inside
        the function.

    -   `automaticSubtract.m` automatically calculates background
        subtracted voltammograms. This function uses signal analysis
        techniques for automation purposes, and it is intended for
        general use. An example of usage is

        `>>[cv,cvdata]=automaticSubtract(object,cursor,volt);`

        where `cursor` is a matlab cursor object indicating
        where the background current stabilization period ends, and
        `volt` indicates a voltage value for selecting a
        voltage trace where current spikes are going to be identified
        (for dopamine `volt` would be close to 0.6 V).

        The function returns a matrix containing background subtracted
        voltammograms as columns `cv(m x n)`, and a second matrix
        `cvdata(2 x n)` which contains the times corresponding for each
        voltammogram (first row), and time difference between the
        background and the maximum current spike (in second row of
        cvdata).

        This function plots an FSCV trace superimposed with the
        locations of extracted current peaks and backgrounds to help
        visualizing and detecting outliers. This function calls

        -   `subtractionIndices.m`

    -   `dbsSubtract.m` automatically calculates background subtracted
        voltammograms, but it is intended to be used with DBS data. This
        function obtains the stimulation times from the object, which
        are used as points of selection for background currents. An
        example of usage is

        `>>[cv,cvdata]=dbsSubtract(object,volt);`

        where `object` is our wincsware object, and
        `volt` indicates a voltage value for selecting a
        voltage trace.

        The function output is the same as
        `automaticSubtract`, however, the second row of
        cvdata now stores the time delay between stimulations and
        maximum current spikes, resulting for each individual
        stimulation.

        This function plots the second row of cvdata to help detect
        outliers (cause by stimulation artifacts or by stimulation
        misfires).

    -   `singleAutoSubtract.m` is a modification of
        `automaticSubtract.m` which uses a fixed background current for
        all background subtractions. This function calls

        -   `subtractionIndices.m`

    -   `singleDbsSubtract.m` is a modification of `dbsSubtract.m` which
        uses a fixed background current for all background subtractions.

-   Charge analysis functions

    -   `dbsChargeAnalysis.m` An example of usage is

        `>>[charge,bdryPairs]=dbsChargeAnalysis(cv,cvdata,object.sensingVoltage,label);`

        This function calls

        -   `select_limits.m`

        -   `differential_analysis.m`

        -   `limitsWithCond.m`

    -   `ChargeAnalysis.m` This function is the same as
        `dbsChargeAnalysis.m`, but has a couple of plotting commands
        commented out. This function calls

        -   `select_limits.m`

        -   `differential_analysis.m`

        -   `limitsWithCond.m`

-   Basic calculation functions called by other functions

    -   `subtractionIndices.m` finds the time indices of current peaks
        and background currents in a time trace vector. This function is
        called by `automaticSubtract.m` and
        `singleAutoSubtract.m`

    -   `select_limits.m` This function finds the zeros in the columns
        of a `m x n` data matrix, which surround and are closer to a
        center value, that varies for each column.

    -   `limitsWithCond.m` does something similar to `select_limits.m`,
        but it allows for a condition on the zeros, that has to be
        satisfied

    -   `differential_analysis.m` takes care of smoothing voltammograms
        for the calculation of higher order derivatives

-   Other

    -   `artifactRemoval.m` is used for the removal for stimulation
        artifacts from background subtracted voltammograms. An example
        of usage is

        `>>cv_modified=artifactRemoval(cv,ave,var);`

    -   `stimParameters.m` is used for obtaining the stimulation
        parameters used in a DBS harmoni recording. An example of usage
        is

        `>>data=stimParameters(object,duration);`

    -   `legend_matrix.m` creates a text cell array to be used as a
        legend for voltammogram-matrix plots
