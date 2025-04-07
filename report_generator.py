import csv
from datetime import datetime
# report_generator.py
import csv
from datetime import datetime

class ReportGenerator:
    def __init__(self, filename):
        self.filename = filename
        self.rows = []

    def add_result(self, request, response, passed):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.rows.append([timestamp, request, response, 'PASS' if passed else 'FAIL'])

    def save_report(self):
        with open(self.filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Request', 'Response', 'Result'])
            writer.writerows(self.rows)

def generate_report(data):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>UDS Diagnostic Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { text-align: center; }
            h1 { text-align: center; margin-bottom: 20px; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; background: white; }
            th, td { border: 1px solid black; padding: 10px; text-align: center; }
            th { background-color: #b0b0b0; color: black; font-weight: bold; }
            .pass { background-color: #c8e6c9; color: green; }
            .fail { background-color: #ffcdd2; color: red; }
            .section-title { background-color: #f0f0f0; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>UDS Diagnostic Report</h1>
            <table>
                <tr>
                    <th>S.No</th>
                    <th>Description</th>
                    <th>Timestamp</th>
                    <th>Step</th>
                    <th>Status</th>
                    <th>Failure Reason</th>
                </tr>
    """
    
    for idx, entry in enumerate(data, start=1):
        html_content += f"""
            <tr class="section-title">
                <td rowspan="2">{idx}</td>
                <td rowspan="2">{entry["action"]}</td>
                <td>{entry["timestamp"]}</td>
                <td>Request Sent</td>
                <td class="{'pass' if entry['request_status'] == 'Pass' else 'fail'}">{entry['request_status']}</td>
                <td>{entry['failure_reason'] if entry['request_status'] == 'Fail' else '-'}</td>
            </tr>
            <tr>
                <td>{entry["response_timestamp"] if entry['response_status'] == 'Pass' else '---'}</td>
                <td>Response Received</td>
                <td class="{'pass' if entry['response_status'] == 'Pass' else 'fail'}">{entry['response_status']}</td>
                <td>-</td>
            </tr>
        """

    html_content += """
            </table>
        </div>
    </body>
    </html>
    """
    
    with open("RTY.html", "w") as file:
        file.write(html_content)
    print("Report generated: UDS_Report.html")
    