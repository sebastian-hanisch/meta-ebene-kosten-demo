"""Rechnet die Messung H5 vor (Rundtour, Training der Auswahl, Budgetkurve des Gegners) und schreibt data/mek_h5.json.

    python tools/mek_make_h5.py messen [--procs 2]    rechnet alle Aufträge, Rohdaten nach %TEMP%/sh-tests/mek_roh/ (setzt fort, was schon da ist)
    python tools/mek_make_h5.py bauen                 liest die Rohdaten und schreibt data/mek_h5.json
    python tools/mek_make_h5.py --check               rechnet 5 Instanzen einer Zelle neu und vergleicht als Band mit der JSON

Aufbau (wie die Vormessung H5, mit SplitMix64 statt numpy.default_rng und 5 statt 3 Wiederholungen): 6 Zellen (3 Familien × n = 30, 60), 30 Testinstanzen
(Zufalls-Seeds 0 bis 29) × 5 Läufe, zwei Akzeptanzregeln (Rekord-zu-Rekord, Late Acceptance mit L = 50). Training: 30 Trainingsinstanzen je Wiederholung
(Instanz 1000 + 30 r + k), Trainingsbudget je Instanz ℓ = 50·n. Gegner: Zufallsauswahl über alle acht Zugarten, Kurve bis 32·ℓ mit Kontrollpunkten bei
1, 1,5, 2, 3, 4, 6, 8, 12, 16, 24 und 32 mal ℓ. Referenz je Instanz: Minimum aus mek_refs.json (Langläufe von Stück 2) und allen Läufen dieser Messung.
Abstand = 100 (Länge − Referenz) / Referenz in Prozent."""

import json
import multiprocessing as mp
import os
import pickle
import platform
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mek_constants as C  # noqa: E402
import mek_train as T  # noqa: E402

ROH = Path(tempfile.gettempdir()) / "sh-tests" / "mek_roh"
AUSGABE = ROOT / "data" / "mek_h5.json"
INST = list(range(C.H5_INSTANZEN))


def zellenname(f: str, n: int) -> str:
    return f"{f}/{n}"


def train_zelle(familie: str, n: int, akz: str):
    """{(wdh, K): (p, Index der besten Einzelheuristik)}: je Wiederholung ein Durchlauf über 30 Trainingsinstanzen, an K = 1, 3, 10, 30 abgegriffen."""
    out = {}
    for wdh in range(C.H5_WDH):
        summe = [0.0] * C.K
        anw = [0] * C.K
        verh = [[] for _ in range(C.K)]
        for k in range(max(C.H5_KS)):
            s, a, v = T.train_instance(familie, n, C.H5_TRAIN_OFFSET + 30 * wdh + k, akz)
            summe = [x + y for x, y in zip(summe, s)]
            anw = [x + y for x, y in zip(anw, a)]
            for h in range(C.K):
                verh[h].append(v[h])
            if k + 1 in C.H5_KS:
                mittel = [sum(x) / len(x) for x in verh]
                out[(wdh, k + 1)] = (T.gewichte(summe, anw), min(range(C.K), key=lambda h: (mittel[h], h)))
    return out


def _train_job(args):
    familie, n, akz = args
    return (akz, familie, n), train_zelle(familie, n, akz)


def job(args):
    """Rohwerte einer Testinstanz: Kurve des Gegners, Mischungen, alle Einzelheuristiken (je 5 Läufe)."""
    familie, n, idx, akz, trained = args
    lo, hi = C.LO_F * n, C.HI_F * n
    cks = tuple(int(m * lo) for m in C.H5_MULTS)
    curve = []
    for s in range(C.H5_SEEDS):
        r, _ = T.lauf(familie, n, idx, s, C.ALLE_ZUGARTEN, akz, cks[-1], None, cks)
        curve.append(list(r["ck"]))
    mix = {}
    for (wdh, k), (p, _) in trained.items():
        lo_, hi_ = [], []
        for s in range(C.H5_SEEDS):
            r, _ = T.lauf(familie, n, idx, s, C.ALLE_ZUGARTEN, akz, hi, T.MixSelector(p), (lo,))
            lo_.append(r["ck"][0])
            hi_.append(r["best"])
        mix[(wdh, k)] = (lo_, hi_)
    single = {}
    for h in range(C.K):
        lo_, hi_ = [], []
        for s in range(C.H5_SEEDS):
            r, _ = T.lauf(familie, n, idx, s, (h,), akz, hi, None, (lo,))
            lo_.append(r["ck"][0])
            hi_.append(r["best"])
        single[h] = (lo_, hi_)
    return (akz, familie, n, idx), dict(curve=curve, mix=mix, single=single)


def messen(procs: int) -> None:
    ROH.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with mp.Pool(procs) as pool:
        tr_path = ROH / "training.pkl"
        if tr_path.exists():
            trained = pickle.loads(tr_path.read_bytes())
        else:
            todo = [(f, n, a) for a in C.H5_AKZ for (f, n) in C.H5_ZELLEN]
            trained = dict(pool.map(_train_job, todo))
            tr_path.write_bytes(pickle.dumps(trained))
        print(f"Training fertig {time.time() - t0:.0f} s", flush=True)
        for akz in C.H5_AKZ:
            for (f, n) in C.H5_ZELLEN:
                pfad = ROH / f"roh_{akz}_{f}_{n}.pkl"
                if pfad.exists():
                    continue
                tr = trained[(akz, f, n)]
                res = dict(pool.imap(job, [(f, n, idx, akz, tr) for idx in INST], chunksize=1))
                pfad.write_bytes(pickle.dumps(res))
                print(f"{akz} {f}/{n} fertig {time.time() - t0:.0f} s", flush=True)


def _mean(x):
    return sum(x) / len(x)


def luecke(wert: float, ref: float) -> float:
    return 100.0 * (wert - ref) / ref


def auswerten(roh: dict, trained: dict, refs: dict):
    """Fasst die Rohwerte zu Abständen zusammen. roh[(akz, f, n, idx)], Rückgabe: Wörterbuch im Format der JSON."""
    out = dict(kurve={}, kurve_inst={}, mix={}, einzel={}, einzel_alle={}, p={}, ref={})
    for (f, n) in C.H5_ZELLEN:
        zn = zellenname(f, n)
        ref = []
        for idx in INST:
            werte = [refs["refs"][f][str(n)][idx]]
            for akz in C.H5_AKZ:
                d = roh[(akz, f, n, idx)]
                werte += [x for zeile in d["curve"] for x in zeile]
                werte += [x for lo_, hi_ in d["mix"].values() for x in lo_ + hi_]
                werte += [x for lo_, hi_ in d["single"].values() for x in lo_ + hi_]
            ref.append(min(werte))
        out["ref"][zn] = ref
    for akz in C.H5_AKZ:
        for key in ("kurve", "kurve_inst", "mix", "einzel", "einzel_alle", "p"):
            out[key][akz] = {}
        for (f, n) in C.H5_ZELLEN:
            zn = zellenname(f, n)
            ref = out["ref"][zn]
            inst_kurve = []
            for i, idx in enumerate(INST):
                zeilen = roh[(akz, f, n, idx)]["curve"]
                inst_kurve.append([_mean([luecke(zeilen[s][j], ref[i]) for s in range(C.H5_SEEDS)]) for j in range(len(C.H5_MULTS))])
            out["kurve_inst"][akz][zn] = [[round(x, 5) for x in z] for z in inst_kurve]
            out["kurve"][akz][zn] = [round(_mean([z[j] for z in inst_kurve]), 5) for j in range(len(C.H5_MULTS))]
            tr = trained[(akz, f, n)]
            mix = []
            einzel = []
            pp = []
            for wdh in range(C.H5_WDH):
                zeile, ez, pz = [], [], []
                for k in C.H5_KS:
                    stufe = []
                    for sidx in (0, 1):
                        stufe.append(round(_mean([_mean([luecke(roh[(akz, f, n, idx)]["mix"][(wdh, k)][sidx][s], ref[i]) for s in range(C.H5_SEEDS)])
                                                  for i, idx in enumerate(INST)]), 5))
                    zeile.append(stufe)
                    p, h = tr[(wdh, k)]
                    ez.append(h)
                    pz.append([round(x, 6) for x in p])
                mix.append(zeile)
                einzel.append(ez)
                pp.append(pz)
            out["mix"][akz][zn] = mix
            out["einzel"][akz][zn] = einzel
            out["p"][akz][zn] = pp
            alle = {"lo": [], "hi": []}
            for h in range(C.K):
                for sidx, st in ((0, "lo"), (1, "hi")):
                    alle[st].append(round(_mean([_mean([luecke(roh[(akz, f, n, idx)]["single"][h][sidx][s], ref[i]) for s in range(C.H5_SEEDS)])
                                                 for i, idx in enumerate(INST)]), 5))
            out["einzel_alle"][akz][zn] = alle
    for zn in out["ref"]:
        out["ref"][zn] = [round(x, 6) for x in out["ref"][zn]]
    return out


def bauen() -> None:
    refs = json.loads((ROOT / "mek_refs.json").read_text(encoding="utf-8"))
    trained = pickle.loads((ROH / "training.pkl").read_bytes())
    roh = {}
    for akz in C.H5_AKZ:
        for (f, n) in C.H5_ZELLEN:
            for idx, d in pickle.loads((ROH / f"roh_{akz}_{f}_{n}.pkl").read_bytes()).items():
                roh[idx] = d
    erg = auswerten(roh, trained, refs)
    auswertungen = 0
    for akz in C.H5_AKZ:
        for (f, n) in C.H5_ZELLEN:
            lo = C.LO_F * n
            je_inst = (C.H5_SEEDS * 32 * lo + len(C.H5_KS) * C.H5_WDH * C.H5_SEEDS * 4 * lo + C.K * C.H5_SEEDS * 4 * lo)
            auswertungen += je_inst * C.H5_INSTANZEN + C.H5_WDH * max(C.H5_KS) * 9 * lo
    meta = dict(schema=1, zellen=[zellenname(f, n) for f, n in C.H5_ZELLEN], akzeptanzen=list(C.H5_AKZ), wiederholungen=C.H5_WDH, ks=list(C.H5_KS),
                mults=list(C.H5_MULTS), instanzen=C.H5_INSTANZEN, laeufe=C.H5_SEEDS, lo_faktor=C.LO_F, hi_faktor=C.HI_F,
                trainingsinstanzen_ab=C.H5_TRAIN_OFFSET, auswertungen_gesamt=auswertungen, python=platform.python_version(), rechner=platform.system(),
                zufall="SplitMix64 (mek_rng.py)", einheit="Abstand zur Referenz in Prozent; Auswertungen = bewertete Kandidaten")
    AUSGABE.parent.mkdir(exist_ok=True)
    AUSGABE.write_text(json.dumps(dict(meta=meta, **erg), separators=(",", ":"), ensure_ascii=False), encoding="utf-8", newline="\n")
    print("geschrieben:", AUSGABE, f"{AUSGABE.stat().st_size / 1e6:.2f} MB; Auswertungen {auswertungen:,}")


def rechne_check(familie="gleich", n=30, akz="rr", idxs=(0, 1, 2, 3, 4), wdh=0, k=3):
    """Kleine Neurechnung für Tests: Abstand des Gegners bei ℓ und der gelernten Mischung (Wiederholung wdh, K = k) über die Instanzen idxs.

    Rückgabe: (Mittel Gegner bei ℓ, Mittel Mischung bei ℓ, Standardfehler der gepaarten Differenz), jeweils in Prozent, gegen die Referenz aus mek_refs.json."""
    refs = json.loads((ROOT / "mek_refs.json").read_text(encoding="utf-8"))
    p, _ = T.trainiere(familie, n, T.training_instanzen(wdh, k), akz, einzel=False)
    lo = C.LO_F * n
    g, m = [], []
    for idx in idxs:
        ref = refs["refs"][familie][str(n)][idx]
        gi, mi = [], []
        for s in range(C.H5_SEEDS):
            r, _ = T.lauf(familie, n, idx, s, C.ALLE_ZUGARTEN, akz, lo, None, (lo,))
            gi.append(luecke(r["ck"][0], ref))
            r, _ = T.lauf(familie, n, idx, s, C.ALLE_ZUGARTEN, akz, lo, T.MixSelector(p), (lo,))
            mi.append(luecke(r["ck"][0], ref))
        g.append(_mean(gi))
        m.append(_mean(mi))
    d = [a - b for a, b in zip(g, m)]
    md = _mean(d)
    se = (sum((x - md) ** 2 for x in d) / max(len(d) - 1, 1)) ** 0.5 / len(d) ** 0.5
    return _mean(g), _mean(m), se


def check() -> int:
    daten = json.loads(AUSGABE.read_text(encoding="utf-8"))
    g, m, se = rechne_check()
    kurve = daten["kurve"]["rr"]["gleich/30"][0]
    mix = daten["mix"]["rr"]["gleich/30"][0][C.H5_KS.index(3)][0]
    print(f"Gegner bei l: neu {g:.3f}, gespeichert {kurve:.3f}; Mischung K = 3: neu {m:.3f}, gespeichert {mix:.3f}; Standardfehler {se:.3f}")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--check" in args:
        sys.exit(check())
    if args and args[0] == "messen":
        procs = int(args[args.index("--procs") + 1]) if "--procs" in args else 2
        os.environ.setdefault("OMP_NUM_THREADS", "1")
        messen(procs)
    elif args and args[0] == "bauen":
        bauen()
    else:
        print(__doc__)
