import json

student = {
    "ali": 12,
    "aslı": 11,
}

with open("data.json", "w") as d:
    json.dump(student, d, indend=4)