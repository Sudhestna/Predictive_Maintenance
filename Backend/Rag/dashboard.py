from statistics import mean
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go


def generate_dashboard(result):

    scores = result.scores

    faithfulness = mean([s["faithfulness"] for s in scores]) * 100
    answer = mean([float(s["answer_relevancy"]) for s in scores]) * 100
    precision = mean([s["context_precision"] for s in scores]) * 100
    recall = mean([s["context_recall"] for s in scores]) * 100

    overall = round(
        (faithfulness + answer + precision + recall) / 4,
        2,
    )

    radar = go.Figure()

    radar.add_trace(
        go.Scatterpolar(
            r=[
                faithfulness,
                answer,
                precision,
                recall,
            ],
            theta=[
                "Faithfulness",
                "Answer\nRelevancy",
                "Context\nPrecision",
                "Context\nRecall",
            ],
            fill="toself",
        )
    )

    radar.update_layout(
        showlegend=False,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
            )
        ),
        height=450,
    )

    radar_html = radar.to_html(
        full_html=False,
        include_plotlyjs="cdn",
    )

    bar = go.Figure()

    bar.add_trace(
        go.Bar(
            x=[
                "Faithfulness",
                "Answer Relevancy",
                "Context Precision",
                "Context Recall",
            ],
            y=[
                faithfulness,
                answer,
                precision,
                recall,
            ],
            text=[
                f"{faithfulness:.1f}%",
                f"{answer:.1f}%",
                f"{precision:.1f}%",
                f"{recall:.1f}%",
            ],
            textposition="outside",
        )
    )

    bar.update_layout(
        yaxis=dict(range=[0, 110]),
        height=450,
    )

    bar_html = bar.to_html(
        full_html=False,
        include_plotlyjs=False,
    )

    rows = []

    dataset = result.dataset

    for i, score in enumerate(scores):

        row = {
            "Question": dataset[i].user_input,
            "Answer": dataset[i].response,
            "Ground Truth": dataset[i].reference,
            "Faithfulness": round(score["faithfulness"], 3),
            "Answer Relevancy": round(
                float(score["answer_relevancy"]),
                3,
            ),
            "Context Precision": round(
                score["context_precision"],
                3,
            ),
            "Context Recall": round(
                score["context_recall"],
                3,
            ),
        }

        rows.append(row)

    df = pd.DataFrame(rows)

    table_html = df.to_html(
        index=False,
        escape=False,
        classes="table",
    )

    # -----------------------------
    # HTML
    # -----------------------------

    html = f"""

<html>

<head>

<title>RAG Evaluation Report</title>

<style>

body{{
font-family:Arial;
background:#f4f7fc;
margin:30px;
}}

h1,h2{{
text-align:center;
}}

.cards{{
display:grid;
grid-template-columns:repeat(4,1fr);
gap:20px;
}}

.card{{
background:white;
padding:20px;
border-radius:12px;
box-shadow:0 4px 12px rgba(0,0,0,.15);
text-align:center;
}}

.metric{{
font-size:34px;
font-weight:bold;
color:#1565C0;
}}

.overall{{
background:white;
padding:20px;
margin-top:25px;
border-radius:12px;
box-shadow:0 4px 12px rgba(0,0,0,.15);
text-align:center;
}}

.grid{{
display:grid;
grid-template-columns:1fr 1fr;
gap:30px;
margin-top:30px;
}}

.summary{{
background:white;
padding:25px;
margin-top:30px;
border-radius:12px;
box-shadow:0 4px 12px rgba(0,0,0,.15);
}}

table{{
width:100%;
border-collapse:collapse;
margin-top:25px;
}}

th{{
background:#1565C0;
color:white;
padding:10px;
}}

td{{
padding:10px;
border:1px solid #ddd;
}}

tr:nth-child(even){{
background:#f2f2f2;
}}

.footer{{
margin-top:40px;
text-align:center;
color:gray;
}}

</style>

</head>

<body>

<h1>RAGAS Evaluation Dashboard</h1>

<p align="center">

Generated on

<b>{datetime.now().strftime("%d %B %Y %H:%M:%S")}</b>

</p>

<div class="cards">

<div class="card">

<h3>Faithfulness</h3>

<div class="metric">

{faithfulness:.1f}%

</div>

</div>

<div class="card">

<h3>Answer Relevancy</h3>

<div class="metric">

{answer:.1f}%

</div>

</div>

<div class="card">

<h3>Context Precision</h3>

<div class="metric">

{precision:.1f}%

</div>

</div>

<div class="card">

<h3>Context Recall</h3>

<div class="metric">

{recall:.1f}%

</div>

</div>

</div>

<div class="overall">

<h2>

Overall Score

</h2>

<h1>

{overall:.1f}%

</h1>

</div>

<div class="grid">

<div>

{radar_html}

</div>

<div>

{bar_html}

</div>

</div>

<h2>

Per Question Evaluation

</h2>

{table_html}

<div class="summary">

<h2>

</div>

<div class="footer">

Generated using RAGAS + Plotly + Python

</div>

</body>

</html>

"""

    with open(
        "ragas_dashboard.html",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(html)

    print("\nDashboard generated successfully.")
    print("Open: ragas_dashboard.html")