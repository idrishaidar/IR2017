#!/usr/bin/env python

import sys
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from collections import defaultdict
from functools import wraps
import copy

factory = StemmerFactory()
stemmer = factory.create_stemmer()

class QueryIndex:

    def __init__(self):
        self.index = {}
        self.myIndex = {}
        self.tf = {}
        self.idf = {}

    def intersectLists(self,lists):
        if len(lists)==0:
            return []
        #start intersecting from the smaller list
        lists.sort(key=len)
        return list(functools.reduce(lambda x,y: set(x)&set(y),lists))
        
    
    def getStopwords(self):
        f=open(self.stopwordsFile, 'r', encoding="utf-8")
        stopwords=[line.rstrip() for line in f]
        self.stopw=dict.fromkeys(stopwords)
        f.close()
        

    def getTerms(self, line):
        line=line.lower()
        line=re.sub(r'[^a-z0-9 ]',' ',line) #put spaces instead of non-alphanumeric characters
        line=line.split()
        line=[x for x in line if x not in self.stopw]
        line=[ stemmer.stem(word) for word in line]
        return line
        
    
    def getPostings(self, terms):
        #all terms in the list are guaranteed to be in the index
        return [ self.index[term] for term in terms ]
    
    
    def getDocsFromPostings(self, postings):
        #no empty list in postings
        return [ [x[0] for x in p] for p in postings ]


    def readIndex(self):
        f=open(self.indexFile, 'r', encoding="utf-8")
        for line in f:
            line=line.rstrip()
            term, postings, tf, idf = line.split('|') #term='termID', postings='docID1:pos1,pos2;docID2:pos1,pos2'
            postings=postings.split(';')        #postings=['docId1:pos1,pos2','docID2:pos1,pos2']
            postings=[x.split(':') for x in postings] #postings=[['docId1', 'pos1,pos2'], ['docID2', 'pos1,pos2']]
            postings=[ [str(x[0]), map(str, x[1].split(','))] for x in postings ]   #final postings list  
            self.index[term]=postings
            tf = tf.split(',')           
            self.tf[term] = list(map(float, tf))
            # self.tf[term] = [float(tf) for tf in self.tf[term]]
            self.idf[term] = float(idf)
        f.close()

        f = open(self.titleIndexFile, 'r', encoding="utf-8")
        for line in f:
            docid, title = line.rstrip().split(' ', 1)
            self.myIndex[str(docid)]=title
        f.close()

    def dotProduct(self, vector1, vector2):
        if len(vector1) != len(vector2):
            return 0
        return sum([x*y for x,y in zip(vector1, vector2)])

    def rankDocuments(self, terms, docs):
        docVecs = defaultdict(lambda: [0]*len(terms))
        queryVector = [0]*len(terms)
        for termIndex, term in enumerate(terms):
            if term not in self.index:
                continue
            
            queryVector[termIndex] = self.idf[term]

            for docIndex, (doc, postings) in enumerate(self.index[term]):
                if doc in docs: 
                    docVecs[doc][termIndex] = self.tf[term][docIndex]

        #count score of each doc
        docScores = [[self.dotProduct(currDocVec, queryVector), doc ] for doc, currDocVec in docVecs.items()]
        docScores.sort(reverse=True)
        resultDocs = [x[1] for x in docScores][:10]
        resultDocs = [self.myIndex[x] for x in resultDocs]
        print ('\n'.join(resultDocs))
        print ('\n')

    def queryType(self,q):
        # if '"' in q:
        #     return 'PQ'
        if len(q.split()) > 1:
            return 'FTQ'
        else:
            return 'OWQ'


    def owq(self,q):
        # One Word Query
        originalQuery=q
        q=self.getTerms(q)
        if len(q)==0:
            print('')
            return
        elif len(q)>1:
            self.ftq(originalQuery)
            return
        
        #q contains only 1 term 
        term=q[0]
        if term not in self.index:
            print('')
            return
        else:
            postings=self.index[term]
            docs=[p[0] for p in postings]
            # p=' '.join(map(str,p)) 
            # print(p)
            # print via rankDocuments()
            self.rankDocuments(q, docs)          

    def ftq(self,q):
        # Free text query
        q=self.getTerms(q)
        if len(q)==0:
            print('')
            return
        
        thisList=set()
        for term in q:
            try:
                postings=self.index[term]
                docs=[p[0] for p in postings]
                li=li|set(docs)
            except:
                pass
        
        thisList=list(thisList)
        # li.sort()
        # print(' '.join(map(str,li)))
        self.rankDocuments(q, li)

    def pq(self,q):
        # Phrase Query (not completed)
        originalQuery=q
        q=self.getTerms(q)
        if len(q)==0:
            print('')
            return
        elif len(q)==1:
            self.owq(originalQuery)
            return

        phraseDocs=self.pqDocs(q)
        self.rankDocuments(q, phraseDocs)
        # print(' '.join(map(str, phraseDocs)))
        
        
    def pqDocs(self, q):
        phraseDocs=[]
        length=len(q)
        #first find matching docs
        for term in q:
            if term not in self.index:
                return []
        
        postings=self.getPostings(q)    #all the terms in q are in the index
        docs=self.getDocsFromPostings(postings)
        #docs are the documents that contain every term in the query
        docs=self.intersectLists(docs)
        #postings are the postings list of the terms in the documents docs only
        for i in xrange(len(postings)):
            postings[i]=[x for x in postings[i] if x[0] in docs]
        
        #check whether the term ordering in the docs is like in the phrase query
        
        #subtract i from the ith terms location in the docs
        postings=copy.deepcopy(postings)    #this is important since we are going to modify the postings list
        
        for i in xrange(len(postings)):
            for j in xrange(len(postings[i])):
                postings[i][j][1]=[x-i for x in postings[i][j][1]]
        
        #intersect the locations
        result=[]
        for i in xrange(len(postings[0])):
            li=self.intersectLists( [x[i][1] for x in postings] )
            if li==[]:
                continue
            else:
                result.append(postings[0][i][0])    #append the docid to the result
        
        return result

        
    def getParams(self):
        param=sys.argv
        self.stopwordsFile=param[1]
        self.indexFile=param[2]
        self.titleIndexFile=param[3]


    def queryIndex(self):
        self.getParams()
        self.readIndex() 
        self.getStopwords() 

        while True:
            q=sys.stdin.readline()
            if q=='':
                break
            qt=self.queryType(q)
            if qt=='OWQ':
                self.owq(q)
            elif qt=='FTQ':
                self.ftq(q)
            elif qt=='PQ':
                self.pq(q)
        
        
if __name__=="__main__":
    q=QueryIndex()
    q.queryIndex()
