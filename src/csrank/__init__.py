#!/usr/bin/env python

import sys
import requests
from bs4 import BeautifulSoup,SoupStrainer
import csv
import urllib
import json
from scholarly import scholarly
import time

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
                "keywords": None,
                "dblp": None
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

        # Try to be nice
        time.sleep(0.1)

        for cand in authors:
            print(cand)
            if searching and not ("university of manchester" in cand["affiliation"].lower() or
                "manchester.ac.uk" in cand["email_domain"]).lower():
                continue
            p["scholar_id"] = cand["scholar_id"]
            p["scholar"] = cand
            break

    # Find ORCIDs  and keywords in research profile
    for p in staff:
        if "orcid" in p and p["orcid"]:
            pass
            #continue
        p["orcid"] = None
        p["keywords"] = []
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
            for keywords in soup.find_all("div", class_="keyword-group"):
                for k in keywords.find("ul").find_all("li"):
                    p["keywords"].append(k.text.strip())

    # Check dblp name
    for p in staff:
        if "dblp" in p and p["dblp"]:
            continue
        p["dblp"] = None
        with requests.get("https://dblp.org/search/author/api",
                    params=[("format","json"),
                            ("q", p["name"])]) as r:
            if r.status_code == 429:
                retry = 10
                retry_s = r.headers.get("Retry-After")
                if retry_s:
                    retry = max(min(int(retry_s)+1, 600), 1)
                print("429 rate limited, waiting", retry, "seconds")
                time.sleep(retry)
                # Retry once
                r = requests.get(r.url)
            else:
                # try to be kind
                time.sleep(0.2)

            if r.status_code != 200:
                print("Warning, dblp status:", r.status_code)
                continue
            dblp = r.json()
            if not dblp or dblp["result"]["status"]["@code"] != "200":
                print("Warning, dblp error:", dblp)
                continue
            print(".", end="")
            #print(r.url"notes" in 
            hits = dblp["result"]["hits"]
            if not hits or not "hit" in hits:
                continue
            for h in hits["hit"]:
                if not "notes" in h["info"]:
                    continue
                notes = h["info"]["notes"]
                if type(notes) == dict: # just one note..
                    notes = [notes]
                for note in notes:
                    note = note["note"]
                    if ("@type" in note and note["@type"] == "affiliation" and
                        "university of manchester" in note["text"].lower()):
                        # Pick up dblp PID
                        p["dblp"] = h["info"]["url"]
                    
        
    # Write out CSV and JSON
    with open("staff-cs.csv", "w", encoding="utf-8") as f:
        w = csv.writer(f, dialect="excel")
        w.writerow(("name", "role", "url", "scholar_id", "orcid", "dblp"))
        for p in staff:
            w.writerow((p["name"], p["role"], p["url"], p["scholar_id"], p["orcid"], p["dblp"]))    

    with open("staff-cs.json", "w", encoding="utf-8") as f:
        json.dump(staff, f, sort_keys=True, indent=4, ensure_ascii=False)



if __name__ == "__main__":
    main()