import os

def count(path):

    with open(path, "r") as file:
        file = file.readlines()

        file = [line.rstrip() for line in file]

        counts_dict = {}

        for line in file:
            if os.path.isfile(line):
                ...
            elif not line.endswith(".js") and line:
                error_type = line.split()[-1]
                if error_type == "space":
                    print(line)
                if not counts_dict.get(error_type):
                    counts_dict[error_type] = 1
                else:
                    counts_dict[error_type] += 1
        print(counts_dict)

count("~/fixer/lint.txt")