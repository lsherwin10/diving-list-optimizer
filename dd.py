import requests
import pandas as pd


class DDTables:
    def __init__(self, front, back, rev, inw, twist):
        self.front = front
        self.back = back
        self.rev = rev
        self.inw = inw
        self.twist = twist

        self.tables = {
            "1": self.front,
            "2": self.back,
            "3": self.rev,
            "4": self.inw,
            "5": self.twist,
        }

    def get_dd(self, dive, position, height):
        return self.tables[dive[0]].get_dd(dive, position, height)


class DDTable:
    def __init__(self, name, one, three):
        self.name = name
        self.one = one
        self.three = three

    def get_name(self):
        return self.name

    def get_1m(self):
        return self.one

    def get_3m(self):
        return self.three

    def get_dd(self, dive, position, height):
        if height == "1M":
            return float(self.one.loc[self.one["Dive"] == dive, position].values[0])
        elif height == "3M":
            return float(self.three.loc[self.three["Dive"] == dive, position].values[0])


def fix_table_headers(df):
    df.drop([0, 1], inplace=True)
    df.reset_index(drop=True, inplace=True)
    headers = df.iloc[0].values

    headers[0] = "Dive"
    headers[1] = "Description"

    df.columns = headers
    df.drop("Description", axis=1, inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def import_dd_tables():
    url = "http://www.usadiver.com/dd_table.htm"

    req = requests.get(url)
    df = pd.read_html(req.content, flavor="html5lib")

    for x in df:
        x.columns = x.iloc[0]

    trim = [x for x in df if "SPRINGBOARD" in x.columns][1:]

    return [fix_table_headers(x) for x in trim]


def create_dd_tables():
    tables = import_dd_tables()
    objs = []

    for table, name in zip(tables, ["Forward", "Back", "Reverse", "Inward", "Twist"]):
        table.drop([0], inplace=True)
        one = table.iloc[:, 0:5]
        three = pd.concat((table.iloc[:, 0], table.iloc[:, 5:]), axis=1)

        objs.append(DDTable(name, one, three))

    return DDTables(*objs)


if __name__ == "__main__":
    dds = create_dd_tables()
    print(dds.get_dd("405", "C", "1M"))
