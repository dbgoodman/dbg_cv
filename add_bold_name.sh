#!/bin/bash
perl -pe 's/(D(aniel|\.)( B.)? Goodman)/\{\\myname\{$1\}\}/' citations.bib > citations_w_bold.bib
#perl -e 'undef $/; $_=<>; /\@article\{.*Author = \{\{\myname/ && print' citations_w_bold.bib
#perl -e '$/ = "}\n\n"; while ($_ = <>) {/^@article.*?\n\s+Author = \{\{\\myname/ && print}' citations_w_bold.bib