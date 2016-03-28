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
        self.bibcode = u''
        self.get_doi()
        self.get_bibcode()

    def __repr__(self):
        return self.bibcode
        
    def get_doi(self):
        """
        sets BibtexEntry.doi = DOI for this BibtexEntry
        """
        re_doi = u'\s*doi\s*=\s*\{(.*)\}.*'
        self.doi = self.search_re_lines(re_doi)

    def get_bibcode(self):
        """
        sets BibtexEntry.bibcode = bibcode for this BibtexEntry
        """
        re_bibcode = u'@[^\{]*\{([^,]*),.*'
        self.bibcode = self.search_re_lines(re_bibcode)

    def search_re_lines(self, regexp):
        """
        Searches self.lines for re, returning group(1) 
        of the match, if found. Otherwise returns an empty string.
        """
        rec = re.compile(regexp, re.IGNORECASE)
        for l in self.lines:
            rem = rec.match(l)
            if rem:
                return rem.group(1)
            else:
                return ''
    
class BibtexCollection(object):
    """
    Holds a set of bibtex files, each of which can have multiple
    entries
    """
    def __init__(self):
        self.bib_files = {} # filename is key, list of BibtexEntry is value
        self.bibcode_entries = {} # Dictionary of BibtexEntry objects keyed by bibcode

    def read_from_string(self, bibtex_string):
        bibtex_lines = bibtex_string.split(u'\n')
        for bl in bibtex_lines:
            bl = bl + u'\n'
        self.read_from_lines(bibtex_lines)

    def read_from_lines(self, bibtexlines):
        self.bib_files["bibtexlines"] = self.get_entries(bibtexlines)
        self.make_unique_entries()

    def read_from_files(self, bibtexfiles):
        """
        Make a BibtexCollection given a list of input files.
        """
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
        # Gets a unique set of BibtexEntry objects by bibcode
        self.make_unique_entries()
        print('Found {} unique bibtex entries'.format(len(self.bibcode_entries)))
        print(self.bibcode_entries)

    def write_unique_entries(self, outfile):
        """
        Writes unique entries into a master Bibtex file
        """
        self.outfile = outfile
        f = codecs.open(self.outfile, encoding='utf-8', mode='w')
        for bc, entry in self.bibcode_entries.iteritems():
            for l in entry.lines:
                f.write(l)
            f.write(u'\n\n')
        f.close()
        
    def make_unique_entries(self):
        """
        Makes a list of unique BibtexEntry objects keyed by bibcode
        """
        for f, belist in self.bib_files.iteritems():
            for be in belist:
                if be.bibcode in self.bibcode_entries.keys():
                    print('Duplicate bibcode {} - Continuing with replacement ...'.format(be.doi))
                self.bibcode_entries[be.bibcode] = be
            
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
        self.arxiv = ''
        self.paper = None
        self.bibcode = None
        self.bibtex = None
        
        # Try to get DOI
        self.get_doi()
        if not self.doi:
            # Try to get arXiv number if no DOI
            self.get_arxiv()

        # Get bibcode for this paper
        if self.doi:
            self.query_ads_bibcode({'identifier':self.doi})
        elif self.arxiv:
            self.query_ads_bibcode({'identifier':self.arxiv})
        else:
            print('Cannot find {} in ADS with no identifier.'.format(self.name))

    def get_doi(self):
        """
        Gets DOI identifier from the file.
        Sets: self.doi
        """
        pdfgrep_doi_re = "doi\s*:\s*[^ \"'\n'\"]*"
        pdfgrep_stdout = self.call_pdfgrep(pdfgrep_doi_re)
        re_doi = re.compile('(\s*)doi(\s*):(\s*)([^\s\n]*)', re.IGNORECASE)
        m = re_doi.match(pdfgrep_stdout)
        if m:
            self.doi = m.group(4)            
        if self.doi:
            print('Found DOI {} in {}'.format(self.doi, self.name))
        else:
            print('Could not find DOI in {}'.format(self.name))

    def get_arxiv(self):
        """
        Gets arXiv identifier from the file.
        Sets: self.arxiv
        """
        pdfgrep_arx_re = "arXiv:[0-9\.]+v?[0-9]* \[[a-zA-Z-\.]+\] [0-9]{1,2} [a-zA-Z]+ [0-9]{4}"
        pdfgrep_stdout = self.call_pdfgrep(pdfgrep_arx_re)
        re_arx = re.compile('(arXiv:[0-9\.]+).*', re.IGNORECASE)
        m_arxiv = re_arx.match(pdfgrep_stdout)
        if m_arxiv:
            self.arxiv = m_arxiv.group(1)
        if self.arxiv:
            print('Found arXiv ID {} in {}'.format(self.arxiv, self.name))
        else:
            print('Could not find arXiv ID in {}'.format(self.name))

    def call_pdfgrep(self, pdfgrep_re):
        """
        Calls pdfgrep with regular expression pdfgrep_re (case insensitive)
        Returns a tuple corresponding to pdfgrep's (STDOUT, STDERR)
        """
        pdfgrep_call = subprocess.Popen(["pdfgrep", "-ioP",
                                         pdfgrep_re,
                                         self.name],
                                        shell=False,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        pdfgrep_stdout, pdfgrep_err = pdfgrep_call.communicate()
        if pdfgrep_err:
            print('Error in function call_pdfgrep returned from subprocess.Popen:')
            print(pdfgrep_err)
            exit()
        else:
            return pdfgrep_stdout

    def query_ads_bibcode(self, query):
        """
        Query ADS for this paper's bibcode
        Uses the dictionary query keyed by argument name expected by ads.SearchQuery
        """
        try:
            paper_query = ads.SearchQuery(**query)
            paper_list = []
            for p in paper_query:
                paper_list.append(p)
            nresults = len(paper_list)
            if nresults==0:
                print('ERROR: Could not find paper on ADS with query {} for paper {}'.format(query, self.name))
            elif nresults==1:
                self.paper = paper_list[0]
                self.bibcode = self.paper.bibcode
            else:
                print('ERROR: Found {} results on ADS with query {} for paper {}:'.format(nresults, query, self.name))
                for p in paper_list:
                    print(p.bibcode)
                    print('-----')
        except ads.exceptions.APIResponseError:
            print('ERROR: ADS APIResponseError. You probably exceeded your rate limit.')
            self.paper = None
            raise

    def bibtex_lines_to_string(self, lines):
        """
        Turn Bibtex lines into a single unicode string.
        """
        return u'\n'.join(lines) + u'\n\n'
        
    def save_bibtex(self):
        """
        Save Bibtex for this file
        """
        if self.paper:
            # Add file link to bibtex
            file_type = 'PDF'
            bibtex_ads = self.bibtex_lines_to_string(self.bibtex)
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
        self.set_document_bibtex()

    def set_document_bibtex(self):
        """
        Uses query_ads_bibtex to set bibtex for documents in the collection
        """
        bibcodes = [d.bibcode for d in self.documents]
        bc_ads = self.query_ads_bibtex(bibcodes)
        for d in self.documents:
            d.bibtex = bc_ads.bibcode_entries[d.bibcode].lines
        
    def query_ads_bibtex(self, bibcodes):
        """
        Query ADS for the paper bibtexes specified by a list of bibcodes ('bibcodes')
        """
        bc_ads = BibtexCollection()
        try:
            bibtex_string = ads.ExportQuery(bibcodes=bibcodes, format='bibtex').execute()
            bc_ads.read_from_string(bibtex_string)
            bibcodes_found = bc_ads.bibcode_entries.keys()
            nresults = len(bibcodes_found)
            nbibcodes = len(bibcodes)
            if nresults==nbibcodes:
                return bc_ads
            else:
                print('WARNING: did not retrieve bibtex for {} bibcodes:'.format(nresults-nbibcodes))
                for bc in bibcodes:
                    if not bc in bibcodes_found:
                        print(bc)
                
        except ads.exceptions.APIResponseError:
            print('ERROR: ADS APIResponseError. You probably exceeded your rate limit.')
            raise


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
        bc = BibtexCollection()
        bc.read_from_files(fbiblist)
        bc.write_unique_entries(args.catbib)
        print('--------------------------------------------------------------------------------')
