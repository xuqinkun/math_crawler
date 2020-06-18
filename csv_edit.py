import csv


def get_url_from_file(file_name=''):
    data = {}
    with open(file_name, "r") as f:
        row = csv.reader(f, delimiter="\n", quotechar=',')
        for line in row:
            url, status = line[0].split(",")
            data[url] = status
    return data


def write_data_to_file(data={}, file_name=''):
    with open(file_name, "w", newline='') as f:
        spam_writer = csv.writer(f, delimiter=",")
        for item in data.items():
            spam_writer.writerow(item)

