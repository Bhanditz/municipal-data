from django.core.management.base import BaseCommand
import csv

FIELDNAMES = [
    "demarcation_code",
    "YEARPERIOD",
    "T_SEQ",
    "Project Decription",
    "Project No",
    "IDP Goal Code",
    "Approved Y/N",
    "Asset Class",
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
        with open(options['infile'], 'rb') as f:
            reader = csv.DictReader(f, fieldnames=FIELDNAMES)
            for row in reader:
                print(row['coordinates'])
