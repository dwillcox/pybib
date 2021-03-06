# pybib Overview

pybib is a python-based automatic bibtex generator for PDF's indexed
in the NASA ADS.

Given a list of PDF's, pybib will search each of them for its DOI
identifier and arXiv number if a DOI is not present. Searches are made
via subprocess.Popen calls to pdfgrep.

pybib then queries the NASA ADS to lookup the articles, generate a
bibcode, and save the bibtex files corresponding to the PDF's as
[bibcode].bib.

You can make pybib.py executable, and it executes via ```python```
as defined by ```/usr/bin/env python```. This works with the anaconda
python distribution or your distribution's python package and is
convenient if you alias ```pybib.py``` to, eg. ```pybib```.

## Examples:

### Generate Bibtex files for a.pdf, b.pdf, and c.pdf

```
$ python pybib.py a.pdf b.pdf c.pdf
```

### Generate Bibtex files for all PDF's in an arbitrary directory.

The Bibtex files will be written to the current directory and the bibtex 'File' attribute will consist of the relative path of the corresponding PDF.

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

### Generate Bibtex from PDF's first then construct master.bib

(Argument order can be reversed with the same effect.)

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



# Note on the ADS API Rate Limits

The ADS API imposes rate limits for different services they provide. While the daily search rate limit is 5000 requests, the daily bibtex export limit is only 100 requests. This means that if you use pybib to query the ADS for articles more than 100 times/day, you'll get an APIResponseError which says 'Rate limit was exceeded'. NOTE, however, that you CAN process more than 100 articles every time you use pybib because pybib will send all their bibcodes to the bibtex export service in just 1 bibtex export request.

If this is a problem you can contact the ADS staff directly and request an increased bibtex export limit via ```adshelp@cfa.harvard.edu```

To see your current rate limit, usage, and UTC reset times, use the following:

(Searches)

```
$ curl -v -H "Authorization: Bearer [your ads token]" 'https://api.adsabs.harvard.edu/v1/search/query?q=star'
```

(Bibtex Export)

```
$ curl -v -H "Authorization: Bearer [your ads token]" 'https://api.adsabs.harvard.edu/v1/export/bibtex'
```



# License

Copyright (c) 2016, Donald E. Willcox

pybib is made openly available under the BSD 3-clause license. For details, see the LICENSE file.