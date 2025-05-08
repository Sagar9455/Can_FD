from datetime import datetime
from collections import defaultdict

class ReportGenerator:
    def __init__(self, filename):
        self.filename = filename
        self.test_cases = defaultdict(list)  

    def add_result(self, tc_id, step, description, timestamp, msg_type, passed, failure_reason="-"):
        self.test_cases[tc_id].append({
            "step": step,
            "desc": description,
            "timestamp": timestamp,
            "type": msg_type,
            "status": "Pass" if passed else "Fail",
            "fail_reason": failure_reason if not passed else "-"
        })

def convert_report(report):
   
    grouped = defaultdict(list)
    for entry in report:
        grouped[entry['id']].append(entry)

    test_cases = []
    for tc_id, steps in grouped.items():
        overall_status = "Pass"
        step_entries = []

        for i, step in enumerate(steps):
            if step["status"].lower() != "pass":
                overall_status = "Fail"

            # Remove a prefix if present in description (e.g. "LABEL - ActualData")
            description = step["description"]
            if " - " in description:
                description = description.split(" - ", 1)[1]

            step_num = i + 1
            # Create two rows for each step: one for Request and one for Response
            step_entries.append({
                "step": step_num,
                "description": description,
                "timestamp": step["timestamp"],
                "type": "Request Sent",
                "status": step["status"].capitalize(),
                "reason": step["failure_reason"],
                "rowspan": 2
            })
            step_entries.append({
                "timestamp": step["response_timestamp"],
                "type": "Response Received",
                "status": step["status"].capitalize(),
                "reason": step["failure_reason"]
            })

        test_cases.append({
            "name": tc_id,
            "status": overall_status,
            "steps": step_entries
        })
    return test_cases

def generate_report(test_cases, filename="UDS_Report.html", log_filename="N/A", generated_time=None,total_duration=None):
    if generated_time is None:
        generated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Prepare the main body of the report
    body = ""
    for test_case in test_cases:
        result_class = "pass" if test_case["status"] == "Pass" else "fail"
        body += f'<button class="accordion">▶ {test_case["name"]} - <span class="{result_class}">{test_case["status"]}</span></button>\n'
        body += '<div class="panel"><table><tr><th>Step</th><th>Description</th><th>Timestamp</th><th>Type</th><th>Status</th><th>Failure Reason</th></tr>\n'
        for step in test_case["steps"]:
            row_class = "step-pass" if step["status"] == "Pass" else "step-fail"
            # Use the provided rowspan if available
            rowspan = f'rowspan="{step["rowspan"]}"' if "rowspan" in step else ""
            body += f'<tr class="{row_class}">'
            if "step" in step:
                body += f'<td {rowspan}>{step["step"]}</td>'
                body += f'<td {rowspan}>{step["description"]}</td>'
            body += f'<td>{step["timestamp"]}</td><td>{step["type"]}</td>'
            body += f'<td class="{step["status"].lower()}">{step["status"]}</td><td>{step["reason"]}</td></tr>\n'
        body += '</table></div>\n'

    total = len(test_cases)
    passed = sum(1 for tc in test_cases if tc["status"] == "Pass")
    failed = total - passed

    html_template = """<!DOCTYPE html>
<html>
<head>
    <title>UDS Diagnostic Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            text-align: center;
        }}
        button.accordion {{
            background-color: #ddd;
            color: black;
            cursor: pointer;
            padding: 10px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 16px;
            border-radius: 5px;
            margin-bottom: 5px;
        }}
        .pass {{
            color: green;
            font-weight: bold;
        }}
        .fail {{
            color: red;
            font-weight: bold;
        }}
        .panel {{
            display: none;
            overflow: hidden;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: white;
            table-layout: fixed;
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 8px;
            text-align: center;
            vertical-align: top;
            overflow-wrap: break-word;
            word-wrap: break-word;
            white-space: normal;
            max-width: 200px;
        }}
        th {{
            background-color: #eee;
        }}
        .step-pass {{
            background-color: #c8e6c9;
        }}
        .step-fail {{
            background-color: #ffcdd2;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        document.addEventListener("DOMContentLoaded", () => {{
            const acc = document.getElementsByClassName("accordion");
            for (let i = 0; i < acc.length; i++) {{
                acc[i].addEventListener("click", function () {{
                    this.classList.toggle("active");
                    const panel = this.nextElementSibling;
                    panel.style.display = (panel.style.display === "block") ? "none" : "block";
                }});
            }}

            const ctx = document.getElementById("summaryChart").getContext("2d");
            new Chart(ctx, {{
                type: 'pie',
                data: {{
                    labels: ['Passed', 'Failed'],
                    datasets: [{{
                        label: 'Test Case Results',
                        data: [{passed}, {failed}],
                        backgroundColor: ['#4CAF50', '#F44336'],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: false,
                    plugins: {{
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}
            }});
        }});
    </script>
</head>
<body>
    <h1>UDS Diagnostic Report</h1>
    <div style="text-align:center; margin-bottom: 20px;">
        <p><strong>Generated:</strong> {generated_time}</p>
        <p><strong>CAN Log File:</strong> {log_filename}</p>
        <p><strong>Total Test Cases:</strong> {total}</p>
        <p style="color:green;"><strong>Passed:</strong> {passed}</p>
        <p style="color:red;"><strong>Failed:</strong> {failed}</p>
        <p><strong>Test Duration:</strong> {total_duration:.3f} seconds
    </div>
    <canvas id="summaryChart" width="300" height="300" style="display: block; margin: 0 auto 30px;"></canvas>
    {body}
</body>
</html>
"""

    with open(filename, "w") as f:
        f.write(html_template.format(
            body=body,
            total=total,
            passed=passed,
            failed=failed,
            generated_time=generated_time,
            log_filename=log_filename,
            total_duration=total_duration
        ))

    print(f"Report generated: {filename}")
