import os
import yaml
import csv
import subprocess
import datetime
# Define the subdirectory to be analyzed
subdirectory = "config"

# Define the output CSV file name
output_file = "config_history_new.csv"

# Define the path to the Git repository
repository_path = "cxserver"

# Define the Git command to get the commit history of the subdirectory
git_command = f"git log --reverse --format=format:%H -- {subdirectory}"

# Get the commit history of the subdirectory
output = subprocess.check_output(git_command, shell=True, cwd=repository_path)
commits = output.decode("utf-8").split("\n")[:-1]

# Define the header of the CSV file
header = ["source language", "target language", "translation engine", "is preferred engine?", "timestamp"]

# Initialize the list of configurations
configurations = []

# Loop through each commit
for commit in commits:
    # Get the timestamp of the commit
    git_command = f"git log -1 --format=%ai {commit}"
    output = subprocess.check_output(git_command, shell=True, cwd=repository_path)
    timestamp = datetime.datetime.strptime(output.decode("utf-8").strip(), '%Y-%m-%d %H:%M:%S %z').isoformat()

    # Checkout the subdirectory at the commit
    git_command = f"git checkout {commit} -- {subdirectory}"
    output = subprocess.check_output(git_command, shell=True, cwd=repository_path)

    # Load the YAML files in the subdirectory
    supported_pairs = []
    for filename in os.listdir(os.path.join(repository_path, subdirectory)):
        if filename.endswith('.yaml') and filename in [ 'mt-defaults.wikimedia.yaml']:
            # Load YAML file
            with open('cxserver/config/mt-defaults.wikimedia.yaml') as file:
                data = yaml.load(file, Loader=yaml.FullLoader)

            # Write CSV file
            with open('mt-defaults.csv', 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["source language", "target language", "translation engine"])
                for key, value in data.items():
                    if len(key.split("-")) == 2:
                        source, target = key.split("-")
                        writer.writerow([source, target, value])

        if filename.endswith('.yaml') and filename not in ['MWPageLoader.yaml', 'languages.yaml', 'JsonDict.yaml',
                                                           'Dictd.yaml', 'mt-defaults.wikimedia.yaml']:
            with open(os.path.join(repository_path, subdirectory, filename), "r") as f:
                config = yaml.safe_load(f)

                # Check if the YAML file has a "handler" key
                if "handler" in config:
                    # Handle transform.js based configuration files
                    handler = config["handler"]
                    if handler == "transform.js":
                        lst = config["languages"]
                        target_langs = []
                        source_lang = []
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
                    # Handle standard configuration files
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
                            "is preferred engine?": preferred_engine,
                            "timestamp": timestamp
                        })

    # Add the configurations to the list
    configurations.extend(supported_pairs)

# Read in the expected_mt-defaults.csv file and build a dictionary for O(1) lookups
with open("mt-defaults.csv", "r") as f:
    reader = csv.DictReader(f)
    mt_defaults = {}
    for row in reader:
        key = (row["source language"], row["target language"], row["translation engine"])
        mt_defaults[key] = row

# Loop over each pair in the configurations list
for pair in configurations:
    # Look up the matching pair in the mt_defaults dictionary
    key = (pair["source language"], pair["target language"], pair["translation engine"])
    match = mt_defaults.get(key)
    # If a match is found, update the "is preferred engine?" flag to True
    if match:
        pair["is preferred engine?"] = "True"


# Export the list of configurations to a CSV file
with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    writer.writerows(configurations)
