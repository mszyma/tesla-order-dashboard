# Analysis scripts

Standalone command-line tools that read `tesla_orders.json` (created by `tesla_order_status.py`, see `README.md`). To try them without your own data, copy `examples/tesla_orders.example.json` to `tesla_orders.json` (made-up data).

| Script | What it does | Writes |
| --- | --- | --- |
| `python3 tesla_order_analyzer.py` | Order timeline, financial breakdown, decoded vehicle configuration, task status, delivery info | `tesla_order_analysis.json`, `tesla_order_analysis_report.txt` |
| `python3 tesla_insights_generator.py` | Facts and insights: processing speed, daily/monthly cost, task progress | `tesla_order_insights.txt` |
| `python3 tesla_dashboard.py` | Text dashboard with progress bars | `tesla_order_dashboard.txt` |

The output files contain your personal order data. They are listed in `.gitignore`: do not commit or share them.

The web app (`app.py`) uses the same three modules.
