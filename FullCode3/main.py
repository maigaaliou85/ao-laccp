detail.loc[
                detail.policy == "AO-LACCP artifact-aligned Q-learning", selected
            ].dropna().to_numpy(),
        ],
        tick_labels=[
            "Baseline",
            "AO-LACCP artifact-aligned Q-learning",
        ],
        showmeans=True,
    )
    ax.set_ylabel(selected); ax.set_title("Held-out scenario outcome distributions"); ax.grid(axis="y", alpha=.25)
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)
    st.subheader("Hypothesis-testing comparison graphs")
    st.caption("Only quantitative modeled outcomes are plotted here. Cryptographic suite switching is measured separately by executing real RSA/ECDSA operations; it is not inferred from action codes.")
    chart_specs = [
        ("resulting_risk", "Cyber risk comparison", "Risk score (lower is better)"),
        ("simulated_latency_ms", "Response latency comparison", "Simulated latency (ms; lower is better)"),
    ]
    for metric, title, ylabel in chart_specs:
        plot_df = detail.groupby(["run_id", "policy"])[metric].mean().reset_index()
        fig, ax = plt.subplots(figsize=(8, 4))
        data = [plot_df.loc[plot_df.policy == pol, metric].to_numpy(float)
                for pol in ["Baseline", "AO-LACCP artifact-aligned Q-learning"]]
        ax.boxplot(data, tick_labels=["Baseline", "AO-LACCP artifact-aligned Q-learning"], showmeans=True)
        ax.set_title(title + " (independent run means)")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=.25)
        fig.tight_layout(); st.pyplot(fig); plt.close(fig)

    st.subheader("Policy action selection counts (descriptive only)")
    action_counts = detail.groupby(["policy", "selected_action"]).size().rename("Scenario count").reset_index()
    action_counts["Share within policy"] = action_counts["Scenario count"] / action_counts.groupby("policy")["Scenario count"].transform("sum")
    st.dataframe(action_counts, use_container_width=True, hide_index=True)

    st.subheader("Repeated-measures ANOVA results")
    st.write("Because both policies receive the same scenarios, an independent-groups one-way ANOVA would ignore pairing. For two policies, the appropriate repeated-measures ANOVA test is equivalent to the paired t-test on independent run-level means (F = t²).")
    anova_table = paired_repeated_measures_anova(detail)
    st.dataframe(anova_table.round(5), use_container_width=True, hide_index=True)

    st.subheader("Exploratory regression analysis (R²)")
    st.write("This OLS model describes how scenario inputs relate to the paired AO-minus-baseline cyber-risk difference. R² is descriptive, not proof of causality or model validity; coefficients and fit depend on the assumed synthetic outcome model.")
    reg_table, reg_r2 = exploratory_risk_regression(detail, wide)
    rcol1, rcol2 = st.columns([1, 2])
    with rcol1:
        st.metric("Exploratory R²", f"{reg_r2:.4f}" if np.isfinite(reg_r2) else "Unavailable")
    with rcol2:
        st.dataframe(reg_table.round(6), use_container_width=True, hide_index=True)

    st.subheader("Markov decision process (MDP)")
    st.markdown("The tabular Q-learning policy now uses an explicit action-dependent synthetic transition rule. The transition probabilities are assumed for demonstration and must be justified or calibrated before dissertation claims. The crypto-pressure band is modelled as an external condition, not as cryptographic posture.")
    transition_table = mdp_transition_table(transition_mix=1.0)
    st.dataframe(transition_table.round(3), use_container_width=True, hide_index=True)

    st.subheader("Optimal policy derived from the learned Q-table")
    optimal = q.copy()
    optimal["Optimal action"] = [str(q.loc[idx].idxmax()) for idx in q.index]
    optimal["Best estimated Q-value"] = [float(q.loc[idx].max()) for idx in q.index]
    st.dataframe(optimal.round(4), use_container_width=True)
    st.caption("The optimal action is optimal only relative to this declared synthetic MDP, reward function, and training setup; it is not established as globally optimal for real financial systems.")

    st.subheader("Policy-to-artifact alignment audit")
    st.markdown("The current original framework code uses three states (Low/Medium/High), three actions (Monitor/Mitigate/Escalate), transition rows Low=[0.70, 0.25, 0.05], Medium=[0.30, 0.50, 0.20], High=[0.10, 0.40, 0.50], and rewards +10/+20/+30 for the matching state/action, otherwise -5. The evaluation reproduces that MDP structure. These transitions are sourced from the code, not empirically calibrated. The original artifact does not connect these actions to separately generated risk/latency/agility values. This app adds an explicit action-to-outcome bridge; therefore the outcome comparison is not a direct validation of the original dashboard's metric generation. Upload comparable observed mitigation data to calibrate action-effect multipliers; absent such data, values remain assumptions.")
    st.dataframe(mdp_transition_table(1.0), use_container_width=True, hide_index=True)

    st.subheader("Genuine sensitivity analysis: retrain and rerun")
    st.caption("Each row retrains the Q policy and reruns the paired held-out evaluation under a different transition or outcome-model assumption. These are stress tests, not empirical calibration.")
    if st.button("Run sensitivity analysis (7 complete reruns)", use_container_width=True):
        with st.spinner("Retraining and reevaluating all sensitivity conditions..."):
            sens = run_sensitivity_analysis(seed + 303_001, episodes, steps, weights, alpha, gamma, epsilon,
                                            min(n_runs, 20), min(n_per_run, 150), calibration_factors)
            st.session_state["eval_sensitivity"] = sens
    if "eval_sensitivity" in st.session_state:
        sens = st.session_state["eval_sensitivity"]
        st.dataframe(sens.round(5), use_container_width=True, hide_index=True)
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.bar(sens["Sensitivity condition"], sens["Mean paired risk difference (AO - baseline)"])
        ax.axhline(0, linestyle="--", linewidth=1)
        ax.set_ylabel("Mean paired risk difference (AO - baseline)")
        ax.set_title("Sensitivity of risk comparison to assumed parameters")
        ax.tick_params(axis="x", labelrotation=25); ax.grid(axis="y", alpha=.25); fig.tight_layout()
        st.pyplot(fig); plt.close(fig)
        st.download_button("Download sensitivity analysis CSV", sens.to_csv(index=False).encode(),
                            "ao_laccp_sensitivity_analysis.csv", "text/csv")

    st.subheader("Real cryptographic operation and switching benchmark (RSA/ECDSA/Hybrid)")
    st.warning("This separate test performs actual cryptographic signing/verification and measures suite transitions in a generated event sequence. The original AO-LACCP dashboard currently exposes a static crypto-model selector and does not implement or log dynamic switching. This benchmark therefore measures a test harness, not original-artifact behavior; PQC is not included.")
    if st.button("Run real cryptographic switching benchmark", use_container_width=True):
        with st.spinner("Executing RSA/ECDSA/Hybrid signing and verification operations..."):
            crypto_trace, crypto_summary, crypto_note = benchmark_real_crypto_switching(seed + 404_001, 30)
            st.session_state["crypto_trace"] = crypto_trace
            st.session_state["crypto_summary"] = crypto_summary
            st.session_state["crypto_note"] = crypto_note
    if "crypto_summary" in st.session_state:
        st.dataframe(st.session_state["crypto_summary"].round(5), use_container_width=True, hide_index=True)
        st.caption(st.session_state["crypto_note"])
        crypto_trace = st.session_state["crypto_trace"]
        st.dataframe(crypto_trace.round(5), use_container_width=True, hide_index=True)
        fig, ax = plt.subplots(figsize=(9, 3.5))
        ax.step(crypto_trace["event_id"], crypto_trace["suite_changed_from_previous_event"].astype(int), where="mid")
        ax.set_yticks([0, 1], labels=["No switch", "Switch"])
        ax.set_xlabel("Event number"); ax.set_title("Observed cryptographic suite changes in the benchmark trace")
        ax.grid(axis="x", alpha=.25); fig.tight_layout(); st.pyplot(fig); plt.close(fig)
        st.download_button("Download cryptographic operation trace CSV",
                            st.session_state["crypto_trace"].to_csv(index=False).encode(),
                            "ao_laccp_crypto_switch_trace.csv", "text/csv")

    st.subheader("Independent run-level results (not a sensitivity analysis)")
    st.dataframe(run_means.round(5), use_container_width=True, hide_index=True)
    st.warning("This run-to-run table measures variability, not parameter sensitivity. A true sensitivity analysis must rerun the complete evaluation under predeclared alternative transition probabilities, action-effectiveness values, scenario distributions, and reward weights.")
    st.subheader("Reproducibility record")
    config_json = json.dumps(config, indent=2, sort_keys=True)
    st.code(config_json, language="json")
    st.write("Configuration SHA-256:", hashlib.sha256(config_json.encode("utf-8")).hexdigest())
    st.download_button("Download detailed scenario results CSV", detail.to_csv(index=False).encode(), "ao_laccp_validation_detailed.csv", "text/csv")
    st.download_button("Download paired outcomes CSV", wide.to_csv(index=False).encode(), "ao_laccp_validation_paired.csv", "text/csv")
    st.download_button("Download statistical summary CSV", summary.to_csv(index=False).encode(), "ao_laccp_validation_statistics.csv", "text/csv")
    st.warning("The MDP logic is aligned to the current original code, but its outputs are not directly linked to the original dashboard metrics. The action-effect bridge remains assumed; sensitivity results test robustness to assumptions but do not calibrate them. The crypto benchmark executes RSA/ECDSA/Hybrid operations in a separate harness; it does not establish original-artifact switching or PQC agility.")

#if __name__ == "__main__":
#    main()
# Execute the Streamlit application
main()
