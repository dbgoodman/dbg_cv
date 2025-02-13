##########
# Ravi S. Jonnal - http://pointsofsail.org - rjonnal@indiana.edu
# Preparing your CV using LaTeX and BibTeX. 
#
# URL: http://pointsofsail.org/wikka.php?wakka=LatexCV
# No rights reserved: http://creativecommons.org/choose/zero/
#
# Obviously there are no explicit or implicit guarantees that this
# program works, works correctly, or does anything remotely related to
# what it claims to do. If you have a specific problem, feel free to
# contact me, but I cannot promise to reply in timely fashion, or at
# all. I will try, though.
#
# Feel free to modify this program and distribute it with or without
# attribution. If you improve it, it would be nice if you sent me a
# copy.
############
#
# This script attempts to convert a LaTeX CV (based on the template
# located at URL above) into wiki markup.
#
# Assuming you have a LaTeX file containing the CV (e.g. my_cv.tex)
# and you have LaTeX-ed and BibTeX-ed it correctly, so that you also
# have the BBL file containing formatted references (my_cv.bbl, in
# this example), you may invoke this script as follows, on the
# filename root my_cv:
#
# 1) To print the output to the terminal:
#    # python texcv2wikicv.py my_cv
#    - or -
#    # python texcv2wikicv.py my_cv | more
#
# 2) To save to a text file:
#    # python texcv2wikicv.py my_cv > outputfile.txt
#
# Make sure you do not invoke this command using the full
# filenames. That is, omit the .tex and .bbl.
#
# The most likely problems you'll encounter are KeyErrors due to
# missing keys in the CODE_DICTIONARY, or failure to zap stray LaTeX
# markup. The former can be addressed by adding entries to
# CODE_DICTIONARY and the latter by modifying the three TABLES near
# the top of the file.

import sys,re

fnTag = sys.argv[1]

# Set to True if year is to be boldfaced (**) in publications. There
# is no unambiguous way to determine if a number in the
# citation/reference text is a year, so this is by no means guaranteed
# to work. If it's breaking your output, set to False.
BOLDFACE_YEARS = True

# List of tuples (x,y); before parsing, every instance of x will be
# replaced with y.
PREPROCESS_REPLACEMENT_TABLE = [
    ('\&','&'),
    ('\'\'','"'),
    ('``','"'),
    ('\\\\',''),
    ('\\cd','""&middot;""'),
    ('\\noindent',''),
    ('\\newblock',''),
    ('\\textwidth','')
    ]

# List of tuples (x); before parsing, any line containing x will be
# completely removed from the text
PREPROCESS_REMOVE_LINES_TABLE = [
    ('\\nobibliography'),
    ('\\begin{minipage}'),
    ('\\end{minipage}'),
    ('\\begin{multicols}'),
    ('\\end{multicols}'),
    ('\\par\\vspace{'),
    ('\\bibliographystyle{'),
    ('\\newpage')
    ]

# List of tuples (x,y); after parsing, each match for regular
# expression x is replaced, using re.sub(x,y,...), with y
POSTPROCESS_REGEX_REPLACEMENT_TABLE = [
    ("\[.*cm\]",""),
    ("\s*[.]","."),
    ("\s*[,]",","),
    ("[ ]+"," "),
    ("[\n][\n]+","\n\n")
    ]

CODE_DICTIONARY = {
    'document':'',
    'em':'//',
    'bf':'**',
    'null':'',
    'center':'',
    'emph':'//',
    'years':('\n**','** '),
    'publication':'',
    'previousMacro':'',
    'nobibliography':'',
    'LARGE':'======',
    'section*':('\n====','===='),
    'subsection*':('\n===','==='),
    'textsc':'',
    'it':'//',
    'minipage':''
}


def isNumber(s):
    '''
    Returns True if s is a number, False otherwise.
    '''
    try:
        float(s)
        return True
    except ValueError:
        return False


def findBraces(texStr):
    '''
    Takes a string of LaTeX and returns a tuple of two lists. The
    first corresponds to the left braces and the second the matching
    right braces.
    '''

    if not len(texStr.strip()):
        return []
    else:
        nestedness = 0
        lefts = []
        rights = []
        stack = []
        for (index,char) in zip(range(len(texStr)),texStr):
            if index>0:
                prev = texStr[index-1]
            else:
                prev = ''

            if index<len(texStr)-1:
                next = texStr[index+1]
            else:
                next = ''

            if char=='{' and not prev=='\\' and not prev=='}':
                nestedness = nestedness + 1
                stack.append(index)
            if char=='}' and not prev=='\\' and not next=='{':
                nestedness = nestedness - 1
                lefts.append(stack.pop())
                rights.append(index+1)
        zlr = zip(lefts,rights)
        return sorted(zlr,key=lambda x: x[0])

def unifyMacros(texStr):
    '''
    This replaces any instance of \begin{macroname} \end{macroname}
    with \macroname{}, to simplify parsing. It also standardizes the
    macro syntax by putting spaces before and after braces, spaces
    before backslashes (\) and getting rid of LaTeX newlines (\\).
    '''
    newString = ''
    oldString = texStr
    done = not oldString.find('\\begin')+1
    while not done:
        pos = oldString.find('\\begin')
        newString = newString + oldString[0:pos]
        openpos = oldString.find('{',pos)
        closepos = oldString.find('}',openpos)
        macroname = oldString[openpos+1:closepos]
        newString = newString + '\\' + macroname + '{'
        oldString = oldString[closepos+1:]
        endString = '\\end{'+macroname+'}'
        oldString = oldString.replace('\\end{'+macroname+'}','}')
        done = not oldString.find('\\begin')+1
    newString = newString + oldString
    newString = newString.replace('{',' {')
    newString = newString.replace('}','} ')
    newString = newString.replace('\\\\','')
    newString = newString.replace('\\',' \\')
    return newString

def isLeftWordMacro(texStr,pos):
    '''
    Is the word to the left of pos in texStr a macro?
    '''
    if pos>0:
        temp = texStr[0:pos]
        temp = temp.split()
        if len(temp)==0:
            return False
        temp = temp[-1].strip()
        isMacro = temp.find('\\')+1
        if isMacro:
            return True
        else:
            return False
    else:
        return False

def isRightWordMacro(texStr,pos):
    '''
    Is the word to the right of pos in texStr a macro?
    '''
    if pos<len(texStr):
        temp = texStr[pos+1:]
        temp = temp.split()
        if len(temp)==0:
            return False
        temp = temp[0].strip()
        isMacro = temp.find('\\')+1
        if isMacro:
            return True
        else:
            return False
    else:
        return False

def getMacro(texStr,pos):
    '''
    Return macro which contains the name of the macro
    (without the \).
    '''
    macro = 'previousMacro'

    if isRightWordMacro(texStr,pos):
        temp = texStr[pos+1:].split()
        macro = temp[0].strip()
        
    if isLeftWordMacro(texStr,pos):
        temp = texStr[0:pos].split()
        macro = temp[-1].strip()

    macro = macro.replace('\\','')
    return macro

def getParseTree(texStr):
    '''
    Recursively build a parse tree of the preprocessed LaTeX
    source. The tree is implemented as list of tuples. The first item
    in the tuple is the macro name and the second item is the text
    belonging to that element. Returns the tree.
    '''
    bracePairs = findBraces(texStr)
#    print 'recursing on ', texStr
#    print 'braces: ', bracePairs
    # are we at a leaf? in other words, are there no braces?
    if len(bracePairs)==0:
        return [('null', texStr)]
    # divide the texStr into 3 parts: left, middle, right
    # left is the text before the first left brace
    # center is the text in the outer braces
    # right is the text beyond the last right brace
    else:
        nextBraces = bracePairs[0]
        nextLeftBraceIndex = nextBraces[0]
        nextRightBraceIndex = nextBraces[1]
        macro = getMacro(texStr,nextLeftBraceIndex)
        
        left = texStr[:nextLeftBraceIndex]
        center = texStr[nextLeftBraceIndex+1:nextRightBraceIndex-1]
        right = texStr[nextRightBraceIndex:]
        
        if isLeftWordMacro(texStr,nextLeftBraceIndex):
            x1 = left.rfind('\\'+macro)
            left = left[:x1]
        if isRightWordMacro(texStr,nextLeftBraceIndex):
            x1 = center.find('\\'+macro)
            x2 = x1 + len('\\'+macro)
            center = center[:x1]+center[x2:]

        return getParseTree(left) + [(macro,getParseTree(center))] + getParseTree(right)


def deparse(pt):
    '''
    Deparse the tree, adding wiki markup as specified in
    CODE_DICTIONARY above.
    '''
    outstr = ""
    for tup in pt:
        cdVal = CODE_DICTIONARY[tup[0]]
        if type(cdVal)==type((1,2)):
            if len(cdVal)==2:
                pre = cdVal[0]
                post = cdVal[1]
            else:
                pre = cdVal[0]
                post = cdVal[0]
        else:
            pre = cdVal
            post = cdVal

        if type(tup[1])==type(''):
            outstr = outstr + pre + tup[1].strip(' ') + post
#            outstr = outstr + pre + tup[1] + post
            if len(outstr)==0:
                outstr = outstr
            elif not outstr[-1]=='\n':
                outstr = outstr + ' '
        else:
            outstr = outstr + pre + deparse(tup[1]).strip(' ') + post + ' '
    return outstr

def getBblDictionary(bblFilename):
    '''
    Returns a dictionary associating citation keys with citation text,
    from the BBL file specified by bblFilename. This is extremely
    kludgy. Sorry.
    '''
    tagdict = {}
    tag = 'junk'
    data = ''
    bblFid = open(bblFilename,'r')
    for s in bblFid:
        if s.find('\\bibitem')+1:
            # write the previous tag and data to dicitonary
            tagdict[tag] = data
            startpoint = s.find('\\bibitem{')
            endpoint = s.find('}')
            substr = s[startpoint:endpoint+1]
            tag = substr.replace('\\bibitem{','')
            tag = tag.replace('}','')
            data = ''
        else:
            s = s.replace('\n',' ')
            if s.find('\\newblock ')+1:
                s = s.replace('\\newblock ','')
            if s.find('~')+1:
                s = s.replace('~',' ')
            containsyear = False
            for sitem in s.split():
                if sitem[-1]=='.':
                    temp = sitem[0:-1]
                    if (temp[0]=='1' or temp[0]=='2') and isNumber(temp) and len(temp)==4:
                        myyear = temp+'.'
                        containsyear = True

            if containsyear and BOLDFACE_YEARS:
                s = s.replace(myyear,'{\\bf '+myyear[0:4]+'}'+'.')
            s = s.replace('\end{thebibliography}','')

            data = data + s
    # write the last item:
    tagdict[tag] = data
    bblFid.close()
    return tagdict


def replacePublications(texStr):
    '''
    Replace the \publication macros in the LaTeX source with the
    citation text. This is done before building the parse tree, so
    that LaTeX macros employed in the BBL file are parsed and recoded
    correctly.
    '''
    done = not texStr.find('\\publication{')+1
    while not done:
        ploc = texStr.find('\\publication{')
        closeIdx = texStr.find('}',ploc)
        openIdx = texStr.find('{',closeIdx)
        closeIdx = texStr.find('}',openIdx)
        tag = texStr[openIdx+1:closeIdx]
        pubdata = bblDict[tag]
        pubdata = pubdata.replace('.','. ')
        pubdata = pubdata.replace(',',', ')
        pubdata = '\n'+' '.join(pubdata.split())
        texStr = texStr[:ploc] + pubdata + texStr[closeIdx+1:]
        done = not texStr.find('\\publication{')+1
    return texStr


def getTexString(filename):
    '''
    Here we do any preprocessing that requires lines of text from the
    file; it's a convenient place to do it since we're reading
    the lines one at a time anyway.

    Preprocessing latex lines:

    1. remove comments, whether they take up a whole line or end a
    line(but preserve \%)

    2. remove '\noindent's

    3. Use PREPROCESS_REMOVE_LINES_TABLE and PREPROCESS_REPLACE_TABLE
    to modify the text according to their rules (see top of this file
    for more info).

    4. Return just the preprocessed text between \begin{document} and
    \end{document}
'''
    texFid = open(filename,'r')
    texString = ''
    for s in texFid:
        newlines = 0
        if not s[0]=='%':
            if s.find('%')+1:
                commentStart = s.find('%')
                if not s[commentStart-1]=='\\':
                    s = s[0:commentStart]
            for item in PREPROCESS_REMOVE_LINES_TABLE:
                if s.find(item)+1:
                    s = ''
                    newlines = newlines + 1
            if s.strip()=='\\noindent':
                s = ''
            s = s.strip()
            if len(s):
                texString = texString + s + '\n'
            else:
                texString = texString + newlines*'\n'
    texFid.close()
    if texString.find('\\begin{document}')+1:
        usableStart = texString.find('\\begin{document}')
        usableEnd = texString.find('\\end{document}') + 14
        texString = texString[usableStart:usableEnd]
    texString = texString.replace('\\begin{document}','')
    texString = texString.replace('\\end{document}','')
    for tup in PREPROCESS_REPLACEMENT_TABLE:
        texString = texString.replace(tup[0],tup[1])
    return texString.strip()


# Here's where the program begins to do stuff:

# preprocess
texString = getTexString(fnTag + '.tex')

# get the BBL dictionary
bblDict = getBblDictionary(fnTag + '.bbl')

# insert pubs
texString = replacePublications(texString)

# get the parse tree
pt = getParseTree(unifyMacros(texString))

# convert to wiki text:
outtxt = deparse(pt)

# postprocess the wiki text:
for tup in POSTPROCESS_REGEX_REPLACEMENT_TABLE:
    outtxt = re.sub(tup[0],tup[1],outtxt)

# print it
print outtxt
