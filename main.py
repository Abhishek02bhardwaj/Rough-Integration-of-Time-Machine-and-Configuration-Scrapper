import os
import yaml
import csv
import subprocess
from datetime import datetime

supported_pairs = []
# Loop through all the YAML files in the config directory
for filename in os.listdir("config"):
    if filename.endswith('.yaml') and filename not in ['MWPageLoader.yaml', 'languages.yaml', 'JsonDict.yaml',
                                                       'Dictd.yaml', 'mt-defaults.wikimedia.yaml']:
        with open(os.path.join("config", filename), "r") as f:
            config = yaml.safe_load(f)

            # Check if the YAML file has a "handler" key
            if "handler" in config:
                handler = config["handler"]
                if handler == "transform.js":
                    lst = config["languages"]
                    target_langs = []
                    source_lang = []
                    # Handle transform.js based configuration files
                    for j in lst:
                        source_lang.append(j)
                        target_lang = []
                        for k in lst:
                            if (j != k and not ((j == "simple" and k == "en") or (k == "simple" and j == "en"))):
                                target_lang.append(k)
                        target_langs.append(target_lang)
                    engine = filename[:-5]
                    preferred_engine = config.get("preferred_engine", False)
            else:
                # # Handle standard configuration files
                # Handle dictionary-based configuration files
                source_lang = list(config.keys())
                target_langs = []
                for j in source_lang:
                    target_langs.append(config[j])
                    engine = filename[:-5]
                    preferred_engine = config.get("preferred_engine", False)

            # Add the supported pairs to the list
            for k in range(len(source_lang)):
                for i in target_langs[k]:
                    source = source_lang[k] if source_lang[k] is not False else "no"
                    target = i if i is not False else "no"
                    supported_pairs.append({
                        "source language": source,
                        "target language": target,
                        "translation engine": engine,
                        "is preferred engine?": preferred_engine
                    })

# Export the list as a CSV file
with open("supported_pairs.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["source language", "target language", "translation engine",
                                           "is preferred engine?"])
    writer.writeheader()
    writer.writerows(supported_pairs)

# Load YAML file
with open('config/mt-defaults.wikimedia.yaml') as file:
    data = yaml.load(file, Loader=yaml.FullLoader)

# Write CSV file
with open('mt-defaults.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["source language", "target language", "translation engine"])
    for key, value in data.items():
        if len(key.split("-")) == 2:
            source, target = key.split("-")
            writer.writerow([source, target, value])

# Read in the expected_supported_pairs.csv file
with open("supported_pairs.csv", "r") as f:
    reader = csv.DictReader(f)
    supported_pairs = [row for row in reader]

# Read in the expected_mt-defaults.csv file and build a dictionary for O(1) lookups
with open("mt-defaults.csv", "r") as f:
    reader = csv.DictReader(f)
    mt_defaults = {}
    for row in reader:
        key = (row["source language"], row["target language"], row["translation engine"])
        mt_defaults[key] = row

# Loop over each pair in the supported_pairs list
for pair in supported_pairs:
    # Look up the matching pair in the mt_defaults dictionary
    key = (pair["source language"], pair["target language"], pair["translation engine"])
    match = mt_defaults.get(key)
    # If a match is found, update the "is preferred engine?" flag to True
    if match:
        pair["is preferred engine?"] = "True"

# Write the updated supported_pairs list back to the CSV file
with open("supported_pairs.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["source language", "target language", "translation engine",
                                           "is preferred engine?"])
    writer.writeheader()
    writer.writerows(supported_pairs)


file_path = 'supported_pairs.csv'


def parse_csv(file_path):
    data = []
    with open(file_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def run_git_command(command):
    return subprocess.check_output(['git'] + command.split()).decode('utf-8')


def get_commits():
    commit_hashes = run_git_command('rev-list --all').splitlines()
    commits = []
    for commit_hash in commit_hashes:
        timestamp = run_git_command(f'show -s --format=%ct {commit_hash}').strip()
        iso8601_timestamp = datetime.utcfromtimestamp(int(timestamp)).isoformat()
        if datetime.fromisoformat(iso8601_timestamp).year >= 2017:
            data = parse_csv('supported_pairs.csv')
            commits.append({'timestamp': iso8601_timestamp, 'data': data})
    return commits


commits = get_commits()


def export_csv(file_path, data):
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['source language', 'target language', 'translation engine', 'is preferred engine?', 'timestamp'])
        for commit in data:
            for row in commit['data']:
                writer.writerow([row['source language'], row['target language'], row['translation engine'], row['is preferred engine?'], commit['timestamp']])


export_csv('data_history_new.csv', commits)
