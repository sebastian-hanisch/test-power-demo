# Teststärke und Stichprobenumfang: wie viele Fenster reichen? – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-test-power-demo.streamlit.app/)**

Interaktive Demo zur **Planung eines Feldversuchs**. **Zweites Stück der Konzepte-Linie „Experimente und
Wirkungsmessung“** im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und Machine
Learning), Kind des [A/B-Tests](https://github.com/sebastian-hanisch/ab-test-demo): dort die Frage nach dem Experiment („ist
der Unterschied echt?“), hier die davor („wie viele Fenster muss ich messen, damit ein echter Vorteil gefunden wird?“). Das
Vehikel ist dasselbe: ein Standort mit täglicher Nachbestellung, Regel A (Sicherheitsfaktor 1,0) gegen Regel B, Einheit ist ein
Standort-Fenster von vier Wochen, Kennzahl der Servicegrad.

## Kernfrage

Was findet ein Test mit n Fenstern gerade noch, wie weit liegt ein signifikantes Ergebnis daneben, und wie gut ist die
übliche Planung aus einem kleinen Pilot?

## Modell und Methodik

- **Vehikel und Pools** wie im ersten Stück (`pwr_vehicle.py`, `generate_precomputed.py`): je Sicherheitsfaktor 10 000
  unabhängige Standort-Fenster aus SplitMix64-Strömen; die Wahrheit ist das Poolmittel, ein Experiment zieht n Fenster je Arm
  mit Zurücklegen.
- **Teststärke-Tabelle** (`precomputed_pools.json`, Abschnitt `power_tables`): je Sicherheitsfaktor und Umfang (2 bis 1 000) der
  Anteil signifikanter Welch-Tests über 1 000 bzw. 500 Wiederholungen.
- **Nachweisbarer Effekt:** Normalformel `Δ_min = (1,96 + 0,84) · sqrt((σ_A² + σ_B²) / n)`.
- **Planung aus einem Pilot** (`pilot_plans`): 2 000 Piloten mit m Fenstern je Arm, daraus vier Regeln für den Umfang der
  Hauptstudie: *Pilot-Wirkung einsetzen*, *nur nach signifikantem Pilot*, *untere 80-%-Grenze der Pilot-Wirkung* und *kleinste
  lohnende Wirkung (2 Prozentpunkte) fest vorgeben, Streuung aus dem Pilot*. Bewertet wird jede Regel mit der gemessenen
  Teststärke der Tabelle bei dem geplanten Umfang.
- **Dauer:** jede Runde braucht vier Wochen Einschwingen und vier Wochen Messfenster, also 8 Wochen; 2n Fenster auf S
  Standorten sind `ceil(2n / S)` Runden.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. Wahre Wirkung bei Sicherheitsfaktor 1,4: **3,49 Prozentpunkte** Servicegrad.

| Frage | Befund |
|---|---|
| Wie viele Fenster für 80 % Teststärke? | Faktor 1,4: **26** Fenster je Arm; Faktor 1,2 (Wirkung 1,96 Punkte): **94**; Faktor 1,8: **11**. Die Tabelle erreicht 80 % bei 27, 95 und 11. |
| Was kostet die Lehrbuchformel mit gleicher Streuung? | Die Streuung ist in B kleiner als in A (B ist ruhiger). Mit der Streuung von A für beide Arme verlangt die Formel bei Faktor 1,4 **34** statt 26 Fenster. |
| Was findet ein Test mit n Fenstern? | Bei 80 % Teststärke bei 30 Fenstern **3,2 Prozentpunkte**, bei 100 Fenstern **1,8**, bei 500 Fenstern **0,8**: vierfacher Umfang, halbe nachweisbare Wirkung. |
| Wie groß ist die Überschätzung? | Unter den signifikanten Ergebnissen ist die Schätzung bei etwa 86 % Teststärke das **1,08-Fache** der Wahrheit, bei 54 % das **1,4-Fache**, bei 26 % das **2,0-Fache** und bei 10 % das **3,7-Fache**. |
| Plant man aus einem Pilot von 10 Fenstern je Arm? | Der geplante Umfang liegt im Median bei 26, streut aber von **8 bis 231** (10 bis 90 %). Die Hauptstudie erreicht im Mittel **72 %** Teststärke, **43 %** der Studien liegen unter 70 %. |
| Mit einem größeren Pilot (50 Fenster)? | Mittlere Teststärke **77 %**, **35 %** der Studien unter 70 %: ein größerer Pilot hilft, löst es nicht. |
| Und wenn man erst nach einem signifikanten Pilot plant? | Nur **36 %** der Piloten sind signifikant, deren Wirkung ist zu groß geschätzt; die Hauptstudie erreicht im Mittel **39 %** Teststärke, alle liegen unter 70 %. |
| Was hilft? | Die **kleinste lohnende Wirkung** (2 Punkte) fest vorgeben: mittlere Teststärke **98 %**, Umfang im Median **75**. Die **untere Grenze** der Pilot-Wirkung einsetzen: **93 %**, aber im Median **351** Fenster je Arm. |
| Wann trägt auch das nicht? | Ist die wahre Wirkung kleiner als die gesetzte Schwelle (Faktor 1,2: 1,96 gegen 2 Punkte), erreichen die Studien im Mittel nur **74 %**. |
| Wie lange dauert es? | 30 Fenster je Arm auf 10 Standorten: **48 Wochen**; auf 4 Standorten **120 Wochen**. |

## Befunde und Korrekturen gegenüber dem Plan

- **Die Vorab-Messreihe auf dem Terminal-Gate** (Tagesmittel der Wartezeit) fand dasselbe Muster: Typ-M-Überschätzung bei
  kleiner Teststärke, ein Pilot von 10 Einheiten streut von 11 bis 173 geplanten Einheiten. Dort lag die Normalformel mit
  gleicher Streuung 1,8-fach über dem Bedarf; hier ist es 1,3-fach (34 gegen 26).
- **Die Planung nach signifikantem Pilot ist der Kernbefund.** Er war im Plan nicht vorgesehen und entstand aus der Frage, was
  Praktiker tatsächlich tun: erst ein Pilot, dann „es scheint zu wirken, jetzt richtig messen“.
- **Dass ein größerer Pilot die Planung nicht auf 80 % bringt,** liegt naheliegend daran, dass der Umfang mit 1/Wirkung² geht:
  zu kleine Schätzungen planen große, zu große kleine Studien. Das ist die Interpretation, nicht isoliert gemessen.

## Ehrliche Grenzen

| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Der Umfang steht vorher fest** | Wer zwischendurch hinsieht und früh stoppt, ändert Fehlalarmrate und Teststärke. | Zwischenblicke und dauerndes Hinsehen |
| **Streuung und Wirkung sind aus dem Pilot schätzbar** | Ein kleiner Pilot streut stark; die Planung ist so unsicher wie er. | Varianzreduktion |
| **Ein Test, eine Kennzahl** | Mehrere Kennzahlen brauchen einen strengeren Schwellenwert und damit mehr Fenster. | Viele Kennzahlen: Mehrfachtests und Gewinnerfluch |
| **Einheiten unabhängig und gleichartig** | Verhältniskennzahlen, Cluster und Serienkorrelation vergrößern die nötige Zahl. | Verhältniskennzahlen und Cluster |
| **Die Zuteilung lief wie geplant** | Verlust von Fenstern verkleinert den Umfang und kann verzerren. | Gültigkeit der Zuteilung (A/A, Sample-Ratio-Mismatch) |
| **Die Verteilung ist harmlos** | Hier schief, aber harmlos; mit Ausreißern verliert der Test Teststärke. | Schiefe Daten und Ausreißer |

Die Zahlen gelten für dieses erfundene Vehikel mit unabhängigen Fenstern; die Dauer rechnet mit einer festen Rundenlänge und
gleichzeitig messenden Standorten, ohne Rüst- oder Auswertezeiten.

## Bezug zu OR

Wie lange man einen Pilotbetrieb laufen lassen muss, ist eine Planungsfrage mit Kosten: jede Woche mit der schlechteren Regel
kostet Fehlmengen, jede zu kurze Studie kostet die Entscheidung. Die Demo macht aus „wir messen mal ein paar Wochen“ eine
Rechnung mit Umfang, Streuung und Standortzahl.

## Verwandte Demos im Portfolio

- [ab-test-demo](https://github.com/sebastian-hanisch/ab-test-demo): das erste Stück der Linie (Vehikel, Welch-Test, Abdeckung).
- [output-analysis-demo](https://github.com/sebastian-hanisch/output-analysis-demo): dort die Frage „wie viele Kunden muss man
  simulieren“ für Intervalle aus einem Lauf; hier unabhängige Fenster und Teststärke.
- [forecast-inventory-demo](https://github.com/sebastian-hanisch/forecast-inventory-demo): die Base-Stock-Regel des Vehikels.

## Verifikation

- **Vehikel, Zufall, Test:** wie im ersten Stück (Mini-Instanz von Hand, SplitMix64-Referenzwerte, Welch gegen scipy, Formel
  gegen Faltung und Simulation).
- **Planung:** Normalformel und nachweisbare Wirkung von Hand, Dauer von Hand, Interpolation der Tabelle, Eigenschaften der
  vier Planungsregeln (untere Grenze nie kleiner als die Punktschätzung, Relevanzregel unabhängig von der Pilot-Wirkung).
- **Konsistenz:** Tabelle gleich Live-Messung bei gleicher Ziehung.
- **Befunde:** jede Zahl dieses READMEs in `tests/test_claims.py`.
- **Presets, Oberfläche, Footer:** vollständig, Permalink eingerastet, AppTest-Rauchtest, Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: nachweisbarer Effekt, Überschätzung, Planung aus einem Pilot, Grenzen |
| `pwr_constants.py` | Vehikel-Konstanten, Regler-Grenzen, Farben, Presets |
| `pwr_rng.py`, `pwr_vehicle.py`, `pwr_formulas.py`, `pwr_stats.py` | Zufall, Standort-Fenster, exakter Servicegrad, Welch-Test und Normalformel (aus dem ersten Stück) |
| `pwr_evaluation.py` | Experimente, Teststärke-Tabellen, nachweisbare Wirkung, Pilot-Planung, Dauer |
| `pwr_presets.py` | Permalink (Begrenzen, Einrasten), Presets, Zufalls-Seed-Button |
| `pwr_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `generate_precomputed.py`, `precomputed_pools.json` | Pools und Teststärke-Tabellen |
| `tools/measure_stueck2.py`, `tools/claims_numbers.py` | Messreihe vor dem Text, README-Zahlen |
| `tests/` | Vehikel, Orakel, Statistik, Planung, Auswertung, Presets, Befunde, AppTest, Footer |

## Bewusst nicht umgesetzt

- **Sequentielle Pläne** (frühes Stoppen mit gültigen Grenzen): eigenes Stück.
- **Bayes'sche Entwurfsrechnung (Assurance):** nicht gebaut.
- **Planung mit mehreren Kennzahlen:** eigenes Stück.
- **Kosten der Fehlentscheidung** (Wert der Information): hier nur die Dauer, keine Geldrechnung.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy (Verteilungsfunktionen).

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Experimente und Wirkungsmessung: A/B bis Logdaten](https://sebastianhanisch.net/konzepte-experimente-wirkungsmessung.html).
