# Municipal Money

Municipal Money is a project between the [South African National Treasury](http://www.treasury.gov.za/) and [Code for South Africa](http://code4sa.org) to
make municipal finance information available to the public. It is made up of a citizen-facing app and an API.

# Local development

1. clone this repo
2. install dependencies: ``pip install -r requirements.txt``
3. create a postgresql user with password ``municipal_finance``: ``createuser municipal_finance -W``
4. create a database: ``createdb municipal_finance -O municipal_finance``
5. install data from somewhere :)
6. run it: ``python manage.py runserver``

# Production

```
dokku config:set municipal-finance DJANGO_DEBUG=False \
                                   DISABLE_COLLECTSTATIC=1 \
                                   DJANGO_SECRET_KEY=... \
                                   NEW_RELIC_APP_NAME=municipal_finance \
                                   NEW_RELIC_LICENSE_KEY=... \
                                   DATABASE_URL=postgres://municipal_finance:...@postgresq....amazonaws.com/municipal_finance
```

# Initial Data Import

Data import is still a fairly manual process leveraging the DB and a few SQL scripts to do the hard work. This is usually done against a local DB, sanity checked with a locally-running instance of the API and some tools built on it, and if everything looks ok, dumped table-by-table with something like `pg_dump "postgres://municipal_finance@localhost/municipal_finance" --table=audit_opinions -O -c --if-exists > audit_opinions.sql` and then loaded into the production database.

1. Create the population table with `cat sql/create/030_population_2011.sql | psql municipal_finance`
2. `python manage.py migrate`
3. Create the tables with `cat sql/create/* | psql municipal_finance`
4. Import the first few columns of the fact tables which are supplied by National Treasury
 - e.g. `psql# \copy incexp(demarcation_code, period_code, function_code, item_code, amount) FROM '/bob/incexp_2015q4.csv' DELIMITER ',' CSV HEADER`
5. Run `sql/decode_period_code.sql` to populate the remaining columns from the period code
  - These should be idempotent so they can simply run again when data is added.
6. Import the dimension table data from `municipal_finance/data_import/dimension_tables`
7. Make sure `create_indices.sql` and its indices are up to date
  - create it with the python module `municiapl_finance.data_import.create_indices`
  - add it to git and run it if it was changed
  - the prod DB doesn't support CREATE INDEX IF NOT EXISTS yet so ignore errors for existing indices unless their columns changed and they need to be manually removed and recreated.

*Remember to run `VACUUM ANALYSE` or REINDEX tables after significant changes to ensure stats are up to date to use indices properly.*

# Standard Operating Procedure

This covers how to keep the data up to date. Each quarter, as new data is released, the following needs to be done to update the data served by the API and the Citizen Scorecard. It's best to do this on a test database first and verify the results before updating the production database.

## Extract CSV datasets from Excel Spreadsheets

Extract CSV datasets from Excel Spreadsheets using the following scripts in `municipal_finance/data_import/`

- audit_opinions.py
- contact_details.py
- bad_expenditure.py

## Scrape http:/mfma.treasury.gov.za for the Audit Report URLs into a CSV file

Using `municipal_finance/data_import/audit_reports`

## Insert/update from CSV files

1. Update the paths in the per-cube files in `sql/upsert/`
2. Execute the files

These files work as follows:

1. Create a temporary table
2. Import the CSV file to the temporary table
3. Decode the `period_code` column into dedicated columns (Some Financial datasets only)
4. Update values  in the fact table that already exist
5. Insert new rows to the fact table

Update the model last-updated date in the model files for each cube in `models/*.json`

## Annual data

Whenever 4th Quarter data becomes available, typically 2 quarters after that financial year end, also adjust the years used by `scorecard/profile_data.py` to include the latest financial year available.

# License

MIT License
