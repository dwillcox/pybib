#!/usr/bin/env python
"""
Copyright (c) 2016, Donald E. Willcox 
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

1. Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
contributors may be used to endorse or promote products derived from
this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from __future__ import print_function
import re
import os
import glob
import ads
import codecs
import argparse
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('infiles', type=str, nargs='*',
                    help='List of input PDF file(s)')
parser.add_argument('-catbib', '--catbib', type=str,
                    help='Name of master bibliography file written')
parser.add_argument('-adstoken', '--adstoken', type=str,
                    help='ADS token to use. (Creates file ads.token).')
args = parser.parse_args()

class BibtexEntry(object):
    """
    Bibtex entry class
    """
    def __init__(self, entry):
        self.lines = entry # entry is a list of bibtex lines
        self.doi   = u''
        self.getdoi()

    def __repr__(self):
        return self.doi
        
    def getdoi(self):
        """
        sets BibtexEntry.doi = DOI for this BibtexEntry
        """
        re_doi = re.compile(u'\s*doi\s*=\s*\{(.*)\}.*', re.IGNORECASE)
        for l in self.lines:
            m_doi = re_doi.match(l)
            if m_doi:
                self.doi = m_doi.group(1)
                return
    
class BibtexCollection(object):
    """
    Holds a set of bibtex files, each of which can have multiple
    entries
    """
    def __init__(self, bibtexfiles, bibtexoutput=None):
        self.bib_files = {} # filename is key, list of BibtexEntry is value
        self.doi_entries = {} # Dictionary of BibtexEntry objects keyed by DOI
        self.outfile = bibtexoutput
        
        for f in bibtexfiles:
            # Open and read f
            fbib = codecs.open(f, encoding='utf-8')
            lines = []
            for l in fbib:
                lines.append(l)
            fbib.close()

            # Turn lines into a list of BibtexEntry objects
            self.bib_files[f] = self.get_entries(lines)

        print('Found {} bibtex files'.format(len(self.bib_files)))
        # Gets a unique set of BibtexEntry objects by DOI
        self.make_unique_entries()
        print('Found {} unique bibtex entries'.format(len(self.doi_entries)))

        # Write the master Bibtex file
        if self.outfile:
            self.write_unique_entries(self.outfile)
            print('Wrote {}'.format(self.outfile))

    def write_unique_entries(self, outfile):
        """
        Writes unique entries into a master Bibtex file
        """
        f = codecs.open(outfile, encoding='utf-8', mode='w')
        for doi, entry in self.doi_entries.iteritems():
            for l in entry.lines:
                f.write(l)
            f.write(u'\n\n')
        f.close()
        
    def make_unique_entries(self):
        """
        Makes a list of unique BibtexEntry objects keyed by DOI
        """
        for f, belist in self.bib_files.iteritems():
            for be in belist:
                if be.doi in self.doi_entries.keys():
                    print('Duplicate DOI {} - Continuing with replacement ...'.format(be.doi))
                self.doi_entries[be.doi] = be
            
    def get_entries(self, lines):
        """
        Turns a list of lines into a list of BibtexEntry objects
        """
        entries = []
        for bibentry in self.gen_bib_entries(lines):
            entries.append(BibtexEntry(bibentry))
        return entries
    
    def gen_bib_entries(self, line_list):
        """
        Yields each entry in list of unicode bibtex lines
        """
        re_entry_start = re.compile(u'@.*')
        re_entry_end   = re.compile(u'\}')
        found_entry = False
        for l in line_list:
            m_entry_start = re_entry_start.match(l)
            if m_entry_start:
                found_entry = True
                entry = []
            if found_entry:
                entry.append(l)
            m_entry_end = re_entry_end.match(l)
            if m_entry_end:
                found_entry = False
                yield entry

class Document(object):
    """
    Class for a document (eg. pdf or ps article)
    """
    def __init__(self, file):
        """
        Initializes Document using filename 'file'
        """
        self.name = file
        
        self.doi = ''
        self.get_doi()

        self.paper = None
        if self.doi:
            self.query_ads()

    def get_doi(self):
        """
        Gets DOI identifier from the file.
        Sets: self.doi
        """
        pdfgrep_doi_re = r'''"doi\s*:\s*[^ "'\n'"]*"'''
        pdfgrep_call = subprocess.Popen("pdfgrep -i -o -P " + pdfgrep_doi_re + ' ' + self.name,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        pdfgrep_stdout, pdfgrep_err = pdfgrep_call.communicate()
        re_doi = re.compile('(\s*)doi(\s*):(\s*)([^\s\n]*)', re.IGNORECASE)
        m = re_doi.match(pdfgrep_stdout)
        if m:
            self.doi = m.group(4)            
        if self.doi:
            print('Found DOI {} in {}'.format(self.doi, self.name))
        else:
            print('Could not find DOI in {}'.format(self.name))

    def query_ads(self):
        """
        Query ADS for this paper using DOI
        """
        try:
            paper_query = ads.SearchQuery(identifier=self.doi)
            paper_list = []
            for p in paper_query:
                paper_list.append(p)
            nresults = len(paper_list)
            if nresults==0:
                print('ERROR: Could not find paper on ADS with DOI {} for paper {}'.format(self.doi, self.name))
            elif nresults==1:
                self.paper = paper_list[0]
                self.bibtex = self.paper.bibtex
            else:
                print('ERROR: Found {} results on ADS with DOI {} for paper {}:'.format(nresults, self.doi, self.name))
                for p in paper_list:
                    print(p.bibtex)
                    print('-----')
        except ads.exceptions.APIResponseError:
            print('ERROR: ADS APIResponseError. You probably exceeded your rate limit.')
            self.paper = None
            pass

    def save_bibtex(self):
        """
        Save Bibtex for this file
        """
        if self.paper:
            # Add file link to bibtex
            file_type = 'PDF'
            bibtex_ads = self.bibtex
            file_bibtex_string = ':{}:{}'.format(self.name, file_type)
            file_bibtex_string = '{' + file_bibtex_string + '}'
            file_bibtex_string = ',\n     File = {}'.format(file_bibtex_string)
            bibtex_last = bibtex_ads[-4:]
            bibtex_body = bibtex_ads[:-4]
            bibtex_body += unicode(file_bibtex_string)
            bibtex = bibtex_body + bibtex_last

            # Save bibtex
            bibtex_file_name = self.paper.bibcode+'.bib'
            fout = open(bibtex_file_name,'w')
            fout.write(bibtex)
            fout.close()
            print('Wrote {} for {}'.format(bibtex_file_name, self.name))
        else:
            print('No paper information for {}, bibtex not written.'.format(self.name))

class DocumentCollection(object):
    """
    Class for a set of documents (eg. pdf or ps articles)
    """
    def __init__(self, files):
        """
        Initializes DocumentCollection using a list of filenames
        """
        self.documents = [Document(f) for f in files]

class ADSToken(object):
    """
    Class for managing the ADS token.
    """
    def __init__(self, token=None):
        self.token = token
        if token:
            self.set_ads_token()
        else:
            self.read_ads_token()

    def exists(self):
        if ads.config.token:
            return True
        else:
            return False
        
    def set_ads_token(self):
        """
        Sets ADS token in file .adstoken
        """
        pybib_dir = os.path.dirname(os.path.realpath(__file__))
        fads_name = os.path.join(pybib_dir,'.adstoken')
        try:
            fads = open(fads_name,'w')
        except:
            print('ERROR: Could not open {} for writing!'.format(fads_name))
            fads_name = os.path.join(os.getcwd(),fads_name)
            try:
                fads = open(fads_name,'w')
            except:
                print('ERROR: Could not open {} for writing!'.format(fads_name))
                exit()
            pass
        fads.write('ads.config.token = {}\n'.format(self.token))
        fads.close()
        print('Wrote {}'.format(fads_name))

    def read_ads_token(self):
        """
        Reads ADS token from file .adstoken
        """
        ads.config.token = ''
        ads_token_re = re.compile(r"(\s*)ads\.config\.token(\s*)=(\s*)(\w*)(\s*)#?.*")
        fail = False
        working_dir = os.getcwd()
        ads_token_dir = working_dir
        try:
            fads = open(os.path.join(os.getcwd(),'.adstoken'),'r')
        except:
            print('Could not find .adstoken in {}'.format(working_dir))
            pybib_dir = os.path.dirname(os.path.realpath(__file__))
            try:
                fads = open(os.path.join(pybib_dir,'.adstoken'),'r')
                ads_token_dir = pybib_dir
            except:
                print('Could not find .adstoken in {}'.format(pybib_dir))
                fail = True
                pass
        if not fail:
            print('Using .adstoken in {}'.format(ads_token_dir))
            for l in fads:
                m = ads_token_re.match(l)
                if m:
                    ads.config.token = m.group(4)
                    break
            fads.close()
            if not ads.config.token:
                print('WARNING: No ads.config.token specified in file .adstoken.')
            else:
                return
        else:
            print('WARNING: No .adstoken file.')
        print('You will not be able to query the NASA ADS. Set your ADS token using the --adstoken option.')
        
if __name__=='__main__':
    print('--------------------------------------------------------------------------------')
    # Initialize ADS token
    ads_token = ADSToken(args.adstoken)

    if ads_token.exists():
        # Make bibtex files for input files
        if args.infiles:
            dc = DocumentCollection(args.infiles)
            print('--------------------------------------------------------------------------------')
            for d in dc.documents:
                d.save_bibtex()
            print('--------------------------------------------------------------------------------')
            
    # Make a master bibliography file
    if args.catbib:
        # Find all .bib files
        fbiblist = glob.glob('*.bib')
        
        # Find unique Bibtex entries and write master file
        bc = BibtexCollection(fbiblist, args.catbib)
        print('--------------------------------------------------------------------------------')
