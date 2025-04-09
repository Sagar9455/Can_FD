def generate_report(test_cases, filename="report.html"):
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>UDS Diagnostic Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            h1 {{ text-align: center; }}
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
            .pass {{ color: green; font-weight: bold; }}
            .fail {{ color: red; font-weight: bold; }}
            .panel {{
                display: none;
                overflow: hidden;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                background: white;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 8px;
                text-align: center;
            }}
            th {{ background-color: #eee; }}
            .step-pass {{ background-color: #c8e6c9; }}
            .step-fail {{ background-color: #ffcdd2; }}
        </style>
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
            }});
        </script>
    </head>
    <body>
        <h1>UDS Diagnostic Report</h1>
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

    with open(filename, "w") as f:
        f.write(html_template.format(body=body))

    print(f"Report generated: {filename}")
