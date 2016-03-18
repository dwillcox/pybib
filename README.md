Author: Donald E. Willcox


# pybib Overview

pybib is a python-based automatic bibtex generator for PDF's indexed
in the NASA ADS.

Given a pdf (or list of pdf's), pybib will search it (them) for a DOI
identifier.

pybib then queries the NASA ADS to lookup the article, generate a
bibcode, and save the bibtex files corresponding to the pdf's as
[bibcode].bib.


# --catbib

If the option --catbib is used, pybib will perform the above (if no
pdf's are given it will skip those steps) and then glob a set of all
*.bib files in the working directory, open them, and concatenate them,
detecting and eliminating duplicates via their DOI numbers. The
argument to --catbib sets the name of the master bibliography thus
generated.


# --adstoken

pybib will look in the file '.adstoken' for your ADS access token,
searching for the file first in the working directory and next in the
directory where pybib.py is stored. It will read all lines of the
file, matching the following regular expression and setting
ads.config.token to group 4 of the match.

``` (\s*)ads\.config\.token(\s*)=(\s*)(\w*)(\s*)#?.* ```

If you don't have an ADS token stored, you will be warned and the
program will not query the ADS.

To set your ADS token, run pybib with the --adstoken option and supply
your token as follows. pybib will create a file named '.adstoken' for
you with your designated token in the directory of pybib.py.


# Supported Journals

Verified to work with recent articles in the following journals:

* ApJ

* ApJ Lett.

* MNRAS

* Phys. Rev. Lett.

* Phys. Rev. D

* Phys. Rev. C


# Dependencies

pybib requires:

* python ads module

* pdfgrep v.1.4.1

