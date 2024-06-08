# Tauron statistics review

This repository contains a python scripts that can check your energy usage statistics (based on unofficial API from eLicznik service) and show them in a form of a simple ASCII table.

**Disclaimer: Use at Your Own Risk. ⚠️**

## Features

* Gathering and aggregating data from eLicznik
* Calculating balance, "positive-days" and estimated cost
* Maintaining a cache file (`cache.csv`) to avoid unnecessary API calls (data from this file can be easily loaded to a spreadsheet)
* Generating an ASCII table with monthly data
* Calculating a simple estimation for the current month

## Requirements
* python 3.11+
* packages from `requirements.txt`

# Configuration file

To use this script you need to create a configuration (`config.yml`) based on the example (`config.example.yml`).

Required values:
* `meter_id`
* `username`
* `password`
* `installation_date` ("YYYY-MM-DD" format)

Optional values:
* `price`
* `fixed_cost`
* `extra_headers`

## Usage examples

```
python3 tauron_statistics.py --help
python3 tauron_statistics.py
python3 tauron_statistics.py -y
python3 tauron_statistics.py -y 2022 --off
python3 tauron_statistics.py -y --no-cache
```
