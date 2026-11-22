"""Plotly-Abbildungen: gestapelte Kosten, Budgetkurve des Gegners mit Break-even, Kosten-Nutzen-Kurve, Zeit. Alle Achsen fest (fixedrange), keine Beschriftungen auf Log-Achsen."""

import math

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import mek_breakeven as BE
import mek_constants as C
import mek_frozen as F

TICKS = [1, 2, 4, 8, 16, 32]


def _fest(fig, hoehe=380):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(height=hoehe, margin=dict(l=50, r=20, t=40, b=45), legend=dict(orientation="h", y=-0.28))
    return fig


def build_kosten(rows: list[dict], n_inst: int, einheit: str):
    """Gestapelte Balken je Verfahren: Entwicklung E und N × Einsatz b, in der Einheit eines Fahrzeugs (nie über Fahrzeuge)."""
    namen = [r["Verfahren"] for r in rows]
    e = [r["E"] for r in rows]
    einsatz = [n_inst * r["b"] for r in rows]
    fig = go.Figure()
    fig.add_bar(x=namen, y=e, name="Entwicklung E", marker_color=C.COLOR_WARN)
    fig.add_bar(x=namen, y=einsatz, name=f"{n_inst} Einsätze", marker_color=C.COLOR_M)
    fig.update_layout(barmode="stack", yaxis_title=einheit, xaxis_title="")
    return _fest(fig, 360)


def build_budgetkurve(akz: str, zellen: list[str], stufe: str, art: str, k: int, n_inst: float, lebensdauer=None):
    """Abstand zur Referenz gegen das Budget je Instanz (Vielfache von ℓ, logarithmisch): Kurve der Zufallsauswahl, waagerecht die trainierte Meta-Ebene
    (Mittel der Wiederholungen, Spanne grau), Punkt „Gegner bei B′ = B + E/N“; der Schnittpunkt ist N*."""
    d = F.h5()
    mults = C.H5_MULTS
    n_eff = n_inst if lebensdauer in (None, "nie") else min(n_inst, float(lebensdauer))
    spalten = 3 if len(zellen) > 1 else 1
    zeilen = math.ceil(len(zellen) / spalten)
    fig = make_subplots(rows=zeilen, cols=spalten, subplot_titles=zellen, vertical_spacing=0.14 if zeilen > 1 else 0.1)
    b_m = 1 if stufe == "lo" else 4
    e_m = F.KO.entwicklung_in_stufen(art, k)
    for i, zn in enumerate(zellen):
        r, c = i // spalten + 1, i % spalten + 1
        kurve = d["kurve"][akz][zn]
        qs = [F.trainiert_gap(akz, zn, art, k, stufe, w) for w in range(d["meta"]["wiederholungen"])]
        q = sum(qs) / len(qs)
        fig.add_trace(go.Scatter(x=list(mults), y=kurve, mode="lines+markers", name="Zufallsauswahl (Gegner)", line=dict(color=C.COLOR_F), showlegend=(i == 0)), row=r, col=c)
        fig.add_trace(go.Scatter(x=[mults[0], mults[-1]], y=[q, q], mode="lines", name="trainiert, bei Einsatz B", line=dict(color=C.COLOR_M, width=3), showlegend=(i == 0)), row=r, col=c)
        fig.add_trace(go.Scatter(x=[mults[0], mults[-1], mults[-1], mults[0]], y=[min(qs), min(qs), max(qs), max(qs)], mode="lines", fill="toself", fillcolor=C.COLOR_BAND, line=dict(width=0),
                                 name="Spanne der Wiederholungen", hoverinfo="skip", showlegend=(i == 0)), row=r, col=c)
        beta = BE.gegner_budget(b_m, e_m, n_eff)
        beta = min(max(beta, mults[0]), mults[-1])
        fig.add_trace(go.Scatter(x=[beta], y=[BE.abstand_bei(mults, kurve, beta)], mode="markers", name=f"Gegner bei B′ (N = {n_eff:g})", marker=dict(color=C.COLOR_WARN, size=11, symbol="diamond"),
                                 showlegend=(i == 0)), row=r, col=c)
        fig.update_xaxes(type="log", range=[0, math.log10(32)], tickvals=TICKS, ticktext=[str(t) for t in TICKS], row=r, col=c)
    fig.update_xaxes(title_text="Budget je Instanz in Vielfachen von ℓ = 50·n", row=zeilen, col=1)
    fig.update_yaxes(title_text="Abstand zur Referenz (%)", row=1, col=1)
    return _fest(fig, 330 * zeilen + 60)


def build_kosten_nutzen_ep(zelle: str, g: int):
    """Einplanung, eine Zelle: Median des Regrets (%) der Suchverfahren gegen ihre Auswertungen, als Punkt der feste Gegner ATC(k) bei seinen g Auswertungen."""
    fig = go.Figure()
    for variante, name, farbe in (("gp", "GP", C.COLOR_M), ("ones", "(1+1)-Suche", C.COLOR_F), ("zufall", "Zufallssuche", C.COLOR_GRAU), ("gp_impf", "GP mit Startbaum", C.COLOR_WARN)):
        kv = F.ep_kurve(zelle, variante)
        if kv:
            fig.add_trace(go.Scatter(x=list(kv), y=[100 * v for v in kv.values()], mode="lines+markers", name=name, line=dict(color=farbe)))
    for gg in C.EP_RASTER:
        fig.add_trace(go.Scatter(x=[gg], y=[100 * F.ep_median_reue(zelle, "atc", g=gg)], mode="markers", name=f"ATC(k), {gg} Werte", marker=dict(size=13 if gg == g else 8, symbol="diamond",
                                                                                                                                    color=C.COLOR_WARN if gg == g else C.COLOR_GRAU)))
    fig.update_xaxes(type="log", title_text="Auswertungen (Regel auf 20 Trainingsinstanzen)")
    fig.update_yaxes(title_text="Median des Regrets auf frischen Instanzen (%)")
    return _fest(fig)


def build_kosten_nutzen_bp(fam: str, gitter: int):
    """Bin Packing, eine Familie: Median des Überschusses gegen Best Fit (Pp) auf Test und Training gegen die Auswertungen der Suche; PR2-Punkte bei g × g Auswertungen."""
    fig = go.Figure()
    for methode, farbe in (("EA-S", C.COLOR_M), ("GP-T", C.COLOR_F)):
        xs = list(C.BP_BUDGETS)
        fig.add_trace(go.Scatter(x=xs, y=[F.bp_suche_median(fam, methode, b, "test") for b in xs], mode="lines+markers", name=f"{methode}, Test", line=dict(color=farbe)))
        fig.add_trace(go.Scatter(x=xs, y=[F.bp_suche_median(fam, methode, b, "train") for b in xs], mode="lines+markers", name=f"{methode}, Training", line=dict(color=farbe, dash="dot")))
    for gi in C.BP_PR2_GRID:
        fig.add_trace(go.Scatter(x=[gi * gi], y=[F.bp_pr2_median(fam, gi, "test")], mode="markers", name=f"PR2 {gi} × {gi}, Test", marker=dict(size=13 if gi * gi == gitter else 8, symbol="diamond",
                                                                                                                               color=C.COLOR_WARN if gi * gi == gitter else C.COLOR_GRAU)))
    fig.update_xaxes(type="log", title_text="Auswertungen (Regel auf 20 Trainingsinstanzen)")
    fig.update_yaxes(title_text="Median Δ gegen Best Fit (Prozentpunkte Überschuss, positiv = schlechter)")
    return _fest(fig)


def build_zeit(rows: list[dict]):
    """Sekunden je 1 000 Auswertungen je Regel (ein Lauf dieses Rechners, kein Befund)."""
    fig = go.Figure(go.Bar(x=[r["Regel"] for r in rows], y=[r["je1000"] for r in rows], marker_color=C.COLOR_F))
    fig.update_yaxes(title_text="Sekunden je 1 000 Auswertungen")
    return _fest(fig, 320)
