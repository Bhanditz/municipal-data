from django.core.management.base import BaseCommand
import csv
from pprint import pprint
import re
from collections import defaultdict

REGEXES = {
    'decimal_lon_lat': '^(?P<lon>\d+[\.,]\d+)[\s;,]+(?P<lat>-\d+[\.,]\d+)$',
    'decimal_lat_lon_labeled': '^Latitude: (?P<lat>-\d+\.\d+)[ |;,]+Longt?itude: (?P<lon>\d+\.\d+)$',
    'decimal_lat_lon': '^(?P<lat>-\d+[\.,]\d+)[ ;,]+(?P<lon>\d+[\.,]\d+)$',
    'decimal_lat_neg_lon': '^(?P<lon>3\d+[\.,]\d+)[ ;,]+(?P<lat>2\d+[\.,]\d+)$',
    'decimal_Slat_neg_Elon': '^S(?P<lat_neg>\d+[\.,]\d+)[ ;]+E(?P<lon>\d+[\.,]\d+)$',
    'dms_lat_negS_lonE': '^(?P<lat_neg>\d+[\xB0\xBA] ?\d+\' ?\d+\.\d+")S *(?P<lon>\d+[\xB0\xBA] ?\d+\' ?\d+\.\d+")E$',
    'dms_lon_lat': '^(?P<lon>\d+[\xB0\xBA] ?\d+\' ?\d+") *(?P<lat>-\d+[\xB0\xBA] ?\d+\' ?\d+")$',
    'dms_lat_negS_lonE_comma': '^(?P<lat_neg>\d+\.\d+\.\d+,\d+) ?S *(?P<lon>\d+\.\d+\.\d+,\d+) ?E$',
    'dms_lat_negS_lonE_qmark': '^(?P<lat_deg_neg>\d+)\?(?P<lat_min>\d+)\'(?P<lat_sec>\d+\.\d+)(''|")S *(?P<lon_deg>\d+)\?(?P<lon_min>\d+)\'(?P<lon_sec>\d+\.\d+)(''|")E$',
    'known_non_coord': '^(N/A|n/a|0|[ a-zA-Z]+)?$',
}

FIELDNAMES = [
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


class Command(BaseCommand):
    help = 'Maintenance operations for SA36 Capital Spending Detail data'

    def add_arguments(self, parser):
        parser.add_argument('infile', type=str)

    def handle(self, *args, **options):
        compiled_rxs = compile_regexes()
        counts = defaultdict(int)
        with open(options['infile'], 'rb') as f:
            reader = csv.DictReader(f, fieldnames=FIELDNAMES)
            for row in reader:
                match = False
                for regex_name, regex in compiled_rxs.iteritems():
                    match = regex.match(row['coordinates'].strip())
                    if match:
                        counts[regex_name] += 1
                        #print("%s [%s] %s %s" % (row['demarcation_code'], row['coordinates'], row['proj_desc'], row['asset_class']))
                        #pprint(match.groupdict())
                        break
                if not match:
                    pprint("%s [%s] %s %s" % (row['demarcation_code'], row['coordinates'], row['proj_desc'], row['asset_class']))
                    counts['no_match'] += 1
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
