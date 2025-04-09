<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UDS Diagnostic Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }

        h1 {
            text-align: center;
        }

        .summary-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 20px 0 30px;
        }

        .summary-container > div {
            width: 50%;
        }

        .report-info p {
            font-size: 14px;
            color: #333;
            margin: 4px 0;
            font-weight: bold;
        }

        .report-info p:first-child {
            font-size: 19.6px; /* 14px + 40% */
        }

        .pass { color: green; font-weight: bold; }
        .fail { color: red; font-weight: bold; }

        .chart-wrapper {
            width: 175px;  /* 70% of original 250px */
            height: 175px;
            position: relative;
            margin: 0 auto;
        }

        canvas {
            width: 100% !important;
            height: 100% !important;
        }

        @media (max-width: 600px) {
            .summary-container {
                flex-direction: column;
                align-items: center;
            }

            .summary-container > div {
                width: 100% !important;
                text-align: center;
            }

            .chart-wrapper {
                width: 140px;
                height: 140px;
            }
        }

        button.accordion {
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
        }

        .panel {
            display: none;
            overflow: hidden;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: white;
            table-layout: fixed;
        }

        th, td {
            border: 1px solid #ccc;
            padding: 8px;
            vertical-align: top;
            overflow-wrap: break-word;
            word-wrap: break-word;
            white-space: normal;
        }

        th {
            background-color: #eee;
            text-align: center;
        }

        th:nth-child(1), td:nth-child(1) {
            width: 40px;
            text-align: center;
        }

        th:nth-child(2), td:nth-child(2) {
            width: 180px;
        }

        th:nth-child(3), td:nth-child(3),
        th:nth-child(4), td:nth-child(4),
        th:nth-child(5), td:nth-child(5) {
            width: 120px;
            text-align: center;
        }

        th:nth-child(6), td:nth-child(6) {
            width: auto;
        }

        .step-pass {
            background-color: #c8e6c9;
        }

        .step-fail {
            background-color: #ffcdd2;
        }
    </style>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        document.addEventListener("DOMContentLoaded", () => {
            // Example test case data (this would typically come from a server or API)
            const testCases = [
                { id: "TC_001", status: "pass", steps: [
                    { description: "Diagnostic Session", timestamp: "12:01:23", type: "Request Sent", status: "pass", failureReason: "-" },
                    { description: "Diagnostic Session", timestamp: "12:01:23", type: "Response Received", status: "pass", failureReason: "-" }
                ] },
                { id: "TC_002", status: "fail", steps: [
                    { description: "Read DTC", timestamp: "12:01:26", type: "Request Sent", status: "pass", failureReason: "-" },
                    { description: "Read DTC", timestamp: "12:01:26", type: "Response Received", status: "fail", failureReason: "Incorrect NRC: 0x13" }
                ] }
                // Add more test cases as needed
            ];

            let passedCount = 0;
            let failedCount = 0;

            const summaryContainer = document.querySelector('.summary-container');
            const reportInfo = document.querySelector('.report-info');
            const chartCanvas = document.getElementById('summaryChart').getContext('2d');
            const accordionContainer = document.createElement('div');

            testCases.forEach(testCase => {
                const testCaseElement = document.createElement('button');
                testCaseElement.classList.add('accordion');
                testCaseElement.innerHTML = `▶ ${testCase.id} - <span class="${testCase.status}">${testCase.status === 'pass' ? '✅ Pass' : '❌ Fail'}</span>`;
                accordionContainer.appendChild(testCaseElement);

                const panel = document.createElement('div');
                panel.classList.add('panel');
                const table = document.createElement('table');
                table.innerHTML = `
                    <tr><th>Step</th><th>Description</th><th>Timestamp</th><th>Type</th><th>Status</th><th>Failure Reason</th></tr>
                `;
                testCase.steps.forEach((step, index) => {
                    const row = document.createElement('tr');
                    row.classList.add(step.status === 'pass' ? 'step-pass' : 'step-fail');
                    row.innerHTML = `
                        <td>${index + 1}</td>
                        <td>${step.description}</td>
                        <td>${step.timestamp}</td>
                        <td>${step.type}</td>
                        <td class="${step.status}">${step.status === 'pass' ? 'Pass' : 'Fail'}</td>
                        <td>${step.failureReason}</td>
                    `;
                    table.appendChild(row);
                });

                panel.appendChild(table);
                accordionContainer.appendChild(panel);

                testCaseElement.addEventListener("click", function() {
                    this.classList.toggle("active");
                    panel.style.display = panel.style.display === "block" ? "none" : "block";
                });

                // Count passed and failed test cases
                if (testCase.status === 'pass') {
                    passedCount++;
                } else {
                    failedCount++;
                }
            });

            summaryContainer.appendChild(accordionContainer);

            // Update the report summary
            const currentDate = new Date().toLocaleString();
            reportInfo.innerHTML = `
                <p>Report Generated: ${currentDate}</p>
                <p>Test Duration: 11 seconds</p>
                <p>Total Test Cases: ${testCases.length}</p>
                <p class="pass">Passed: ${passedCount}</p>
                <p class="fail">Failed: ${failedCount}</p>
            `;

            // Generate the pie chart
            new Chart(chartCanvas, {
                type: 'pie',
                data: {
                    labels: ['Passed', 'Failed'],
                    datasets: [{
                        data: [passedCount, failedCount],
                        backgroundColor: ['#4CAF50', '#F44336'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        });
    </script>
</head>
<body>
    <h1>UDS Diagnostic Report</h1>

    <div class="summary-container">
        <!-- Report Info -->
        <div class="report-info"></div>

        <!-- Pie Chart -->
        <div class="chart-wrapper">
            <canvas id="summaryChart"></canvas>
        </div>
    </div>
</body>
</html>
