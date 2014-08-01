from collections import defaultdict
import xlrd
import sys
import csv


def load_mapping():
    with open("../jurisdictions.csv", 'r') as fd:
        reader = csv.DictReader(fd)
        for row in reader:
            yield row


def process_district(district):
    objs = [x.strip() for x in district.split("-")]
    # http://www.dot.wisconsin.gov/localgov/highways/docs/cvtindex.pdf
    # for CVT codes. Nothing better :\
    try:
        place, identifier = objs
        ret = {"place": place,
               "cvt": identifier,
               "extra": ""}
    except ValueError:
        place, extra, identifier = objs
        ret = {"place": place,
               "cvt": identifier,
               "extra": extra}

    return ret


def normalize(person):
    # {'WorkPhone': '', 'HomePhone': '',
    #  'JurisdictionName': 'CITY OF KAUKAUNA - MAIN - 45241',
    #  'CityStateZip': 'KAUKAUNA, WI  54130-3040',
    #  'TermStartDate': 1.0,
    #  'TermEndDate': 1.0}

    translate = {
        "LastName": "Last Name",
        "FirstName": "First Name",
        "MiddleName": "Middle Name",

        "DistictName": "Role",   # Yes, it's typo'd.
        "OfficePosition": "Position",

        "Email": "Email",
        "Fax": "Fax",
        "HomePhone": "Phone (Home)",
        "WorkPhone": "Phone (Work)",
    }

    obj = {}

    obj['Address'] = "%s, %s" % (
        person.pop("Address"),
        person.pop("CityStateZip"),
    )

    for k, v in translate.items():
        obj[v] = person.pop(k)

    dconv = lambda args: "%s-%s-%s" % args[:3] if args else None

    obj['Start Date'] = dconv(person.pop("TermStartDate"))
    obj['End Date'] = dconv(person.pop("TermEndDate"))

    jurisdiction = person.pop("JurisdictionName")
    # Index into a mapping

    assert person == {}
    return jurisdiction, obj


def parsedate(sheet, value):
    if value == 1.0:
        return ""  # For some reason some records have nothing here.
    return xlrd.xldate_as_tuple(value, sheet.book.datemode)


def process_sheet(sheet):
    rows = [sheet.row(x) for x in range(sheet.nrows)]
    if rows == []:
        return

    rows = iter(rows)
    header = [x.value for x in next(rows)]
    data = defaultdict(list)

    for row in rows:
        obj = dict(zip(header, [x.value for x in row]))
        district = obj.get('DistictName')
        jurisdiction = process_district(obj.get('JurisdictionName'))
        obj['TermEndDate'] = parsedate(sheet, obj['TermEndDate'])
        obj['TermStartDate'] = parsedate(sheet, obj['TermStartDate'])
        jurisdiction, person = normalize(obj)
        data[jurisdiction].append(person)

    mappings = load_mapping()
    places = defaultdict(dict)

    for mapping in mappings:
        places[mapping['Place'].lower()][
            mapping['Place Type'].lower()
        ] = mapping['Division']

    for key in data.keys():
        jurisdiction_data = data[key]

        jurisdiction = process_district(key)
        placename = jurisdiction['place']
        if placename.endswith("COUNTY"):
            type_ = "COUNTY"
            name = placename.replace(" COUNTY", "")
        else:
            type_, name = placename.split("OF", 1)
        type_, name = type_.strip().lower(), name.strip().lower()

        if name not in places:
            print("Error: %s isn't in known places." % (name))
            continue

        if type_ not in places[name]:
            print("Error: %s (%s) isn't in '%s'" % (
                name, type_, ", ".join(list(places[name].keys()))
            ))
            continue

        did = places[name][type_]
        jid = "%s/government" % (
            did.replace("ocd-division", "ocd-jurisdiction")
        )


        with open("%s.csv" % (placename), 'w') as fd:
            fields = list(jurisdiction_data[0].keys())
            writer = csv.DictWriter(fd, fields)
            for row in jurisdiction_data:
                writer.writerow(row)


def convert(path):
    with open(path, 'rb') as fd:
        book = xlrd.open_workbook(file_contents=fd.read())
        for sheet in book.sheets():
            process_sheet(sheet)


if __name__ == "__main__":
    convert(*sys.argv[1:])
