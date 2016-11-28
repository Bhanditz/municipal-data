from django.core.management.base import BaseCommand
import csv
from pprint import pprint
import re

REGEXES = {
    'decimal_lon_lat': '^(\d+.\d+)[ ;]+(-\d+.\d+)$',
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
        with open(options['infile'], 'rb') as f:
            reader = csv.DictReader(f, fieldnames=FIELDNAMES)
            for row in reader:
                for key, value in compiled_rxs.iteritems():
                    match = value.match(row['coordinates'])
                    if match:
                        print("%s [%s] %s %s" % (row['demarcation_code'], row['coordinates'], row['proj_desc'], row['asset_class']))
                        pprint(match.groups())
                        break


def compile_regexes():
    compileds = {}
    for key, value in REGEXES.iteritems():
        print("Compiling %s" % key)
        compileds[key] = re.compile(value)
    return compileds
