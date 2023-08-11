import logging
import requests
import datetime
import pickle
import os
from typing import Any, Dict, List, Optional

from fake_useragent import UserAgent

class CapitolTrades():
    """A class for interacting with the API which supports https://capitoltrades.com."""

    def __init__(self, window=100):
        """init varz"""
        self.__url = "https://bff.capitoltrades.com"
        self.__ua = UserAgent()
        self.__session = requests.Session()
        self.__session.get("https://bff.capitoltrades.com/trades")
        self.__pkl_path = "data/trades.pkl"
        self.window = window # days before today of trades to consider
        self.data = None
        try:
            self.update_data()
        except Exception as e:
            raise Exception("Error initializing: " + str(e))

    def __get_headers(self) -> Dict[str, Any]:
        """Generates headers for the Capitol Trades API."""
        return {
            "User-Agent": self.__ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "Origin": "https://bff.capitoltrades.com",
            "DNT": "1",
            "Connection": "keep-alive",
            "Referer": "https://bff.capitoltrades.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Sec-GPC": "1",
            "Cache-Control": "max-age=0",
            "TE": "trailers",
        }

    def __get_data(self) -> Optional[Dict]:
        """Gather trading data from https://capitoltrades.com"""
        script_dir = os.path.dirname(__file__)
        if os.path.isfile(os.path.join(script_dir, self.__pkl_path)):
            print("Getting seed data from pickle file.")
            with open(os.path.join(script_dir, self.__pkl_path), "rb") as fp:
                return pickle.load(fp)

        today = datetime.datetime.utcnow().date()
        print("Getting seed data on", today)

        seed_data = []
        page_num = 1
        paginating = True
        while paginating:
            params = (
                ("page", page_num),
                # 100 is the max return size of the API.
                ("pageSize", 100),
            )
            r = self.__session.get(
                self.__url + "/trades",
                headers=self.__get_headers(),
                params=params,
            )
            r.raise_for_status()

            response_json = r.json()
            data = response_json["data"]
            seed_data.extend(data)
            
            days_difference = float('inf')
            
            if data:
                pubDate = datetime.datetime.strptime(data[-1]['pubDate'], '%Y-%m-%dT%H:%M:%SZ').date()
                days_difference = (today - pubDate).days

            if len(seed_data) >= response_json["meta"]["paging"]["totalItems"] or not data or days_difference > self.window:
                paginating = False
            else:
                page_num += 1


        print(f"Got {len(seed_data)} trade records.")
        script_dir = os.path.dirname(__file__)
        with open(os.path.join(script_dir, self.__pkl_path), "wb") as fp:
            pickle.dump(seed_data, fp)

        return seed_data
    
    def update_data(self):
        today = datetime.datetime.utcnow().date()
        print("Updating data on", today)
        
        if not self.data:
            self.data = self.__get_data()
        else:
            latestPubDate = datetime.datetime.strptime(self.data[0]['pubDate'], '%Y-%m-%dT%H:%M:%SZ').date()
            new_data = []
            page_num = 1
            paginating = True
            while paginating:
                params = (
                    ("page", page_num),
                    # 100 is the max return size of the API.
                    ("pageSize", 100),
                )
                r = self.__session.get(
                    self.__url + "/trades",
                    headers=self.__get_headers(),
                    params=params,
                )
                r.raise_for_status()

                response_json = r.json()
                data = response_json["data"]
                new_data.extend(data)

                days_difference_window = float('inf') # for if window is in data
                days_difference_data = -1 # for if we already have this data
                if data:
                    pubDate = datetime.datetime.strptime(data[-1]['pubDate'], '%Y-%m-%dT%H:%M:%SZ').date()
                    days_difference_window = (today - pubDate).days 
                    days_difference_data = (pubDate - latestPubDate).days
                print(days_difference_window, days_difference_data)

                if len(new_data) >= response_json["meta"]["paging"]["totalItems"] or not data or days_difference_window > self.window or days_difference_data <= 0:
                    paginating = False
                else:
                    page_num += 1
            
            
            print(len(new_data), len(self.data))
            # merge new_data with existing data and remove stale data
            seen = set()
            merged_data = []
            for item in new_data + self.data:
                pubDate = datetime.datetime.strptime(item['pubDate'], '%Y-%m-%dT%H:%M:%SZ').date()
                days_diff = (today - pubDate).days
                if item["_txId"] not in seen and days_diff <= self.window:
                    seen.add(item["_txId"])
                    merged_data.append(item)
                    
            print(f"Merged {len(new_data)} new records and {len(self.data)} old records into {len(merged_data)} total records.")

            script_dir = os.path.dirname(__file__)
            with open(os.path.join(script_dir, self.__pkl_path), "wb") as fp:
                pickle.dump(merged_data, fp)
            self.data = merged_data
            