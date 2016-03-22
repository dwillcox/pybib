Author: Donald E. Willcox


# pybib Overview

pybib is a python-based automatic bibtex generator for PDF's indexed
in the NASA ADS.

Given a list of PDF's, pybib will search each of them for it's DOI identifier and arXiv number if a DOI is not present.

pybib then queries the NASA ADS to lookup the articles, generate a
bibcode, and save the bibtex files corresponding to the PDF's as
[bibcode].bib.

You can make pybib.py executable, and it will execute via ```python``` as
defined by ```/usr/bin/env python```. This works with the anaconda
python distribution and is convenient if you also alias ```pybib.py``` to, eg. ```pybib```

## Examples:

### Generate Bibtex files for a.pdf, b.pdf, and c.pdf

```
$ python pybib.py a.pdf b.pdf c.pdf
```

### Generate Bibtex files for all PDF's in an arbitrary directory. The Bibtex files will be written to the current directory.

```
$ python pybib.py ~/library/articles/*.pdf
```


# --catbib

If the option --catbib is used, pybib will perform the above (if no
PDF's are given it will skip those steps) and then glob a set of all
*.bib files in the current directory, open them, and concatenate them,
detecting and eliminating duplicates via their bibcodes. The
argument to --catbib sets the name of the master bibliography thus
generated.

## Examples:

### Generate master.bib from all the Bibtex files in the current directory

```
$ python pybib.py --catbib master.bib
```

### Generate Bibtex from all the PDF's in the current directory and then write master.bib. (Argument order can be reversed with the same effect.)

```
$ python pybib.py *.pdf --catbib master.bib
```


# --adstoken

pybib will look in the file '.adstoken' for your ADS access token,
searching for the file first in the working directory and next in the
directory where pybib.py is stored.

It will read all lines of the '.adstoken' file, matching the following regular
expression and setting ads.config.token to group 4 of the match.

``` (\s*)ads\.config\.token(\s*)=(\s*)(\w*)(\s*)#?.* ```

If you don't have an ADS token stored, you will be warned and the
program will not query the ADS.

To create an ADS token:

* Create an account at [https://ui.adsabs.harvard.edu]

* Go to Account > Customize Settings > API Token

* ``Generate a new key''

To set your ADS token, run pybib with the --adstoken option and supply
your token as follows. pybib will create a file named '.adstoken' for
you with your designated token in the directory of pybib.py. If you've
cloned a git repo, '.adstoken' is in the .gitignore file so your token
won't be accidentally committed to git.

If you'd rather create an '.adstoken' file manually in the current
directory, create it as follows with your token (eg. '01234abcd'):

```
ads.config.token = 01234abcd # Comments
```

## Example:

```
$ python pybib.py --adstoken '01234abcd'
```


# Supported Journals/Databases

Verified to work with recent articles in the following:

* arXiv

* ApJ

* ApJ Lett.

* MNRAS

* Phys. Rev. Lett.

* Phys. Rev. D

* Phys. Rev. C



# Dependencies

* python ads module [https://pypi.python.org/pypi/ads]

* pdfgrep v.1.4.1 [https://pdfgrep.org]

