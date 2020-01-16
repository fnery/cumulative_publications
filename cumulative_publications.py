#!/usr/bin/env python
r"""Search PubMed and plot evolution in the number of renal MRI articles

***NOTE*** For this module to work, the user's email must be specified in the
constant EMAIL. This is a requirement from NCBI
    "The value of email should be a complete and valid e-mail address of the
    software developer and not that of a third-party end user. The value of
    email will be used only to contact developers if NCBI observes requests that
    violate our policies, and we will attempt such contact prior to blocking
    access." (see https://www.ncbi.nlm.nih.gov/books/NBK25497/)

This module is divided into two functions:
    1. cumulative_publications.do_searches()
    2. cumulative_publications.do_plot()

These, respectively, search PubMed for renal (functional) MRI publications, in
particular using the MRI techniques of diffusion imaging, arterial spin
labelling, blood oxygenation level-dependent MRI and T1&T2 mapping, and
subsequently generate a plot of the evolution in the cumulative number of
publications in the context of renal imaging for technique.

A limited number of searches per second are allowed as per NCBI search
guidelines (see www.ncbi.nlm.nih.gov/books/NBK25497/). This script automatically
limits the frequency of queries to conform to this. Since this slows down the
do_searches() function, this and the do_plot() function can be run separately
by importing the module or together if this module is called as a script.

This code was used in July 2019 to generate Fig. 1 in the following manuscript:
    I. Mendichovszky et al., “Technical recommendations for clinical
    translation of renal MRI: a consensus project of the Cooperation in Science
    and Technology Action PARENCHIMA,” Magn. Reson. Mater. Physics, Biol. Med.,
    Oct. 2019. https://doi.org/10.1007/s10334-019-00784-w

Author: fnery, 20200113

"""

import time
import json
import itertools
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from utils import search

# Options
EMAIL = 'user@email.com'
FNAME_N_IDS = 'n_ids.json'
FNAME_QUERIES = 'queries.json'
FNAME_PLOT = 'cumulative_publications.png'
QUIET = False

# Constants to limit frequency of searches www.ncbi.nlm.nih.gov/books/NBK25497/
N_ALLOWED_REQUESTS = 3  # per second
SAFETY_MARGIN = 0.1  # in seconds

# Constants to build renal MRI queries
ORGAN = '(kidney* OR renal)'
TECHNIQUE = ['(diffusion weighted imaging OR diffusion tensor imaging OR intravoxel incoherent motion)',
             'arterial spin label*',
             'blood oxygenation level-dependent',
             '(T1 mapping OR T2 mapping)']
MODALITY = 'MRI'
YEARS = range(1989, 2021)

# Constants related to the resulting plot
PLOT_LABELS = ['Diffusion imaging',
               'Arterial spin labeling',
               'BOLD',
               'T1&T2 mapping']


def do_searches():
    r"""Search PubMed for renal MRI articles

    Builds yearly search queries using constants defined at the module level.
    Removes duplicates.

    Parameters
    ----------
    None

    Returns
    -------
    Generates two .json files in the current directory, filenames specified in
    the constants FNAME_N_IDS, FNAME_QUERIES (defined at the module level).
    These files contain the number of yearly publications (FNAME_N_IDS) and
    the corresponding query (FNAME_QUERIES).

    Examples
    --------
    >>> import cumulative_publications as cp
    >>> cp.do_searches()

    """

    # Init lists to be populated with dictionaries:
    n_ids = []  # year : number of papers
    queries = []  # year : query strings used

    # Init query counter
    query_ct = 0

    n_queries = len(TECHNIQUE)*len(YEARS)

    for technique in TECHNIQUE:
        for year_index, year in enumerate(YEARS):

            query_ct += 1

            # Build query string and search
            query = f"{ORGAN} AND {technique} AND {MODALITY} AND {year}[PDAT]"
            ids = search(EMAIL, query)

            if not QUIET:
                print(f"Query #{query_ct}/{n_queries}:", end=" ")
                print(f"{query};", end=" ")
                print(f"Found: {len(ids)};", end=" ")

            # Pause execution to comply to max number of requests per second
            time.sleep(1/N_ALLOWED_REQUESTS + SAFETY_MARGIN)

            if year_index == 0:
                cn_ids = len(ids)
                all_ids = ids

                # Set up dict with number of found papers per year
                cdict_n_ids = {year: cn_ids}
                cdict_queries = {year: query}

                if not QUIET:
                    print(f"After removing duplicates: {cn_ids}")

            else:

                # Only keep ids which were not yet seen in previous years
                new_ids = [x for x in ids if x not in all_ids]
                cn_ids = len(new_ids)

                # Having removed duplicates, update list of all_ids
                all_ids.extend(new_ids)

                # Update dict
                cdict_n_ids[year] = cn_ids
                cdict_queries[year] = query

                if not QUIET:
                    print(f"After removing duplicates: {cn_ids}")

        # Append dicts to lists for saving (one technique per list element)
        n_ids.append(cdict_n_ids)
        queries.append(cdict_queries)

    # Save output .json files
    with open(FNAME_N_IDS, 'w', encoding='utf-8') as f:
        json.dump(n_ids, f, ensure_ascii=False, indent=4)

    with open(FNAME_QUERIES, 'w', encoding='utf-8') as f:
        json.dump(queries, f, ensure_ascii=False, indent=4)


def do_plot():
    r"""Plot evolution in the number of renal MRI articles

    Reads the .json file in the current directory with name specified in
    FNAME_N_IDS and plots

    Parameters
    ----------
    None

    Returns
    -------
    Generates a .png figure in the current directory (filename specified in
    the variable FNAME_PLOT) corresponding to the plot showing the evolution in
    the number of renal MRI articles

    Examples
    --------
    This example assumes that the function do_searches() was already called
    to generate the .json files with the data corresponding to the number of
    yearly renal MRI publications
    >>> import cumulative_publications as cp
    >>> cp.do_plot()

    """

    # Open n_ids.json file generated in do_searches()
    with open(FNAME_N_IDS, 'r') as f:
        n_ids = json.load(f)

    # Ensure the number of PLOT_LABELS matches the previously generated n_ids
    if len(PLOT_LABELS) != len(n_ids):
        raise Exception("The number of PLOT_LABELS must match len(n_ids)")

    # Make plot
    style = itertools.cycle(["-", "--", "-.", ":", ".", "h", "H"])
    sns.set_context("notebook", font_scale=1, rc={"lines.linewidth": 2.5})

    for i_label, c_label in enumerate(PLOT_LABELS):
        c_years = np.array(list(n_ids[i_label].keys()))
        c_n_ids = np.array(list(n_ids[i_label].values()))
        plt.plot(c_years, np.cumsum(c_n_ids),
                 linestyle=next(style), label=c_label)

    # Customise appearance and save as .png file
    sns.despine()
    axes = plt.gca()
    axes.set_xlim([15.0, 31])
    plt.legend()
    plt.xticks(rotation=70)
    plt.xlabel('Year')
    plt.ylabel('Cumulative publications')
    plt.tight_layout()
    plt.savefig(FNAME_PLOT, format="png", dpi=300)


if __name__ == "__main__":
    do_searches()
    do_plot()
