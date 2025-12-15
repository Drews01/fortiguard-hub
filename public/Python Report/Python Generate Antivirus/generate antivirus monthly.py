#!/usr/bin/env python3
import sys
from datetime import datetime

# Simple placeholder monthly generator for Antivirus
# Accepts optional month argument in YYYYMM or YYYY_MM or YYYY-MM

def normalize_month(arg):
    if not arg:
        # default to last month
        from datetime import date
        today = date.today()
        year = today.year
        month = today.month - 1
        if month == 0:
            month = 12
            year -= 1
        return f"{year}{month:02d}"
    return arg.replace('-', '').replace('_', '')

if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    norm = normalize_month(arg)
    print(f"Antivirus monthly generator called with month: {norm}")
    # TODO: implement aggregation of daily_reports into monthly report
