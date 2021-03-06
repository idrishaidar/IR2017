#!/usr/bin/env python

import sys
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from collections import defaultdict
from array import array
import math
import gc

# create stemmer by Sastrawi
factory = StemmerFactory()
stemmer = factory.create_stemmer()

class CreateIndex:

    def __init__(self):
        self.index=defaultdict(list)    #the inverted index
        self.myIndex = {}
        self.tf = defaultdict(list)
        self.df = defaultdict(int)
        self.docCount = 0

    def getStopwords(self):
        f=open(self.stopwordsFile, 'r', encoding="utf-8")
        stopwords=[line.rstrip() for line in f]
        self.stopw=dict.fromkeys(stopwords)
        f.close()
        

    def getTerms(self, line):
        line=line.lower()
        line=re.sub(r'[^a-z0-9 ]',' ',line) #put spaces instead of non-alphanumeric characters
        line=line.split()
        line=[x for x in line if x not in self.stopw]  #eliminate the stopwords
        line=[ stemmer.stem(word) for word in line]
        return line


    def getCollection(self):
        doc=[]
        for line in self.collection:
            if line=='</DOC>\n':
                break
            doc.append(line)
        
        currentDoc=''.join(doc)
        docid=re.search('<DOCID>(.*?)</DOCID>', currentDoc, re.DOTALL)
        docdate=re.search('<DATETIME>(.*?)</DATETIME>', currentDoc, re.DOTALL)
        docurl=re.search('<DOC URL>(.*?)</DOC URL>', currentDoc, re.DOTALL)
        doctitle=re.search('<TITLE>(.*?)</TITLE>', currentDoc, re.DOTALL)
        doctext=re.search('<TEXT>(.*?)</TEXT>', currentDoc, re.DOTALL)

        
        if docid==None or doctitle==None or doctext==None or docdate==None:
            return {}

        docs={}
        docs['DOCID'] = docid.group(1)
        docs['DATETIME'] = docdate.group(1)
        docs['DOC URL'] = docurl.group(1)
        docs['TITLE'] = doctitle.group(1)
        docs['TEXT'] = doctext.group(1)
        return docs


    def writeIndexToFile(self):
        f=open(self.indexFile, 'w', encoding="utf-8")
        print (self.docCount)        
        
        for term in self.index.keys():
            postinglist=[]
            for p in self.index[term]:
                docID=p[0].strip()
                positions=p[1]
                # date = p[2]
                postinglist.append(':'.join([str(docID) ,','.join(map(str,positions))]))

            thisPosting = ';'.join(postinglist)
            tfs = ','.join(map(str, self.tf[term]))
            idfs = '%.2f' % (self.docCount/self.df[term])
            # print (''.join((term,'|',';'.join(postinglist))), file=f)
            print ('|'.join((term, thisPosting, tfs, idfs)), file=f)
        f.close()

        f=open(self.titleIndexFile, 'w', encoding="utf-8")
        for docid, attr in self.myIndex.items():
            title, date, url = attr.split('|')
            print ('|'.join((docid.strip(), title, date, url)), file=f)
        f.close()
        

    def getParams(self):
        self.stopwordsFile = "C:\Python34\stopwords_indo.txt"
        self.collectionFile = "C:\Python34\scrap_half.txt"
        self.indexFile = "C:\Python34\collIndex.dat"
        self.titleIndexFile = "C:\Python34\myTitleIndex.txt"
        

    #main 
    def createIndex(self):
        self.getParams()
        self.collection = open(self.collectionFile,'r', encoding="utf-8")
        self.getStopwords()

        gc.disable()
        
        docdict={}
        docdict=self.getCollection()
        #main loop creating the index
        while docdict != {}:            
            lines = '\n'.join((docdict['TITLE'],docdict['TEXT']))
            docid = (str(docdict['DOCID']))
            docdate = docdict['DATETIME'].strip()
            terms = self.getTerms(lines)

            # self.myIndex[docdict['DOCNO']] = docdict['TITLE']
            self.myIndex[docdict['DOCID']] = '|'.join((docdict['TITLE'].strip(), docdict['DATETIME'].strip(), docdict['DOC URL'].strip()))
            self.docCount+=1
            
            #build the index for the current page
            docTerms={}
            for position, term in enumerate(terms):
                try:
                    docTerms[term][1].append(position)
                except:
                    docTerms[term]=[docid, array('I',[position])]
            
            #normalize
            norm = 0
            for term, posting in docTerms.items():
                norm += len(posting[1]) ** 2
            norm = math.sqrt(norm)

            #calculate tf and df
            for term, posting in docTerms.items():
                self.tf[term].append('%.2f' % (len(posting[1])/norm))
                self.df[term] += 1

            #merge the current page index with the main index
            for termpage, postingpage in docTerms.items():
                self.index[termpage].append(postingpage)
            
            docdict=self.getCollection()


        gc.enable()
            
        self.writeIndexToFile()
        print ("Indexing finished.")
    
if __name__=="__main__":
    c=CreateIndex()
    c.createIndex()
    

