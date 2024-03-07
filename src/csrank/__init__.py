#!/usr/bin/env python

import sys
import requests
from bs4 import BeautifulSoup,SoupStrainer
import csv
import urllib
import json
from scholarly import scholarly

def main():
    print("Hello there")
    staff = []
    with requests.get("https://www.cs.manchester.ac.uk/about/people/academic-and-research-staff/") as r:
        soup = BeautifulSoup(r.content)
        rows = soup.find(id="content").find(class_="tabRow")
        if not rows:
            return
        for r in rows.find_all("li"):
            cols = r.find_all("div", recursive=False)
            if not cols:
                continue
            person = len(cols) > 0 and cols[0] or None
            role = len(cols) > 1 and cols[1] or None
            area = len(cols) > 2 and cols[2] or None
            p = {
                "name": person and person.text.strip().replace(person.find(class_="screenreader").text, ""),
                "role": role and role.text.strip().replace(role.find(class_="screenreader").text, ""),
                "area": area and area.text.strip().replace(area.find(class_="screenreader").text, ""),
                "url": None,
                "area_url": None
            }
            url = person and person.find("a")
            if url:
                p["url"] = url["href"].strip()
            area_url = area and area.find("a")
            if area_url:
                p["area_url"] = area_url["href"].strip()
            staff.append(p)

    with open("staff-cs.csv", "w", encoding="utf-8") as f:
        w = csv.writer(f, dialect="excel")
        w.writerow(("name", "role", "url", "area", "area_url"))
        for p in staff:
            w.writerow((p["name"], p["role"], p["url"], p["area"], p["area_url"]))    

    

if __name__ == "__main__":
    main()