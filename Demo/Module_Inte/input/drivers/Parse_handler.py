
import csv
from collections import defaultdict

grouped_cases = defaultdict(list)

def load_testcases():
    file_path="/home/mobase/Inte_Project/supportFiles/test_cases.txt"
    grouped_cases.clear()
    try:
        with open(file_path, "r") as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header

            for row in reader:
                if not row or len(row) < 5:
                    continue  # Skip empty or malformed lines

                tc_id = row[0].strip()
                step_desc = row[1].strip()
                service_id = row[2].strip()
                subfunction_or_did = row[3].strip()
                expected_response = row[4].strip()

                grouped_cases[tc_id].append((
                    tc_id,
                    step_desc,
                    service_id,
                    subfunction_or_did,
                    expected_response
                ))

        return grouped_cases

    except Exception as e:
        print(f"Error parsing testcases: {e}")
        return {}
