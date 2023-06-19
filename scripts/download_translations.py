import json
import os
import sys
import time

import tolgee_requests

root_dir = os.path.join(os.path.dirname(__file__), "..")
os.chdir(root_dir) # move to root project

sys.path.append("wingetui")

from lang.lang_tools import *

# Update contributors
os.system("python scripts/get_contributors.py")

countOfChanges = len(os.popen("git status -s").readlines())

isAutoCommit = False
isSomeChanges = False

if len(sys.argv)>1:
    if (sys.argv[1] == "--autocommit"):
        isAutoCommit = True
    else:
        print("nocommit")
        print(sys.argv[1])


import glob
import zipfile

os.chdir(os.path.normpath(os.path.join(root_dir, "wingetui/lang")))

print()
print("-------------------------------------------------------")
print()
print("  Downloading updated translations...")


response = tolgee_requests.export()
if (not response.ok):
    statusCode = response.status_code
    print(f"  Error {statusCode}: {response.text}")
    if (statusCode == 403):
        print("  APIKEY is probably wrong!")
    exit(1)
with open("langs.zip", "wb") as f:
    f.write(response.content)
    langArchiveName = f.name


print("  Download complete!")
print()
print("-------------------------------------------------------")
print()
print("  Extracting language files...")



downloadedLanguages = []
zip_file = zipfile.ZipFile(langArchiveName)

for file in glob.glob('lang_*.json'): # If the downloaded zip file is valid, delete old language files and extract the new ones
    os.remove(file)

for name in zip_file.namelist():
    lang = os.path.splitext(name)[0]
    if (lang in languageRemap):
        lang = languageRemap[lang]
    newFilename = f"lang_{lang}.json"
    downloadedLanguages.append(lang)

    try:
        zip_file.extract(name, "./")
        os.replace(name, newFilename)

        print(f"  Extracted {newFilename}")
    except KeyError as e:
        print(type(name))
        f = input(f"  The file {name} was not expected to be in here. Please write the name for the file. It should follow the following structure: lang_[CODE].json: ")
        zip_file.extract(f, "./")
        os.replace(f, newFilename)
        print(f"  Extracted {f}")
zip_file.close()
downloadedLanguages.sort()
os.remove("langs.zip")


print("  Process complete!")
print()
print("-------------------------------------------------------")
print()
print("  Generating translations file...")


langPerc = {}
langCredits = {}

for lang in downloadedLanguages:
    with open(f"lang_{lang}.json", "r", encoding='utf-8') as f:
        data = json.load(f)
    c = 0
    a = 0
    for key, value in data.items():
        c += 1
        if (value != None):
            a += 1
    credits = []
    try:
        credits = getTranslatorsFromCredits(data["{0} {0} {0} Contributors, please add your names/usernames separated by comas (for credit purposes)"])
    except KeyError as e:
        print(e)
        print("Can't get translator list!")
    langCredits[lang] = credits
    percNum = a / c
    perc = "{:.0%}".format(percNum)
    if (perc == "100%" and percNum < 1):
        perc = "99%"
    if (perc == "100%" or lang == "en"):
        continue
    langPerc[lang] = perc

if (isAutoCommit):
    os.system("git add .")
countOfChanges = len(os.popen("git status -s").readlines()) - countOfChanges
isSomeChanges = True if countOfChanges > 0 else False

outputString = f"""
# Autogenerated file, do not modify it!!!

untranslatedPercentage = {json.dumps(langPerc, indent=2, ensure_ascii=False)}

languageCredits = {json.dumps(langCredits, indent=2, ensure_ascii=False)}
"""

translations_filepath = os.path.normpath(os.path.join(root_dir, "wingetui/data/translations.py"))
with open(translations_filepath, "w", encoding="utf-8") as f:
    f.write(outputString.strip())


print("  Process complete!")
print()
print("-------------------------------------------------------")
print()
print("  Updating README.md...")


# Generate language table
readmeFilename = os.path.join(root_dir, "README.md")

with open(readmeFilename, "r+", encoding="utf-8") as f:
    skip = False
    data = ""
    for line in f.readlines():
        if (line.startswith("<!-- Autogenerated translations -->")):
            data += f'{line}{getMarkdownSupportLangs()}\nLast updated: {str(time.ctime(time.time()))}\n'
            print("  Text modified")
            skip = True
        if (line.startswith("<!-- END Autogenerated translations -->")):
            skip = False
        if (not skip): data += line
    if (isSomeChanges):
        f.seek(0)
        f.write(data)
        f.truncate()


print("  Process complete!")
print()
print("-------------------------------------------------------")
print()

if (isAutoCommit):
    if (not isSomeChanges):
        os.system("git reset --hard") # prevent clean
else:
    os.system("pause")
