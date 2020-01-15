"""Utilities for the cumulative_publications project.

Author: fnery, 20190705

"""

from Bio import Entrez

DB = 'pubmed'
SORT = 'relevance'
RETMAX = '2000'
RETMODE = 'xml'

def search(email, query):
    r"""Run Entrez search and return list of IDs with results

    Parameters
    ----------
    email : string
        Email address of the user performing the search. NCBI will contact the
        user before blocking the user's IP in case usage guidelines are violated
    query : string
        Entrez text query

    Returns
    -------
    ids : list of ids
        Search results

    Notes
    -----
    Searches pubmed using the package Entrez (in particular functions [1] and
    [2]) from biopython [3] and does some basic checks to the search results

    References
    ----------
    .. [1] https://biopython.org/docs/1.74/api/Bio.Entrez.html#Bio.Entrez.esearch
    .. [2] https://biopython.org/docs/1.74/api/Bio.Entrez.html#Bio.Entrez.read
    .. [3] https://biopython.org/

    Examples
    --------
    >>> query = 'biopython AND 2019[PDAT]'
    >>> email = 'user@email.com'
    >>> ids = search(email, query)
    >>> print(ids)
    ['31278684', '31762715', '31069053']

    """

    # Perform search
    Entrez.email = email
    handle = Entrez.esearch(db=DB,
                            sort=SORT,
                            retmax=RETMAX,
                            retmode=RETMODE,
                            term=query)

    # Parse results
    results = Entrez.read(handle)

    # Ensure 'retmax' parameter was large enough to return all IDs
    n_found = results['Count']
    n_returned = results['RetMax']

    if n_found != n_returned:
        raise Exception(
            (f"Found {n_found} papers but only returned {n_returned}.\n"
             f"Need to increase 'RETMAX' parameter?"))

    ids = list(results['IdList'])

    # ids should always be a list of unique elements
    if len(ids) != len(set(ids)):
        raise Exception(
            f"Non-unique IDs resulted from searching' {query}'")

    return ids
