import csv
import os
import pandas as pd
from datetime import datetime
import shutil

SOURCE_FILE = r"C:\Users\13915\payroll\Export_Payroll Export_1726628851334.xlsx"
NAME_MAP_FILE = r"C:\Users\13915\payroll\Name mapping_DW.csv"

def type_to_xero_type(type):
    type_lower = type.lower()
    if "evening" in type_lower:
        return "HCP - Support Workers (Evening Hours)"
    if "sun" in type_lower or "sunday" in type_lower:
        return "HCP - Support Workers (Sunday Hours)"
    if "sat" in type_lower or "saturday" in type_lower:
        return "HCP - Support Workers (Saturday Hours)"
    if "public" in type_lower or "holiday" in type_lower:
        return "HCP - Support Workers (Public Holiday Hours)"
    if "sleepover" in type_lower:
        return "HCP - Support Workers (Sleepover)"
    return "HCP - Support Workers (Ordinary Hours)"

class PAYROLL:
    def __init__(self, turnpoint_path, name_map_path):
        print(f"turnpoint file: {turnpoint_path}")
        print(f"name map file: {name_map_path}")
        self.turnpoint_path = turnpoint_path
        self.name_map_path = name_map_path

    def output_dir_create(self):
        dir_path = os.path.dirname(self.turnpoint_path)
        dir_basename = os.path.basename(dir_path)
        output_dir = dir_path + r"\output"
        shutil.rmtree(output_dir, ignore_errors=True)
        os.mkdir(output_dir)
        self.output_dir = output_dir
        self.dir_basename = dir_basename

    def name_map_populate(self):
        duplicated_names = []
        self.name_map = {}
        try:
            with open(self.name_map_path, encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=",")
                for row in reader:
                    if row[0] in self.name_map:
                        duplicated_names.append(row[0])
                    #self.name_map[row[0]] = (row[1], row[2])
                    try:
                        self.name_map[row[0]] = (row[1], row[2])
                    except IndexError as e:
                        print(f"Error at row {row}: {e}")
        except UnicodeDecodeError as e:
            print(f"UnicodeDecodeError: {e}")    

        if len(duplicated_names) > 0:
            print(f"=================================================================")
            print(f"Error: Name map includes {len(duplicated_names)} duplicated names in name map file")
            for duplicated_name in duplicated_names:
                print(f"{duplicated_name}")
            print(f"=================================================================")
            print(f"Cannot generate Timesheet")
            return False
        return True
    def name_map_validate(self):
        invalid_names = []
        for index, row in self.df.iterrows():
            name = row['Care Worker']
            if name not in self.name_map:
                invalid_names.append(name)
        invalid_names_set = sorted(set(invalid_names))
        if len(invalid_names_set) > 0:
            print(f"=================================================================")
            print(f"Error: Name map doesn't include {len(invalid_names_set)} care workers in turnpoint excel file")
            for invalid_name in invalid_names_set:
                print(f"{invalid_name}")
            print(f"=================================================================")
            print(f"Cannot generate Timesheet")
            return False
        return True

    def data_read(self):
        self.df = pd.read_excel(self.turnpoint_path)

    def data_cleanup(self):
        df = self.df
        df = df.dropna(subset=['Care Worker'])
        df = df[df['Client'] != 'PERIOD TOTALS']
        df = df[~df['Client'].str.startswith('Warning')]
        df = df[~df['Client'].str.startswith('SHIFT BREAK')]
        df['Duration'] = df['Duration'].astype(str)
        df['Duration'] = df['Duration'].str.replace('Long', '')
        df['Duration'] = df['Duration'].astype(float) 
        df['Travel W/Client'] = df['Travel W/Client'].apply(lambda x: 0 if pd.isna(x) else float(x.split()[0]) if 'km' in x else x)
        df['Date Range'] = pd.to_datetime(df['Date Range'], format='%d/%b/%Y').dt.strftime('%d/%m/%Y')
        self.df = df

    def data_xero_type_add(self):
        df = self.df
        df['xero_type'] = df['Dep Code'].apply(type_to_xero_type)
        self.df = df

    def data_xero_name_add(self):
        df = self.df
        df['First Name'] = df['Care Worker'].apply(lambda x: self.name_map[x][0])
        df['Last Name'] = df['Care Worker'].apply(lambda x: self.name_map[x][1])
        self.df = df

    def data_car_allowance_add(self):
        df = self.df
        #df['Car Allowance'] = df['Travel W/Client'].apply(lambda x: 0 if pd.isna(x) else float(x.split()[0]) if 'km' in x else x)
        df['Car Allowance'] = df['Travel W/Client']
    def data_timesheet_gen(self):
        df = self.df

        # ignore if First Name and Last Name is empty
        df = df[(df['First Name'] != '') & (df['Last Name'] != '')]

        df = df.rename(columns={'Date Range': 'Date', 'xero_type': 'Type', 'Duration': 'hours', 'Travel W/Client': 'Mileage'})

        # timesheet with hour type
        hour = df.groupby(["Care Worker", "First Name", "Last Name", "Date", "Type"])["hours"].sum()
        hour_df = pd.DataFrame(hour)
        hour_df = hour_df.reset_index()
        hour_df = hour_df.sort_values(by=['First Name', 'Last Name', "Date"], ascending=True)
        self.hour_df = hour_df

        # timesheet with mileage
        km = df.groupby(["Care Worker", "First Name", "Last Name", "Date", "Type"])["Mileage"].sum()
        km_df = pd.DataFrame(km)
        km_df = km_df.reset_index()
        km_df["Type"] = "Mileage"                                   # change Type to Mileage
        km_df = km_df.rename(columns={'Mileage':'hours'}) # change Mileage column to hours for join
        km_df = km_df[km_df['hours'] > 0]       # drop 0
        km_df = km_df.sort_values(by=['First Name', 'Last Name', "Date"], ascending=True)
        self.km_df = km_df

        # outer join: hour and mileage
        hour_km_df = pd.merge(hour_df, km_df, how="outer")
        hour_km_df = hour_km_df.sort_values(by=['First Name', 'Last Name', "Date", 'Type'], ascending=True)
        self.hour_km_df = hour_km_df

        total = hour_km_df.groupby(["Care Worker", "First Name", "Last Name", "Type"])["hours"].sum()
        total_df = pd.DataFrame(total)
        total_df = total_df.reset_index()
        self.total_df = total_df

    def data_to_csv(self):
        csv_path = self.output_dir + f"\\{self.dir_basename}_1_src.csv"
        self.df.to_csv(csv_path, index = None, header=True, encoding="utf-8")

        csv_path = self.output_dir + f"\\{self.dir_basename}_2_timesheet_hour.csv"
        df = self.hour_df.drop(columns=['Care Worker'])
        df.to_csv(csv_path, sep=",", encoding="utf-8", index=False)

        csv_path = self.output_dir + f"\\{self.dir_basename}_3_timesheet_hour_km.csv"
        df = self.hour_km_df.drop(columns=['Care Worker'])
        df.to_csv(csv_path, sep=",", encoding="utf-8", index=False)

        csv_path = self.output_dir + f"\\{self.dir_basename}_4_total.csv"
        df = self.total_df
        df = df.rename(columns={'Care Worker':'name', 'hours':'hours or km'})
        df.to_csv(csv_path, sep=",", encoding="utf-8", index=False)

if __name__ == "__main__":
    payroll = PAYROLL(SOURCE_FILE, NAME_MAP_FILE)
    payroll.output_dir_create()
    if not payroll.name_map_populate():
        exit()
    payroll.data_read()
    payroll.data_cleanup()
    if not payroll.name_map_validate():
        exit()
    payroll.data_xero_type_add()
    payroll.data_xero_name_add()
    payroll.data_car_allowance_add()
    payroll.data_timesheet_gen()
    payroll.data_to_csv()
    print("\nTimesheet is generated successfully")
