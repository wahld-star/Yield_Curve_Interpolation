#import Packages
import datetime as dt
import requests as rq
import xml.etree.ElementTree as ET

class Treasury_Data:

    Data_Key = {
        "BC_1MONTH":    ("1M", 1/12),
        "BC_1_5MONTH":  ("1.5M", 1.5/12),
        "BC_2MONTH":    ("2M", 2/12),
        "BC_3MONTH":    ("3M", 3/12),
        "BC_4MONTH":    ("4M", 4/12),
        "BC_6MONTH":    ("6M", 6/12),
        "BC_1YEAR":     ("1Y", 1),
        "BC_2YEAR":     ("2Y", 2),
        "BC_3YEAR":     ("3Y", 3),
        "BC_5YEAR":     ("5Y", 5),
        "BC_7YEAR":     ("7Y", 7),
        "BC_10YEAR":    ("10Y", 10),
        "BC_20YEAR":    ("20Y", 20),
        "BC_30YEAR":    ("30Y", 30),
    }

    NS = {
        "atom": "http://www.w3.org/2005/Atom",
        "d":    "http://schemas.microsoft.com/ado/2007/08/dataservices",
        "m":    "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
    }


    def __init__(self, date: str):
        fmt = "%m-%d-%Y"
        self.date = dt.datetime.strptime(date, fmt)
        self.xml_pull = None
        self.maturity_map = dict(self.Data_Key)
        self.maturity_labels = [n[0] for n in self.maturity_map.values()]
        self.maturity_floats = [n[1] for n in self.maturity_map.values()]
        self.input_rates = {}
        self.fmt_load(self.date) #Loads format data before raw pull
        self.tdata_xml_pull() #pulls from treasury xml feed and fills rates data

    #Sets URL for treasury XML feed
    def fmt_load(self, date=None):
        archive_date = dt.datetime(2024, 1, 1)          #rates before 2025 in treasury archive
        base_url = 'https://home.treasury.gov'

        if date <= archive_date:
            endpoint  = '/resource-center/data-chart-center/interest-rates/daily-treasury-rate-archives/par-yield-curve-rates-1990-2023.xml'
            self.xml_pull   = base_url + endpoint
        else:
            endpoint    = '/resource-center/data-chart-center/interest-rates/pages/xml'
            date_format = date.strftime("%Y%m")
            self.xml_pull     = f"{base_url}{endpoint}?data=daily_treasury_yield_curve&field_tdr_date_value_month={date_format}"

    #Parses XML feed to define what rates were issues at that date
    def parse_xml_feed(self, props, active_labels):
        yields = {}
        for child in props:
            tag = child.tag.split("}", 1)[-1]

            mapping = self.maturity_map.get(tag)
            if mapping is None:
                continue

            label, _years = mapping
            if label not in active_labels:
                continue

            text = (child.text or "").strip()
            if not text:
                continue

            try:
                yields[label] = float(text)
            except ValueError:
                continue
        return yields

    #main XML pull, handles holidays and weekends
    def tdata_xml_pull(self, maturities: list = None, loobal: int = 3) -> dict:
        fmt      = "%m-%d-%Y"
        #looks at previous 3 days to check if month changes
        Lookback = 3
        results  = {}
        # cache: month_key -> (response, maturity_map) to avoid redundant HTTP calls
        months_checked = {}

        active_labels = (set(maturities) if maturities else {v[0] for v in self.maturity_map.values()})

        for m in range(Lookback):
            current_search_date = self.date - dt.timedelta(days=m)
            month_key           = current_search_date.strftime("%Y%m")

            if month_key not in months_checked:
                self.fmt_load(current_search_date)
                response = rq.get(self.xml_pull)
                response.raise_for_status()
                months_checked[month_key] = (response)
            else:
                response = months_checked[month_key]

            root = ET.fromstring(response.content)
            date_found = False
            target = current_search_date.replace(hour=0,minute=0, second=0, microsecond=0)


            for entry in root.findall("atom:entry", self.NS):
                props = entry.find(".//m:properties", self.NS)
                if props is None:
                    continue

                date_el = props.find("d:NEW_DATE", self.NS)
                if date_el is None or not date_el.text:
                    continue

                try:
                    entry_date = dt.datetime.strptime(date_el.text.strip(), "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    continue

                if entry_date != target:
                    continue

                yields = self.parse_xml_feed(props, active_labels)
                if yields:
                    results[entry_date.strftime(fmt)] = yields
                    date_found = True
                break

            if date_found:
                break

        self.input_rates = list(next(iter(results.values())).values())
        #Update shape of maturity labels and floats
        present_rates = set(next(iter(results.values()))) if results else set()
        self.maturity_labels = []
        self.maturity_floats = []
        for label, years in self.maturity_map.values():
            if label in present_rates:
                self.maturity_labels.append(label)
                self.maturity_floats.append(years)
