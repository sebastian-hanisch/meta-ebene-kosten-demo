"""Lohnt die Meta-Ebene? Eine Kostenrechnung in Auswertungen
Sebastian Hanisch - Operations Research und Machine Learning

Zusammenfluss der Reihe „Hyperheuristiken erklärt“: Entwicklungskosten, Break-even und Karte der Messungen aus den Demos der Reihe.
Fast alles ist Arithmetik auf eingefrorenen Tabellen (data/mek_*.json); live sind nur die Probe des Trainings und die Zeitmessung.

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import mek_constants as C
import mek_evaluation as E
import mek_frozen as F
import mek_kosten as KO
import mek_texts as TX
import mek_visualization as V
from mek_layout import dunkles_design, kopf_css
from mek_presets import (
    FAHRZEUGE,
    init_session_state_defaults,
    load_permalink_settings,
    next_seed,
    options,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="Lohnt die Meta-Ebene? – Sebastian Hanisch", layout="wide")

st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title(TX.TITEL)
    st.caption(TX.UNTERTITEL)
st.markdown(TX.EINLEITUNG)

with st.expander("💬 In einfachen Worten", expanded=False):
    st.markdown(TX.IN_EINFACHEN_WORTEN)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

if F.h5() is None or F.gegner() is None or F.karte() is None:
    st.error("Die eingefrorenen Messreihen (data/mek_h5.json, mek_gegner.json, mek_karte.json) fehlen: Die Demo braucht sie.")
    st.stop()

AKZ_NAMEN = C.AKZ_ANZEIGE
ANZEIGE_ZELLE = {"alle sechs": "alle sechs Zellen"}


def _wahl(label, key, help_text, fmt=None, radio=False):
    """Auswahlregler der Seitenleiste mit Werten und Anzeigenamen aus dem Presets-Modul."""
    opts = options(key)
    if radio:
        return st.radio(label, opts, key=key, help=help_text, format_func=fmt or str, horizontal=True)
    return st.selectbox(label, opts, key=key, help=help_text, format_func=fmt or str)


with st.sidebar:
    sidebar_presets()
    st.header("🧮 Kosten und Einsatz (Frage 1)")
    fahrzeug = _wahl("Fahrzeug", "fahrzeug", "Rundtour, Einplanung oder Bin Packing: jedes Fahrzeug hat seine eigene Zähleinheit.")
    n_inst = st.select_slider("Zahl künftiger Instanzen N", options("n_inst"), key="n_inst", help="Wie viele neue Instanzen aus derselben Verteilung nach dem Training zu lösen sind.")
    st.markdown("**Rundtour**")
    rt_n = _wahl("Orte n (für die Kontrollstufe ℓ = 50·n)", "rt_n", "Die Länge ℓ der Kontrollstufe in Auswertungen je Instanz.", radio=True)
    rt_k = st.select_slider("Trainingsinstanzen K", options("rt_k"), key="rt_k", help="Wie viele Instanzen für das Training der Auswahl benutzt werden (Frage 1 und 2).")
    rt_art = _wahl("Art des Trainings", "rt_art", "Mischung: K Läufe; Einzelheuristik: 8·K Läufe.", fmt=lambda a: C.ARTEN_ANZEIGE[a], radio=False)
    st.markdown("**Einplanung**")
    ep_regime = _wahl("Regime", "ep_regime", "klein: Training mit 10 Aufträgen, Referenz exaktes Optimum; groß: 40 Aufträge, beste bekannte Folge.", fmt=lambda r: C.EP_REGIME_ANZEIGE[r], radio=True)
    ep_b = _wahl("Auswertungen der Suche B", "ep_b", "Budget der Erzeugung von Regeln (GP, (1+1), Zufallssuche).", radio=True)
    ep_g = _wahl("Auswertungen des Gegners g (Raster von ATC(k))", "ep_g", "Wie viele k-Werte ATC(k) auf den 20 Trainingsinstanzen ausprobiert.", radio=True)
    ep_familie = _wahl("Familie (Frage 3)", "ep_familie", "Instanzfamilie der Einplanung: E enge, M mittlere, W weite Fristen, S breite Spanne.", radio=True)
    st.markdown("**Bin Packing**")
    bp_familie = _wahl("Familie", "bp_familie", "Instanzfamilie des Bin Packing.")
    bp_k = _wahl("Größe k der Menge", "bp_k", "Eine Menge der Größe k kostet im Einsatz k Instanzläufe.", radio=True)
    bp_pr2 = _wahl("Auswertungen von PR2", "bp_pr2", "PR2 mit 8 × 8, 16 × 16 oder 32 × 32 Gitter: 64, 256 oder 1 024 Auswertungen.", radio=True)

    st.header("📈 Break-even (Frage 2)")
    h5_zelle = _wahl("Zelle", "h5_zelle", "Eine der sechs Zellen (Familie und n) oder alle.", fmt=lambda z: ANZEIGE_ZELLE.get(z, z))
    h5_akz = _wahl("Akzeptanzregel", "h5_akz", "Nur diese zwei sind für das Training gemessen.", fmt=lambda a: AKZ_NAMEN[a], radio=True)
    h5_stufe = _wahl("Einsatzbudget", "h5_stufe", "klein: 50·n Auswertungen je Instanz, groß: 200·n.", fmt=lambda s: C.STUFEN_ANZEIGE[s], radio=True)
    h5_r = _wahl("Lebensdauer des Trainings R (Instanzen)", "h5_r", "Nach R Instanzen wechselt die Verteilung und das Training ist zu wiederholen; „nie“ heißt unbegrenzt.")

    st.header("🔧 Erzeugen (Frage 3)")
    e3_fahrzeug = _wahl("Fahrzeug", "e3_fahrzeug", "Einplanung (Zelle aus Regime und Familie oben) oder Bin Packing (Familie oben).", radio=True)

    st.header("🗺️ Karte (Frage 4)")
    karte_fahrzeug = _wahl("Fahrzeug", "karte_fahrzeug", "Welche Zeilen die Karte zeigt.")
    karte_stabil = st.toggle("nur Zeilen, deren Zählung in allen Wiederholungen stabil ist", key="karte_stabil", help="Zeilen der Rundtour, bei denen das Mittel der Wiederholungen und alle Wiederholungen dasselbe zählen.")

    st.header("⏱️ Zeit (Frage 5)")
    zeit_seed = st.number_input("Zufalls-Seed der Zeitmessung", 0, C.SEED_MAX, key="zeit_seed", step=1)
    st.button("🎲 Neuer Zufalls-Seed", width="stretch", on_click=next_seed)

sync_query_params({k: st.session_state[k] for k in ("fahrzeug", "n_inst", "rt_n", "rt_k", "rt_art", "ep_regime", "ep_b", "ep_g", "ep_familie", "bp_familie", "bp_k", "bp_pr2",
                                                    "h5_zelle", "h5_akz", "h5_stufe", "h5_r", "e3_fahrzeug", "karte_fahrzeug", "karte_stabil", "zeit_seed")})

st.info(TX.ZAEHLEINHEIT_HINWEIS)

# ------------------------------------------------------------------ Frage 1
st.markdown(f"## 1. {TX.KERNFRAGEN[1]}")
einsatz_lo = KO.kontrollstufe(rt_n)
if fahrzeug == "Rundtour":
    rows = E.rows_rundtour(rt_n, rt_k, rt_art, h5_akz, h5_stufe, n_inst)
    df = pd.DataFrame(rows)
    st.dataframe(df.rename(columns={"gesamt": f"Gesamtkosten E + {n_inst}·b", "aufschlag": "Aufschlag gegen den Einsatz allein", "E": "Entwicklung E", "b": "Einsatz b je Instanz"}),
                 hide_index=True, width="stretch")
    sel = next(r for r in rows if r["Verfahren"].startswith(C.ARTEN_ANZEIGE[rt_art]))
    kind, text = E.verdict_aufschlag(sel["Verfahren"], n_inst, sel["E"], sel["b"], KO.EINHEIT["Rundtour"])
    st.plotly_chart(V.build_kosten(rows, n_inst, "Auswertungen (bewertete Kandidaten)"), width="stretch", key="chart_kosten_rt")
elif fahrzeug == "Einplanung":
    rows = E.rows_einplanung(ep_regime, ep_b, ep_g, n_inst)
    df = pd.DataFrame([dict(Verfahren=r["Verfahren"], E=r["E"], b=r["b"], Gesamt=KO.gesamt(r["E"], n_inst, r["b"]), Faktor=r["faktor"],
                            Zählung="nicht gemessen" if r["m"] == 0 else ("Referenz" if r["m"] is None else f"{r['besser']} / {r['gleich']} / {r['schlechter']} von {r['m']}"),
                            Training=r["train"], Test=r["test"], Knotenauswertungen=r["knoten"], Hinweis=r["Hinweis"]) for r in rows])
    st.dataframe(df.rename(columns={"E": "Entwicklung E (Auswertungen)", "b": "Einsatz b je Instanz (Auswertungen)", "Gesamt": f"Gesamtkosten E + {n_inst}·b", "Faktor": "Faktor gegen ATC(k)",
                                    "Zählung": "Test: besser / gleich / schlechter", "Training": "Training: Läufe besser (%)", "Test": "Test: Läufe besser (%)",
                                    "Knotenauswertungen": "Knotenauswertungen je Auswertung der Endregel"}),
                 hide_index=True, width="stretch",
                 column_config={"Training: Läufe besser (%)": st.column_config.NumberColumn(format="%.0f"), "Test: Läufe besser (%)": st.column_config.NumberColumn(format="%.0f"),
                                "Faktor gegen ATC(k)": st.column_config.NumberColumn(format="%.1f")})
    gp = next(r for r in rows if r["Verfahren"].startswith("Genetische"))
    kind, text = E.verdict_kosten("Genetische Programmierung (GP)", f"ATC(k) mit {ep_g} Werten", ep_b / ep_g, ep_b, ep_g, KO.EINHEIT["Einplanung"], gp["besser"], gp["gleich"], gp["schlechter"], gp["m"])
    st.plotly_chart(V.build_kosten([dict(Verfahren=r["Verfahren"], E=r["E"], b=r["b"]) for r in rows], n_inst, "Auswertungen (Regel auf 20 Trainingsinstanzen)"), width="stretch", key="chart_kosten_ep")
else:
    rows = E.rows_packen(bp_familie, bp_k, bp_pr2)
    df = pd.DataFrame([dict(Verfahren=r["Verfahren"], E=r["E"], b=r["b"], Gesamt=r["E"] + n_inst * r["b"] / 20, Test=r["Test"], Training=r["Training"]) for r in rows])
    st.dataframe(df.rename(columns={"E": "Entwicklung E (Auswertungen)", "b": "Einsatz b je Instanz (Läufe)", "Gesamt": f"Gesamtkosten E + {n_inst}·b/20 (Auswertungen)",
                                    "Test": "Test gegen Best Fit", "Training": "Training gegen Best Fit"}), hide_index=True, width="stretch")
    bb, gg, ss = F.bp_suche_zaehlung(1000, ["EA-S", "GP-T"])
    kind, text = E.verdict_kosten("Die Suche mit EA-S und GP-T (1 000 Auswertungen)", f"PR2 ({bp_pr2} Auswertungen)", 1000 / bp_pr2, 1000, bp_pr2, KO.EINHEIT["Bin Packing"], bb, gg, ss, bb + gg + ss)
    st.plotly_chart(V.build_kosten([dict(Verfahren=r["Verfahren"], E=r["E"], b=r["b"] / 20) for r in rows], n_inst, "Auswertungen (Regel auf 20 Trainingsinstanzen)"), width="stretch", key="chart_kosten_bp")
getattr(st, kind)(text)
st.caption("Die Spalten zu Test und Training sind eingefroren (Messungen der Demos der Reihe, nach Regel D1 bzw. der Regel der Platzierungsfunktionen); Gesamtkosten und Aufschlag rechnet die Demo live. "
           "Die Zeile „feste Teilmenge T3“ wurde nachträglich gewählt: Ihre Kosten null verschweigen die Kosten der Erkenntnis.")

st.markdown("---")

# ------------------------------------------------------------------ Frage 2
st.markdown(f"## 2. {TX.KERNFRAGEN[2]}")
zellen = F.zellen_namen(h5_zelle)
z = F.zaehlung_lohnt(h5_akz, h5_zelle, rt_art, rt_k, h5_stufe, n_inst, h5_r)
st.plotly_chart(V.build_budgetkurve(h5_akz, zellen, h5_stufe, rt_art, rt_k, n_inst, h5_r), width="stretch", key="chart_h5")
einsatz_faktor = C.LO_F if h5_stufe == "lo" else C.HI_F
kind, text = E.verdict_breakeven(z, n_inst, rt_art, rt_k, h5_akz, f"{einsatz_faktor}·n", h5_r)
getattr(st, kind)(text)
st.markdown("**Break-even N\\* je Zelle und K** (aus dem Mittel der Wiederholungen; in Klammern die Spanne über die Wiederholungen, „nie“: kein Gewinn bei gleichem Einsatzbudget, „> Kurve“: der Gewinn ist größer, als die gemessene Kurve bis 32·ℓ abdeckt)")
st.dataframe(pd.DataFrame(E.stern_tabelle(h5_akz, zellen, rt_art, h5_stufe)), hide_index=True, width="stretch",
             column_config={"Gewinn K = 1 (Pp)": st.column_config.NumberColumn(format="%+.2f"), "Gewinn K = 30 (Pp)": st.column_config.NumberColumn(format="%+.2f")})
t3 = next((r for r in F.karte_zeilen("Rundtour") if r["id"] == f"rt-t3-{h5_akz}-{0 if h5_stufe == 'lo' else 1}"), None)
if t3 is not None:
    st.caption(f"Zum Vergleich die Zeile „feste Teilmenge T3“ (E = 0, nachträglich gewählt; Zahl führt die Demo zur Zugmenge): besser / gleich / schlechter {t3['b']} / {t3['g']} / {t3['s']} von {t3['m']} Zellen "
               f"gegen die Zufallsauswahl, Mittel {E.pp(t3['mittel'])} Prozentpunkte.")

probe_key = (h5_akz, rt_art, min(rt_k, C.PROBE_K_MAX))
if st.button("▶️ Probe live rechnen", key="knopf_probe", help=f"Training auf höchstens {C.PROBE_K_MAX} Instanzen, Einsatz auf {C.PROBE_INSTANZEN} Testinstanzen mit {C.PROBE_SEEDS} Läufen (Zelle gleichverteilt, n = {C.PROBE_N})."):
    with st.spinner(f"Probe läuft (rund {E.tsd(E.probe_auswertungen_nach_budget(rt_art, rt_k))} Auswertungen nach Budget gerechnet, Rundtour)…"):
        st.session_state["probe"] = (probe_key, E.probe(h5_akz, rt_art, rt_k))
pr = st.session_state.get("probe")
if pr and pr[0] == probe_key:
    res = pr[1]
    pk, ptext = E.verdict_probe(res["mittel"], res["se"], res["m"], rt_art)
    getattr(st, pk)(ptext + f" Gerechnet: {E.tsd(res['kosten'])} Auswertungen. Aus der Probe entsteht keine N*-Zahl.")
st.caption("Die Probe ist klein (8 Instanzen) und soll nur zeigen, wie breit das Rauschen bei so wenigen Instanzen ist; die Zahlen oben sind die eingefrorene Messung (30 Instanzen, 5 Läufe, 5 Wiederholungen).")

st.markdown("---")

# ------------------------------------------------------------------ Frage 3
st.markdown(f"## 3. {TX.KERNFRAGEN[3]}")
if e3_fahrzeug == "Einplanung":
    zelle = f"{ep_regime}|{ep_familie}"
    st.plotly_chart(V.build_kosten_nutzen_ep(zelle, ep_g), width="stretch", key="chart_e3_ep")
    bb, gg, ss = F.ep_zaehlung("gp", ep_b, ep_g)
    kind, text = E.verdict_erzeugen("GP", f"ATC(k) mit {ep_g} Werten", ep_b / ep_g, bb, gg, ss, F.ep_zellen_gemessen("gp", ep_b), F.ep_anteil("gp", ep_b, ep_g, "train"), F.ep_anteil("gp", ep_b, ep_g, "test"))
    tab = [dict(Zelle=zz, **{f"ATC mit {g} Werten": 100 * F.ep_median_reue(zz, "atc", g=g) for g in C.EP_RASTER}, **{f"GP bei {b}": 100 * F.ep_median_reue(zz, "gp", b) for b in C.EP_B}) for zz in F.ep_zellen()]
    st.markdown("**Median des Regrets auf frischen Instanzen in Prozent** (20 Läufe je Zelle; Zelle: Regime und Trainingsfamilie)")
    st.dataframe(pd.DataFrame(tab), hide_index=True, width="stretch")
else:
    st.plotly_chart(V.build_kosten_nutzen_bp(bp_familie, bp_pr2), width="stretch", key="chart_e3_bp")
    bb, gg, ss = F.bp_suche_zaehlung(1000, ["EA-S", "GP-T"])
    train_a = sum(F.bp_anteil_besser(f, m, 1000, "train") for f in C.BP_FAMILIEN for m in ("EA-S", "GP-T")) / 6
    test_a = sum(F.bp_anteil_besser(f, m, 1000, "test") for f in C.BP_FAMILIEN for m in ("EA-S", "GP-T")) / 6
    kind, text = E.verdict_erzeugen("Die Suche (EA-S und GP-T, 1 000 Auswertungen)", f"PR2 mit {bp_pr2} Auswertungen", 1000 / bp_pr2, bb, gg, ss, bb + gg + ss, train_a, test_a)
getattr(st, kind)(text)
st.caption(E.text_raster(ep_b) + " Ein Break-even N* wird hier nicht angezeigt: Vom Gegner sind nur vier Rasterpunkte (ATC) bzw. drei Gitter (PR2) gemessen, und sein Verlauf ist nicht durchgehend fallend. "
           "Die Raster-Gegner sind eine Rechnung dieser Demo auf den Läufen der Demos zu Prioritätsregeln und Platzierungsfunktionen (20 Läufe, Median).")

st.markdown("---")

# ------------------------------------------------------------------ Frage 4
st.markdown(f"## 4. {TX.KERNFRAGEN[4]}")
zeilen = F.karte_zeilen(karte_fahrzeug, karte_stabil)
st.dataframe(pd.DataFrame([{"Meta-Ebene": r["meta_ebene"], "Gegner": r["gegner"], "Fahrzeug": r["fahrzeug"], "Einheit": r["einheit"], "Bedingung": r["bedingung"], "Zählung": E.zaehlung_text(r),
                            "Kosten": r["kosten"], "Entscheidungsregel": r["regel"], "Voraussetzung": r["voraussetzung"], "Stück": f"{r['stueck']}: {r['stueck_name']}"} for r in zeilen]),
             hide_index=True, width="stretch", height=380)
if zeilen:
    namen = {r["id"]: f"{r['fahrzeug']}: {r['meta_ebene']} ({r['bedingung']})" for r in zeilen}
    wahl = st.selectbox("Zeile für das Verdikt", list(namen), format_func=lambda i: namen[i], key="karte_zeile")
    kind, text = E.verdict_karte(next(r for r in zeilen if r["id"] == wahl))
    getattr(st, kind)(text)
else:
    st.info("Keine Zeile mit diesen Einstellungen.")
st.caption(TX.KLASSEN_HINWEIS + " Die Linie hat zwei Entscheidungsregeln (Einplanung: Regel D1, Packen: Median und Läufe); die Karte nennt sie in jeder Zeile und zählt nie beide zusammen. "
           "Zeilen „nicht gemessen“ sind Lücken, keine Aussagen.")

st.markdown("---")

# ------------------------------------------------------------------ Frage 5
st.markdown(f"## 5. {TX.KERNFRAGEN[5]}")
st.caption(f"Feste Messung: Rundtour n = {C.ZEIT_N}, Familie gleichverteilt, {E.tsd(C.ZEIT_AUSWERTUNGEN)} Auswertungen je Regel, Rekord-zu-Rekord, Median aus {C.ZEIT_WDH} Wiederholungen. "
           "Zeiten werden nicht gespeichert und sind nie ein Befund (Rechner und Python-Version bestimmen sie).")
if st.button("⏱️ Zeit messen", key="knopf_zeit"):
    with st.spinner(f"Zeitmessung läuft ({E.tsd(len(C.ZEIT_REGELN) * C.ZEIT_WDH * C.ZEIT_AUSWERTUNGEN)} Auswertungen)…"):
        st.session_state["zeit"] = (int(zeit_seed), E.zeit_messung(int(zeit_seed)))
zm = st.session_state.get("zeit")
if zm and zm[0] == int(zeit_seed):
    zr = zm[1]
    st.dataframe(pd.DataFrame([{"Regel": r["Regel"], "Anwendungen": r["Anwendungen"], "Auswertungen": r["Auswertungen"], "Sekunden": r["Sekunden"], "Sekunden je 1 000 Auswertungen": r["je1000"],
                                "Sekunden je 1 000 Anwendungen": r["je1000_anw"]} for r in zr]), hide_index=True, width="stretch",
                 column_config={"Sekunden": st.column_config.NumberColumn(format="%.3f"), "Sekunden je 1 000 Auswertungen": st.column_config.NumberColumn(format="%.3f"),
                                "Sekunden je 1 000 Anwendungen": st.column_config.NumberColumn(format="%.3f")})
    st.plotly_chart(V.build_zeit(zr), width="stretch", key="chart_zeit")
    kind, text = E.verdict_zeit({r["regel"]: r["je1000"] for r in zr})
    getattr(st, kind)(text)
    if len({r["Auswertungen"] for r in zr}) != 1:
        st.warning("Prüfzeile: Die Auswertungen sind nicht in allen Zeilen gleich.")
else:
    st.caption("Noch nicht gemessen: Mit dem Knopf starten.")

st.markdown("---")

with st.expander("🔧 Wie wir das erreichen – vollständiger Vergleich", expanded=False):
    st.markdown("**Benannte Verfahren**")
    st.markdown(TX.ERKLAERTABELLE_MD)
    st.markdown("**Kostenbuch aller drei Fahrzeuge** (je Fahrzeug in dessen Einheit; Einstellungen wie in der Seitenleiste)")
    tabs = st.tabs(list(FAHRZEUGE))
    with tabs[0]:
        st.dataframe(pd.DataFrame(E.rows_rundtour(rt_n, rt_k, rt_art, h5_akz, h5_stufe, n_inst)), hide_index=True, width="stretch")
    with tabs[1]:
        st.dataframe(pd.DataFrame(E.rows_einplanung(ep_regime, ep_b, ep_g, n_inst)), hide_index=True, width="stretch")
    with tabs[2]:
        st.dataframe(pd.DataFrame(E.rows_packen(bp_familie, bp_k, bp_pr2)), hide_index=True, width="stretch")

st.markdown("---")

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(TX.ASSUMPTIONS_MARKDOWN)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(TX.FORMEL_LESEHILFE)
    for beschreibung, formel in TX.FORMEL_BLOECKE:
        st.markdown(beschreibung)
        st.latex(formel)
    st.markdown(TX.FORMEL_TABELLE)
    st.markdown(TX.FORMEL_SCHLUSS)
    st.markdown(TX.LITERATUR)

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Hyperheuristiken: Auswählen und Erzeugen](https://sebastianhanisch.net/konzepte-hyperheuristiken.html)."
)
