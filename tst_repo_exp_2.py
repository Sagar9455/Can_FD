def generate_report(test_cases, filename="UDS_Report.html"):
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
        <p><strong>Total Test Cases:</strong> {total}</p>
        <p style="color:green;"><strong>Passed:</strong> {passed}</p>
        <p style="color:red;"><strong>Failed:</strong> {failed}</p>
    </div>
    <canvas id="summaryChart" width="300" height="300" style="display: block; margin: 0 auto 30px;"></canvas>
    {body}
</body>
</html>
"""

    body = ""
    for test_case in test_cases:
        result_class = "pass" if test_case["status"] == "Pass" else "fail"
        body += f'<button class="accordion">▶ {test_case["name"]} - <span class="{result_class}">{test_case["status"]}</span></button>\n'
        body += '<div class="panel"><table><tr><th>Step</th><th>Description</th><th>Timestamp</th><th>Type</th><th>Status</th><th>Failure Reason</th></tr>\n'
        for step in test_case["steps"]:
            row_class = "step-pass" if step["status"] == "Pass" else "step-fail"
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

    with open(filename, "w") as f:
        f.write(html_template.format(body=body, total=total, passed=passed, failed=failed))

    print(f"Report generated: {filename}")
