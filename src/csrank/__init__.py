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
    name_to_staff = {}
    for p in staff:
        if p["url"]:
            if p["url"] in url_to_staff:
                print("Duplicate: ", p)
                sys.exit(1)
            url_to_staff[p["url"]] = p
        if p["name"]:
            if p["name"] in name_to_staff:
                print("Duplicate: ", p)
                sys.exit(1)
            name_to_staff[p["name"]] = p

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
                "scholar_id": None,
                "scholar": None,
                "orcid": None,
            }
            url = person and person.find("a")
            if url:
                p["url"] = url["href"].strip()
            area_url = area and area.find("a")
            if area_url:
                p["area_url"] = area_url["href"].strip()
            
            if p["url"] in url_to_staff or p["name"] in name_to_staff:
                # Avoid duplicates!
                # TODO: But how to update?
                continue
            staff.append(p)

    for p in staff:
        entry = url_to_staff.get(p["url"]) or name_to_staff.get(p["name"])
        searching = True
        authors = []
        if entry:
            if "scholar" in entry and entry["scholar"]:
                continue # TODO: Add flag to update
            if "scholar_id" in entry and entry["scholar_id"]:
                authors = [scholarly.search_author_id(entry["scholar_id"])]
                searching = False          

        if searching or not authors:
            authors = scholarly.search_author(p["name"] + ", Manchester")

        for cand in authors:
            print(cand)
            if searching and not ("University of Manchester" in cand["affiliation"] or
                "manchester.ac.uk" in cand["email_domain"]):
                continue
            p["scholar_id"] = cand["scholar_id"]
            p["scholar"] = cand
            break

    # Find ORCIDs in research profile
    
    for p in staff:
        if "orcid" in p and p["orcid"]:
            continue
        p["orcid"] = None
        if not p["url"] or not "research.manchester.ac.uk" in p["url"]:
            continue # not the research portal
        with requests.get(p["url"]) as r:
            soup = BeautifulSoup(r.content, features="lxml")
            orcid = soup.find("a", class_="orcid")
            if orcid:
                url = orcid["href"]
                if not "https://orcid.org/" in url:
                    continue
                p["orcid"] = url


    # Write out CSV and JSON

    with open("staff-cs.csv", "w", encoding="utf-8") as f:
        w = csv.writer(f, dialect="excel")
        w.writerow(("name", "role", "url", "scholar_id", "orcid"))
        for p in staff:
            w.writerow((p["name"], p["role"], p["url"], p["scholar_id"], p["orcid"]))    

    with open("staff-cs.json", "w", encoding="utf-8") as f:
        json.dump(staff, f, sort_keys=True, indent=4, ensure_ascii=False)



if __name__ == "__main__":
    main()