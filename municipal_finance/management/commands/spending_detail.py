from django.core.management.base import BaseCommand
import csv
from pprint import pprint
import re
from collections import defaultdict
from decimal import Decimal

REGEXES = {
    'decimal_lon_lat': '^(?P<lon>\d+[\.,]\d+)[\s;,:/]+(?P<lat>-\d+[\.,]\d+)$',
    'decimal_lon_lat_multi': '^(?P<lon>\d+[\.,]\d+)[\s;,:/]+(?P<lat>-\d+[\.,]\d{3,6})[\d\s\.,\-]+$',
    'decimal_lon_lat_labeled': '^[Ll]ong *= *(?P<lon>\d+[\.,]\d+)[\s;,/]+[Ll]at *= *(?P<lat>-\d+[\.,]\d+)$',
    'decimal_lon_lat_neg_labeled': '^[Ll]ong *= *(?P<lon>\d+[\.,]\d+)[\s;,/]+[Ll]at *= *(?P<lat_neg>\d+[\.,]\d+)$',
    'decimal_lat_lon_labeled': '^Latitude: (?P<lat>-\d+\.\d+)[ |;,/]+Longt?itude: (?P<lon>\d+\.\d+)$',
    'decimal_lat_lon': '^(?P<lat>-\d+[\.,]\d+)[\s;,/]+(?P<lon>\d+[\.,]\d+)$',
    'decimal_lat_lon_unseparated': '^(?P<lat>-\d+[\.,]\d+)(?P<lon>\d{2}[\.,]\d+)$',
    'decimal_lat_neg_lon': '^(?P<lat_neg>3\d+[\.,]\d+)[ ;,\-&/]+(?P<lon>[12]\d+[\.,]\d+)$',
    'decimal_lon_lat_neg': '^(?P<lon>[12]\d+[\.,]\d+)[ ;,\-&/]+(?P<lat_neg>3\d+[\.,]\d+)$',
    'decimal_Slat_neg_Elon': '^S(?P<lat_neg>\d+[\.,]\d+)[ ;/]+E(?P<lon>\d+[\.,]\d+)$',
    'decimal_lat_negS_lonE': '^(?P<lat_neg>\d+[\.,]\d+) *S[ ;/]+(?P<lon>\d+[\.,]\d+) *E$',
    'decimal_lat_negS_lonE_deg': '^(?P<lat_neg>\d+[\.,]\d+)[ \xB0]+S[ ;/]+(?P<lon>\d+[\.,]\d+)[ \xB0]+E$',
    'dms_lat_negS_lonE_spaced': '^(?P<lat_deg_neg>\d+) (?P<lat_min>\d+) (?P<lat_sec>\d+) s / (?P<lon_deg>\d+) (?P<lon_min>\d+) (?P<lon_sec>\d+) e$',
    'dms_lat_negS_lonE': '^(?P<lat_deg_neg>\d+)[\xB0\xBA,] ?(?P<lat_min>\d+)[\',] ?(?P<lat_sec>(\d+|\.\d+|\d+.|\d+\.\d+))(,|\"|\'\') ?S[ |/]*(?P<lon_deg>\d+)[\xB0\xBA,] ?(?P<lon_min>\d+)[,\'] ?(?P<lon_sec>(\d+|\.\d+|\d+.|\d+\.\d+))(,|\"|\'\') ?E$',
    'dms_lat_negS_lonE_zero_simple': '^(?P<lat_deg_neg>\d{2})0(?P<lat_min>\d+)`(?P<lat_sec>\d+)"S,(?P<lon_deg>\d{2})0(?P<lon_min>\d+)`(?P<lon_sec>\d+)"E,?$',
    'dms_Slat_Elon_backticks': '^S *-(?P<lat_deg>\d{2})[\xB0\xBA,0\-] ?(?P<lat_min>\d{2})[`\',] ?(?P<lat_sec>[\d+\.]+)(,|\"|\'\'|``) *E *(?P<lon_deg>\d{2})[\xB0\xBA,0\-] ?(?P<lon_min>\d{2})[,\'`] ?(?P<lon_sec>[\d+\.]+)(,|\"|\'\'|``)$',
    'dms_lat_negS_lonE_comma': '^(?P<lat_deg_neg>\d+)\.(?P<lat_min>\d+)\.(?P<lat_sec>\d+,\d+) ?S *(?P<lon_deg>\d+)\.(?P<lon_min>\d+)\.(?P<lon_sec>\d+,\d+) ?E$',
    'dms_lat_negS_lonE_qmark': '^(?P<lat_deg_neg>\d+)\?(?P<lat_min>\d+)\'(?P<lat_sec>\d+\.\d+)(\'\'|\")S *(?P<lon_deg>\d+)\?(?P<lon_min>\d+)\'(?P<lon_sec>\d+\.\d+)(\'\'|\")E$',
    'dms_lon_lat': '^(?P<lon_deg>\d+)[\xB0\xBA] ?(?P<lon_min>\d+)\' ?(?P<lon_sec>\d+)\" *(?P<lat_deg>-\d+)[\xB0\xBA] ?(?P<lat_min>\d+)\' ?(?P<lat_sec>\d+)\"$',
    'dms_lonE_lat_negS': '^(?P<lon_deg>\d+)[\xB0\xBA] ?(?P<lon_min>\d+)[\'\?] ?(?P<lon_sec>(\d+|\.\d+|\d+.|\d+\.\d+))(\"|\'\') *E,? *(?P<lat_deg_neg>\d+)[\xB0\xBA] ?(?P<lat_min>\d+)[\'\?] ?(?P<lat_sec>(\d+|\.\d+|\d+.|\d+\.\d+))(\"|\'\') *S$',
    'dms_lon_lat_neg_labeled': '^Long? *=? *(?P<lon_deg>\d+)[\xB0\xBA\'] ?(?P<lon_min>\d+)\' ?(?P<lon_sec>(\d+|\.\d+|\d+.|\d+\.\d+))\"[ ,=]*Lat *=? *(?P<lat_deg_neg>\d+)[\xB0\xBA\'] ?(?P<lat_min>\d+)\' ?(?P<lat_sec>(\d+|\.\d+|\d+.|\d+\.\d+))[\'\"]*$',
    'dms_lon_lat_labeled': '^Long? *=? *(?P<lon_deg>\d+)[\xB0\xBA\'] ?(?P<lon_min>\d+)\' ?(?P<lon_sec>(\d+|\.\d+|\d+.|\d+\.\d+))\"[ ,=]*Lat *=? *-(?P<lat_deg>\d+)[\xB0\xBA\'] ?(?P<lat_min>\d+)\' ?(?P<lat_sec>(\d+|\.\d+|\d+.|\d+\.\d+))[\'\"]*$',
    'known_non_coord': '^(N/A|n/a|0|[ a-zA-Z]+|-?\d{2}[,.]\d+|\d+|\w+|[\w\(\)\- ]+|\d+\xB0\d+\'\d+\.\d+\"[SE])?$',
}

IN_FIELDNAMES = [
    "demarcation_code",
    "YEARPERIOD",
    "T_SEQ",
    "proj_desc",
    "Project No",
    "IDP Goal Code",
    "Approved Y/N",
    "asset_class",
    "Asset Sub-Class",
    "coordinates",
    "Total Project Estimate",
    "Ward Location",
    "New/Renewal",
    "ACT_OR_BUD"
]

PARSED_FIELDNAMES = [
    "demarcation_code",
    "YEARPERIOD",
    "T_SEQ",
    "proj_desc",
    "Project No",
    "IDP Goal Code",
    "Approved Y/N",
    "asset_class",
    "Asset Sub-Class",
    "longitude",
    "latitude",
    "coordinates_supplied",
    "Total Project Estimate",
    "Ward Location",
    "New/Renewal",
    "ACT_OR_BUD"
]


class Command(BaseCommand):
    help = 'Maintenance operations for SA36 Capital Spending Detail data'

    def add_arguments(self, parser):
        parser.add_argument('infile', type=str)

    def handle(self, *args, **options):
        compiled_rxs = compile_regexes()
        counts = defaultdict(int)
        muni_counts = defaultdict(int)
        with open(options['infile'], 'rb') as infile:
            with open('unparsed.csv', 'wb') as unmatched_file:
                reader = csv.DictReader(infile, fieldnames=IN_FIELDNAMES)
                writer = csv.DictWriter(unmatched_file, fieldnames=PARSED_FIELDNAMES)
                for row in reader:
                    match = False
                    coordstr = row['coordinates'].strip().replace('\xa0', ' ')
                    for regex_name, regex in compiled_rxs.iteritems():
                        match = regex.match(coordstr)
                        if match:
                            counts[regex_name] += 1
                            #pprint((regex_name, match.groupdict()))
                            coords = format_coords(regex_name, match.groupdict())
                            if coords:
                                print("%s %s [%s] %s" % (row['demarcation_code'], coords, row['coordinates'], row['proj_desc']))
                            break
                    if not match:
                        #pprint("%s [%s] %s %s" % (row['demarcation_code'], coordstr, row['proj_desc'], row['asset_class']))
                        counts['no_match'] += 1
                        muni_counts[row['demarcation_code']] += 1
            print
            for muni, count in sorted(muni_counts.iteritems(), key=lambda x: x[1], reverse=True)[0:5]:
                print("%s\t\t%s" % (muni, count))
            print
            total = 0
            for key in sorted(counts.keys()):
                total += counts[key]
                print("%s\t%d" % (key, counts[key]))
            print("TOTAL\t\t%d" % total)


def compile_regexes():
    compileds = {}
    for key, value in REGEXES.iteritems():
        print("Compiling %s" % key)
        compileds[key] = re.compile(value)
    return compileds


def format_coords(regex_name, groupdict):
    if regex_name.startswith('decimal_'):
        print regex_name, groupdict
        if '_neg' in regex_name:
            lat = str(Decimal(groupdict['lat_neg'].replace(',', '.')).copy_negate())
            lon = str(Decimal(groupdict['lon'].replace(',', '.')))
        else:
            lat = str(Decimal(groupdict['lat'].replace(',', '.')))
            lon = str(Decimal(groupdict['lon'].replace(',', '.')))
        return (lat, lon)
    elif regex_name.startswith('dms_'):
        print regex_name, groupdict
        if '_neg' in regex_name:
            lat = str(-dms2dd(groupdict['lat_deg_neg'], groupdict['lat_min'], groupdict['lat_sec'].replace(',', '.')))
            lon = str(dms2dd(groupdict['lon_deg'], groupdict['lon_min'], groupdict['lon_sec'].replace(',', '.')))
        else:
            lat = str(dms2dd(groupdict['lat_deg'], groupdict['lat_min'], groupdict['lat_sec'].replace(',', '.')))
            lon = str(dms2dd(groupdict['lon_deg'], groupdict['lon_min'], groupdict['lon_sec'].replace(',', '.')))
        return (lat, lon)


def dms2dd(degrees, minutes, seconds):
    dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
    return dd;
