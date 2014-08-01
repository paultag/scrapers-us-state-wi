# division, jxn, name

import csv
import sys

(csvf,) = sys.argv[1:]

with open(csvf, 'r') as fd:
    for row in csv.DictReader(fd):
        did = row['Division']
        jid = "%s/government" % (
            did.replace("ocd-division", "ocd-jurisdiction"))
        name = "%s, %s" % (row['Place'], row['State'])

        print("%s,%s,%s" % (did, jid, name))
