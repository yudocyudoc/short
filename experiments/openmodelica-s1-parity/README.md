# S1 parity — Hines PySD versus OpenModelica / SystemDynamics

## Goal and scope

Compare the *same* S1 synthetic make-to-stock mechanism using three implementations: the original SHA-verified Hines Vensim models executed by PySD 3.14.3; a new mathematical Modelica restatement; and a native SystemDynamics Levels + Rates composition. This does not estimate real bakery capacity or prove a universal compiler.

## Identical conditions

The shared fixture is experiments/molecule-composer-v1/synthetic_mts.json. T = 0..8 hours; Euler dt = 0.25 h (33 saved points); hypothetical capacity = 12 units/h; planned production = 8 units/h; independently accepted orders = 6/h; backlog0 = 5; finished-stock0 = 12; min ship time = .25 h; process-and-ship target = .5 h.

The equations are fixed to the two original Hines mechanisms: production = capacity × CapUtilLookup(planned/capacity); derivative backlog = accepted - shipping; derivative inventory = production - shipping; maximumShipping = inventory / minShipTime; indicatedFraction = backlog / processShipTime / maximumShipping, using fallback 10 when maximumShipping is zero; shipping = maximumShipping × ShippingFractionLookup(indicatedFraction). Exact curve knots are verified by test_parity.py against the existing frozen Hines manifest.

No rewriting the shipping policy as min(backlog,cap), no making production strictly follow accepted orders, and no using checkout timestamps as real arrivals. Modelica is an independently authored mathematical restatement, not redistribution of the original Vensim .mdl file.

## Three runs

1. PySD loads temporary verified publisher CapUtil.mdl and invbakf.mdl using the existing, unit-label-only, temporary adapter.
2. OpenModelica 1.26.3 runs IGCS1Parity.Equations with explicit ODE states, Euler, 32 intervals.
3. OpenModelica 1.26.3 with BSD-3-Clause SystemDynamics 2.1.2 runs IGCS1Parity.Components with Level and Rate_1 connectors, Euler, 32 intervals.

A deterministic Python comparator checks 33 timepoints × 4 variables (production, shipping, backlog, inventory) for all three pairs: OMC equations vs PySD; OMC components vs PySD; components vs equations. Predeclared absolute tolerance 1e-4.

PASS means numerical agreement for this conditional scenario, **not causal or operational validation**. BLOCKED means an environment/library/translation problem, and MISMATCH means numerical disagreement. The subjective claim that components are easier to assemble is NOT MEASURED by numerical parity; it needs a second practical benchmark.

The workflow publishes only derived outputs, input hashes and execution logs. Original Hines .mdl bytes remain outside GitHub and artifacts. No LLM calls in this experiment.

## Project files

- IGCS1Parity.mo: mathematical model and native component model.
- equations.mos / components.mos: scripted CLI simulation.
- test_parity.py: offline input and curve integrity.
- compare.py: timestamp-by-timestamp adjudication and quantitative report.
- .github/workflows/igc-openmodelica-s1-parity.yml: CI.

Source: https://build.openmodelica.org/Documentation/SystemDynamics.html (SystemDynamics 2.1.2, BSD-3-Clause).
