#!/usr/bin/env python

import sys
import requests
from bs4 import BeautifulSoup,SoupStrainer
import csv
import urllib
import json
from scholarly import scholarly

def main():
    staff = []

    with open("staff-cs.json", "r", encoding="utf-8") as f:
        staff = json.load(f)

    url_to_staff = {}
    for p in staff:
        if p["url"]:
            if p["url"] in url_to_staff:
                print("Duplicate: ", p)
                sys.exit(1)
            url_to_staff[p["url"]] = p

    with requests.get("https://www.cs.manchester.ac.uk/about/people/academic-and-research-staff/") as r:
        soup = BeautifulSoup(r.content, features="lxml")
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
                "area_url": None,
                "scholar_id": None
            }
            url = person and person.find("a")
            if url:
                p["url"] = url["href"].strip()
            area_url = area and area.find("a")
            if area_url:
                p["area_url"] = area_url["href"].strip()
            staff.append(p)

    for p in staff:
        authors = scholarly.search_author(p["name"] + ", Manchester")
        for cand in authors:
            print(cand)
            if not ("University of Manchester" in cand["affiliation"] or
                "manchester.ac.uk" in cand["email_domain"]):
                continue
            p["scholar_id"] = cand["scholar_id"]
            p["scholar"] = cand
            break


    with open("staff-cs.csv", "w", encoding="utf-8") as f:
        w = csv.writer(f, dialect="excel")
        w.writerow(("name", "role", "url", "area", "area_url", "scholar_id"))
        for p in staff:
            w.writerow((p["name"], p["role"], p["url"], p["area"], p["area_url"], p["scholar_id"]))    

    with open("staff-cs.json", "w", encoding="utf-8") as f:
        json.dump(staff, f, sort_keys=True, indent=4, ensure_ascii=False)



if __name__ == "__main__":
    main()