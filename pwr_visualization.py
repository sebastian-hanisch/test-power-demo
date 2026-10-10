"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Scrollen auf dem Handy nicht zoomt."""

import numpy as np
import plotly.graph_objects as go

import pwr_constants as C

_LAYOUT = dict(margin=dict(l=10, r=10, t=40, b=10), height=340, legend=dict(orientation="h", y=-0.22))


def _finish(fig, title, xtitle=None, ytitle=None, **extra):
    fig.update_layout(title=dict(text=title, x=0), xaxis=dict(title=xtitle, fixedrange=True),
                      yaxis=dict(title=ytitle, fixedrange=True), **{**_LAYOUT, **extra})
    return fig


def build_mde(ns, mde, truth, n_now, n_need):
    """Kleinste nachweisbare Wirkung (80 % Teststärke) gegen die Fenster je Arm; waagerecht die wahre Wirkung, in Punkten.
    Die Hilfslinien sind Linienspuren (keine Shapes): auf logarithmischen Achsen rechnet Plotly Shapes anders um."""
    xs = [float(v) for v in ns]
    ys = [100 * v for v in mde]
    ymax = max(ys) * 1.05
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name="nachweisbare Wirkung (80 %)", line=dict(color=C.COLOR_B, width=3)))
    if truth > 0:
        fig.add_trace(go.Scatter(x=[xs[0], xs[-1]], y=[100 * truth] * 2, mode="lines", name="wahre Wirkung",
                                 line=dict(color=C.COLOR_TRUTH, width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=[n_now, n_now], y=[0, ymax], mode="lines", name="Ihre Wahl", line=dict(color=C.COLOR_A, width=2)))
    if n_need is not None and xs[0] <= n_need <= xs[-1]:
        fig.add_trace(go.Scatter(x=[n_need, n_need], y=[0, ymax], mode="lines", name="reicht ab hier",
                                 line=dict(color=C.COLOR_TRUTH, width=1.5, dash="dot")))
    fig.update_xaxes(type="log", range=[np.log10(xs[0]), np.log10(xs[-1])])
    fig.update_yaxes(range=[0, ymax])
    return _finish(fig, "Was ein Test mit n Fenstern je Arm gerade noch findet", "Fenster je Arm (logarithmisch)",
                   "nachweisbare Wirkung (Prozentpunkte)")


def build_exaggeration(points, current):
    """Überschätzung unter den signifikanten Ergebnissen gegen die Teststärke. points: Liste (Teststärke, Faktor, n)."""
    pts = sorted(points)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[100 * p[0] for p in pts], y=[p[1] for p in pts], mode="lines+markers", name="gemessen",
                             line=dict(color=C.COLOR_B, width=3), text=[f"n = {p[2]}" for p in pts],
                             hovertemplate="Teststärke %{x:.0f} %, Faktor %{y:.2f} (%{text})<extra></extra>"))
    fig.add_hline(y=1.0, line=dict(color="gray", dash="dot"), annotation_text="keine Überschätzung",
                  annotation_position="bottom right")
    if current is not None and np.isfinite(current[1]):
        fig.add_trace(go.Scatter(x=[100 * current[0]], y=[current[1]], mode="markers", name="Ihre Wahl",
                                 marker=dict(color=C.COLOR_TRUTH, size=14, symbol="diamond")))
    fig.update_xaxes(range=[0, 100])
    return _finish(fig, "Wenn der Test anschlägt: wie viel zu groß ist die Schätzung?", "Teststärke in %",
                   "Schätzung / wahre Wirkung (nur signifikante Ergebnisse)")


RULE_LABELS = {"plugin": "Pilot-<br>Wirkung", "signif": "nur nach<br>sign. Pilot", "konserv": "vorsichtig", "relevanz": "lohnende<br>Wirkung"}


def build_plan_boxes(plans, n_need):
    """Geplanter Umfang je Planungsregel (Kästen über die Piloten), logarithmisch; gestrichelt: was reicht."""
    fig = go.Figure()
    colors = {"plugin": C.COLOR_A, "signif": C.COLOR_MISS, "konserv": C.COLOR_B, "relevanz": "#7570b3"}
    labels = list(RULE_LABELS.values())
    for rule, label in RULE_LABELS.items():
        n = plans[rule]
        n = n[~np.isnan(n)]
        if len(n):
            fig.add_trace(go.Box(y=n, x=[label] * len(n), name=label, marker_color=colors[rule], boxpoints=False))
    if n_need is not None:
        fig.add_trace(go.Scatter(x=labels, y=[n_need] * len(labels), mode="lines", name="reicht für 80 %",
                                 line=dict(color=C.COLOR_TRUTH, width=2, dash="dash")))
    fig.update_yaxes(type="log", range=[0.2, 3.1])
    fig.update_xaxes(tickangle=0)
    fig.update_layout(showlegend=n_need is not None)
    return _finish(fig, "Geplanter Umfang je Regel", None, "Fenster je Arm (logarithmisch)")


def build_plan_power(outcomes):
    """Mittlere erreichte Teststärke und Anteil der Studien unter 70 % je Planungsregel."""
    rules = [r for r in RULE_LABELS if not np.isnan(outcomes[r]["power_mean"])]
    labels = [RULE_LABELS[r] for r in rules]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=[100 * outcomes[r]["power_mean"] for r in rules], name="mittlere Teststärke",
                         marker_color=C.COLOR_B))
    fig.add_trace(go.Bar(x=labels, y=[100 * outcomes[r]["share_below_70"] for r in rules], name="Studien unter 70 %",
                         marker_color=C.COLOR_MISS))
    fig.add_hline(y=80, line=dict(color="gray", dash="dot"), annotation_text="Ziel 80 %", annotation_position="top right")
    fig.update_layout(barmode="group")
    fig.update_yaxes(range=[0, 105])
    fig.update_xaxes(tickangle=0)
    return _finish(fig, "Erreichte Teststärke", None, "in %")
