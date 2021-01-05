# yacreader projects

This repository is for any random code that can be used with the yacreader project https://www.yacreader.com

I created a script in Python which people interested in this forum topic may find useful as a short term workaround. 
https://www.yacreader.com/forum/suggestions/421-comicbook-lover-comicrack-metadata-compatibility

It loads records from the yacreader sqlite3 database, checks each zip file for a comic rack xml metadata file, and if one exists it updates the yacreader db file with the info it found. It ignores any records that don't have an xml file, but will completely overwrite the db record for any issues that do have an xml file.

I tested with my collection of 40,000 files that I had tagged with Comic Vine API and edited with Comic Tagger a few years ago and caught a bunch of exceptions, but your mileage may vary. Please make a backup copy of your .yacreader/library.ydb file before you run this in case anything goes wrong.

Put the code into a file callled 'yacxmlupdater.py' and make it executable. You may need to edit the first line of the script to point to your local installation of Python 3, on my Mac it was '#!/usr/bin/python3'

Execute the file and tell it where your library directory is and the maximum number of records to update, example:

```
./yacxmlupdater.py --library /Volumes/comics --max 100
```
