        raise ValueError("observed_mitigation_fraction must be numeric and between 0 and 1")
    mapping = {"monitor": "monitor", "mitigate": "rate_limit", "rate_limit": "rate_limit",
               "escalate": "isolate", "isolate": "isolate"}
    df["action_normalized"] = df["action"].astype(str).str.strip().str.lower().map(mapping)
    if df["action_normalized"].isna().any():
        raise ValueError("action values must be Monitor/Mitigate/Escalate or monitor/rate_limit/isolate")
    means = df.groupby("action_normalized")["observed_mitigation_fraction"].agg(["mean", "std", "count"]).reset_index()
    factors = {}
    for _, row in means.iterrows():
        action = row["action_normalized"]
        factors[action] = float(row["mean"] / max(ACTION_MITIGATION[action], 1e-9))
    note = ("Calibration multipliers were derived from the uploaded observed mitigation fractions. "
            "Use only observations measured under comparable conditions with a documented outcome definition. "
            "This does not calibrate transition probabilities or latency unless those are separately observed and modeled.")
    return factors, means, note

def run_sensitivity_analysis(seed: int, episodes: int, steps: int, weights: Dict[str, float],
                             alpha: float, gamma: float, epsilon: float, n_runs: int, n_per_run: int,
                             calibration_factors: Dict[str, float] | None = None) -> pd.DataFrame:
    """Genuine one-factor-at-a-time reruns: retrain and reevaluate for each assumption set."""
    variants = [
        ("Reference assumptions", 1.00, 1.00, 1.00),
        ("Transition rows blended 50% toward uniform", 0.50, 1.00, 1.00),
        ("Transition rows blended 100% toward uniform", 0.00, 1.00, 1.00),
        ("Action effectiveness -25%", 1.00, 0.75, 1.00),
        ("Action effectiveness +25%", 1.00, 1.25, 1.00),
        ("Network-noise effect -25%", 1.00, 1.00, 0.75),
        ("Network-noise effect +25%", 1.00, 1.00, 1.25),
    ]
    rows = []
    for i, (label, trans_mix, eff_scale, noise_scale) in enumerate(variants):
        q = train_q_policy(seed + 101_000 + i * 17, episodes, steps, weights, alpha, gamma, epsilon,
                           transition_mix=trans_mix)
        detail, wide = evaluate(seed + 202_000 + i * 31, n_runs, n_per_run, q, eff_scale, noise_scale, calibration_factors)
        run_diff = wide.groupby("run_id")[["resulting_risk__diff_AO_minus_baseline",
                                            "simulated_latency_ms__diff_AO_minus_baseline"]].mean()
        rows.append({"Sensitivity condition": label, "Transition mix": trans_mix,
                     "Action-effect scale": eff_scale, "Network-noise scale": noise_scale,
                     "Mean paired risk difference (AO - baseline)": run_diff["resulting_risk__diff_AO_minus_baseline"].mean(),
                     "Mean paired latency difference ms (AO - baseline)": run_diff["simulated_latency_ms__diff_AO_minus_baseline"].mean(),
                     "Risk direction favors AO?": bool(run_diff["resulting_risk__diff_AO_minus_baseline"].mean() < 0),
                     "Latency direction favors AO?": bool(run_diff["simulated_latency_ms__diff_AO_minus_baseline"].mean() < 0)})
    return pd.DataFrame(rows)


def benchmark_real_crypto_switching(seed: int, n_events: int = 30) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
    """Run real RSA/ECDSA signing+verification and record actual suite-selection transitions.

    The suite selector is a transparent test policy, not present in the original dashboard.
    This benchmark measures actual operations for RSA/ECC/Hybrid where cryptography is installed.
    PQC is deliberately excluded unless a validated PQC backend is integrated.
    """
    if not CRYPTO_BACKEND_AVAILABLE:
        return pd.DataFrame(), pd.DataFrame(), "The Python cryptography package is unavailable; no cryptographic operations were run."
    rng = np.random.default_rng(seed)
    # Deterministic, reproducible event stream. Mode selection is a test rule, not claimed to be
    # the original AO-LACCP behavior. It allows measurement of actual suite changes/operations.
    events = []
    for i in range(n_events):
        pressure = float(rng.random())
        threat = str(rng.choice(["benign", "brute_force", "mitm", "zero_day"]))
        if threat in ("mitm", "zero_day") or pressure >= .70:
            suite = "Hybrid (RSA+ECDSA)"
        elif pressure >= .35:
            suite = "ECDSA"
        else:
            suite = "RSA"
        events.append({"event_id": i + 1, "threat_type": threat, "crypto_pressure": pressure, "selected_suite": suite})
    # Generate real keys once; per-event signing and verification use the selected suite.
    rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ec_key = ec.generate_private_key(ec.SECP256R1())
    payload = b"AO-LACCP crypto-switch benchmark payload"
    rows = []
    previous = None
    for ev in events:
        suite = ev["selected_suite"]
        switched = previous is not None and suite != previous
        t0 = time.perf_counter()
        ok = True
        try:
            if suite in ("RSA", "Hybrid (RSA+ECDSA)"):
                sig_rsa = rsa_key.sign(payload, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                    salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
                rsa_key.public_key().verify(sig_rsa, payload, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                    salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
            if suite in ("ECDSA", "Hybrid (RSA+ECDSA)"):
                sig_ec = ec_key.sign(payload, ec.ECDSA(hashes.SHA256()))
                ec_key.public_key().verify(sig_ec, payload, ec.ECDSA(hashes.SHA256()))
        except Exception:
            ok = False
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        rows.append({**ev, "suite_changed_from_previous_event": bool(switched),
                     "operation_success": bool(ok), "sign_verify_elapsed_ms": elapsed_ms,
                     "operations_performed": 2 if suite != "Hybrid (RSA+ECDSA)" else 4})
        previous = suite
    trace = pd.DataFrame(rows)
    total_switches = int(trace["suite_changed_from_previous_event"].sum())
    success_rate = float(trace["operation_success"].mean()) if len(trace) else float("nan")
    summary = pd.DataFrame([{"Events": len(trace), "Suite transitions observed": total_switches,
                             "Transition rate (excluding first event)": total_switches / max(1, len(trace)-1),
                             "Successful sign/verify events": int(trace["operation_success"].sum()),
                             "Operation success rate": success_rate,
                             "Mean sign/verify elapsed ms": float(trace["sign_verify_elapsed_ms"].mean()),
                             "PQC tested": False}])
    note = ("This executes real RSA-2048 and ECDSA P-256 signing/verification and counts suite-selection changes. "
            "It is a separate benchmark harness, not evidence that the original AO-LACCP dashboard performs these switches. "
            "PQC is not tested because no PQC backend is integrated; do not claim PQC agility from these results.")
    return trace, summary, note

def main() -> None:
    st.title("AO-LACCP: Scientific Paired Evaluation Prototype")
    st.warning("Synthetic model only. This app can test reproducibility and conditional behavior; it cannot by itself validate real-world banking efficacy or justify uncalibrated simulation assumptions.")
    with st.expander("Protocol, policy and limitations", expanded=True):
        st.markdown("""
**Design:** Q-learning is trained on synthetic training scenarios and then frozen. Evaluation uses independent held-out scenarios. Each held-out scenario is passed unchanged to the baseline and AO-LACCP policy.

**Baseline:** fixed thresholds on initial risk, threat signal and cryptographic pressure. This is one explicit comparator, not a claim to represent all production SOCs.

**Policy alignment audit:** the Q-learning state/action/reward/transition structure below now reproduces the current `ao_laccp_full_framework_updated.py` illustrative MDP: Low/Medium/High; Monitor/Mitigate/Escalate; configured state-only transition rows; matching-action rewards +10/+20/+30 and -5 otherwise. The original artifact does NOT connect this Q-table to its generated risk/latency/agility outcomes. The mapping from actions to outcome effects in this evaluation is therefore an explicitly added bridge assumption, not verified original behavior.

**Shared outputs:** both policies use the same synthetic outcome equations. The action-effect bridge and scenario generator are not empirically calibrated. A separate cryptographic benchmark below performs real RSA/ECDSA signing and verification and records suite transitions, but it does not validate the original dashboard or PQC switching.

**Inference:** scenarios are nested within independent simulation runs. The primary statistical summaries therefore use run-level mean differences, with confidence intervals, effect sizes and Holm correction across the displayed metrics.

**Before dissertation use:** pre-specify primary outcomes and reward weights; justify/calibrate scenario and action-effect parameters; perform sensitivity analyses; and verify the evaluated policy matches the artifact you claim to evaluate.
""")
    c1, c2, c3 = st.columns(3)
    with c1: seed = int(st.number_input("Random seed", min_value=0, max_value=2_000_000_000, value=20261017, step=1))
    with c2: n_runs = int(st.number_input("Independent test runs", min_value=10, max_value=200, value=40, step=10))
    with c3: n_per_run = int(st.number_input("Scenarios per run", min_value=25, max_value=2000, value=200, step=25))
    st.subheader("Training protocol")
    a, b, c, d = st.columns(4)
    with a: episodes = int(st.number_input("Training episodes", min_value=100, max_value=10000, value=1500, step=100))
    with b: steps = int(st.number_input("Steps per episode", min_value=5, max_value=100, value=20, step=5))
    with c: alpha = float(st.slider("Learning rate α", 0.01, 1.0, 0.10, 0.01))
    with d: gamma = float(st.slider("Discount γ", 0.0, 0.99, 0.80, 0.01))
    epsilon = float(st.slider("Exploration ε during training", 0.01, 1.0, 0.15, 0.01))
    st.markdown("**Predeclared reward weights** (must be justified and sensitivity-tested)")
    w1, w2, w3, w4 = st.columns(4)
    with w1: wrisk = float(st.number_input("Risk weight (reported; artifact reward uses fixed +10/+20/+30/-5)", min_value=0.0, max_value=1.0, value=0.55, step=0.05))
    with w2: wlat = float(st.number_input("Latency weight", min_value=0.0, max_value=1.0, value=0.15, step=0.05))
    with w3: wserv = float(st.number_input("Service impact weight", min_value=0.0, max_value=1.0, value=0.20, step=0.05))
    with w4: wcost = float(st.number_input("Action cost weight", min_value=0.0, max_value=1.0, value=0.10, step=0.05))
    weights = {"risk": wrisk, "latency": wlat, "service": wserv, "cost": wcost}
    if sum(weights.values()) <= 0:
        st.error("At least one reward weight must be positive.")
        return
    st.caption(f"Reward weights sum to {sum(weights.values()):.2f}; note that the artifact-aligned Q learner uses the original fixed +10/+20/+30/-5 reward table; these weights are retained for sensitivity-report context only.")
    st.subheader("Optional empirical action-effect calibration")
    st.write("Upload a CSV with columns `action,observed_mitigation_fraction`, where action is Monitor/Mitigate/Escalate (or monitor/rate_limit/isolate) and the fraction is an observed, documented mitigation proportion from comparable experiments. Do not upload invented values and label them empirical.")
    calibration_upload = st.file_uploader("Empirical action-effect calibration CSV (optional)", type=["csv"], key="action_calibration_csv")
    calibration_factors = {}
    if calibration_upload is not None:
        try:
            calibration_factors, calibration_table, calibration_note = parse_action_calibration(calibration_upload)
            st.dataframe(calibration_table.round(5), use_container_width=True, hide_index=True)
            st.caption(calibration_note)
        except Exception as exc:
            st.error(f"Calibration file was not applied: {exc}")
            calibration_factors = {}
    if st.button("Train policy and run held-out paired evaluation", type="primary", use_container_width=True):
        with st.spinner("Training Q-learning on training scenarios, freezing the policy, and evaluating on held-out scenarios..."):
            q = train_q_policy(seed + 7_000_001, episodes, steps, weights, alpha, gamma, epsilon)
            detail, wide = evaluate(seed + 19_000_003, n_runs, n_per_run, q, calibration_factors=calibration_factors)
            summary, run_means = summarize_runs(wide)
            config = {"seed": seed, "independent_test_runs": n_runs, "scenarios_per_run": n_per_run,
                      "training_episodes": episodes, "steps_per_episode": steps, "alpha": alpha, "gamma": gamma,
                      "epsilon": epsilon, "reward_weights": weights, "baseline": "fixed-threshold policy",
                      "AO-LACCP policy": "state/action/reward/transition structure aligned to current original artifact MDP",
                      "policy_outcome_bridge": "new, assumed mapping from original actions to common outcome equations",
                      "mdp_transition_model": "original artifact configured state-only transition rows; not calibrated",
                      "sensitivity_analysis": "separate retraining and reevaluation across parameter variants",
                      "empirical_action_calibration_factors": calibration_factors,
                      "calibration_note": "No action-effect calibration applied unless a valid empirical CSV was uploaded"}
            st.session_state["eval_detail"] = detail
            st.session_state["eval_wide"] = wide
            st.session_state["eval_summary"] = summary
            st.session_state["eval_runs"] = run_means
            st.session_state["eval_q"] = q
            st.session_state["eval_config"] = config
    if "eval_summary" not in st.session_state:
        st.info("Set the protocol values, then run the held-out paired evaluation.")
        return
    detail = st.session_state["eval_detail"]
    wide = st.session_state["eval_wide"]
    summary = st.session_state["eval_summary"]
    run_means = st.session_state["eval_runs"]
    q = st.session_state["eval_q"]
    config = st.session_state["eval_config"]
    st.subheader("Learned Q-table — frozen before test evaluation")
    st.dataframe(q.round(4), use_container_width=True)
    st.subheader("Primary statistical summary")
