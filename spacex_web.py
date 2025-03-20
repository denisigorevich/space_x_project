import requests
from bs4 import BeautifulSoup
import pandas as pd
import unicodedata

# URL of the Wikipedia page snapshot (June 9, 2021)
static_url = "https://en.wikipedia.org/w/index.php?title=List_of_Falcon_9_and_Falcon_Heavy_launches&oldid=1027686922"

# Perform an HTTP GET request
response = requests.get(static_url)

# Ensure the request was successful
if response.status_code != 200:
    print(f"Failed to retrieve the page, status code: {response.status_code}")
    exit()

# Create a BeautifulSoup object
soup = BeautifulSoup(response.text, 'html.parser')

# Print page title to verify
print("Page Title:", soup.title.text)

# Find all tables in the page
html_tables = soup.find_all("table", class_="wikitable plainrowheaders collapsible")

# Check if tables were found
if len(html_tables) < 3:
    print("Error: Expected launch record table not found!")
    exit()

# Select the third table which contains launch records
first_launch_table = html_tables[2]

# Function to clean and extract column names
def extract_column_from_header(row):
    """Extracts column names from the table header."""
    if row.br:
        row.br.extract()
    if row.a:
        row.a.extract()
    if row.sup:
        row.sup.extract()

    column_name = ' '.join(row.contents).strip()
    return column_name if column_name and not column_name.isdigit() else None

# Extract column names
column_names = [extract_column_from_header(th) for th in first_launch_table.find_all("th")]
column_names = [name for name in column_names if name]  # Remove None values

# Print extracted column names
print("Extracted Columns:", column_names)

# Initialize dictionary to store data
launch_dict = {
    "Flight No.": [],
    "Launch site": [],
    "Payload": [],
    "Payload mass": [],
    "Orbit": [],
    "Customer": [],
    "Launch outcome": [],
    "Version Booster": [],
    "Booster landing": [],
    "Date": [],
    "Time": []
}

# Helper functions to clean data
def date_time(table_cells):
    return [data_time.strip() for data_time in list(table_cells.strings)][0:2]

def booster_version(table_cells):
    out = ''.join([booster_version for i, booster_version in enumerate(table_cells.strings) if i % 2 == 0][0:-1])
    return out

def landing_status(table_cells):
    return list(table_cells.strings)[0] if table_cells else None

def get_mass(table_cells):
    mass = unicodedata.normalize("NFKD", table_cells.text).strip()
    return mass[0:mass.find("kg")+2] if "kg" in mass else None

# Extract table data
extracted_row = 0
for table_number, table in enumerate(html_tables):
    for rows in table.find_all("tr"):
        # Check if the first table heading is a number (launch number)
        if rows.th and rows.th.string:
            flight_number = rows.th.string.strip()
            flag = flight_number.isdigit()
        else:
            flag = False

        # Get table data
        row = rows.find_all('td')

        # If valid data row, extract values
        if flag:
            extracted_row += 1
            launch_dict["Flight No."].append(flight_number)

            # Extract Date and Time
            datatimelist = date_time(row[0])
            launch_dict["Date"].append(datatimelist[0].strip(','))
            launch_dict["Time"].append(datatimelist[1] if len(datatimelist) > 1 else None)

            # Extract Booster Version
            bv = booster_version(row[1])
            bv = bv if bv else (row[1].a.string if row[1].a else None)
            launch_dict["Version Booster"].append(bv)

            # Extract Launch Site
            launch_site = row[2].a.string if row[2].a else row[2].text.strip()
            launch_dict["Launch site"].append(launch_site)

            # Extract Payload
            payload = row[3].a.string if row[3].a else row[3].text.strip()
            launch_dict["Payload"].append(payload)

            # Extract Payload Mass
            payload_mass = get_mass(row[4]) if row[4] else None
            launch_dict["Payload mass"].append(payload_mass)

            # Extract Orbit
            orbit = row[5].a.string if row[5].a else row[5].text.strip()
            launch_dict["Orbit"].append(orbit)

            # Extract Customer
            customer = row[6].a.string if row[6].a else row[6].text.strip() if row[6] else None
            launch_dict["Customer"].append(customer)

            # Extract Launch Outcome
            launch_outcome = list(row[7].strings)[0] if row[7] else None
            launch_dict["Launch outcome"].append(launch_outcome)

            # Extract Booster Landing Status
            booster_landing = landing_status(row[8]) if row[8] else None
            launch_dict["Booster landing"].append(booster_landing)

# Convert dictionary to Pandas DataFrame
df_launches = pd.DataFrame(launch_dict)

# Save DataFrame to CSV
csv_filename = "spacex_web_scraped.csv"
df_launches.to_csv(csv_filename, index=False)

print(f"Data successfully scraped and saved to {csv_filename}")

# Display first few rows of the DataFrame
print(df_launches.head())
