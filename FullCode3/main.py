ax.tick_params(axis="x", labelrotation=25)
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.download_button(
            "Download sensitivity analysis CSV",
            sensitivity.to_csv(index=False).encode(),
            "ao_laccp_sensitivity_analysis.csv",
            "text/csv",
        )

    st.subheader("Real cryptographic operation and switching benchmark (RSA/ECDSA/Hybrid)")
    st.warning(
        "This separate test performs actual cryptographic signing/verification "
        "and measures suite transitions in a generated event sequence. The "
        "original AO-LACCP dashboard currently exposes a static crypto-model "
        "selector and does not implement or log dynamic switching. This benchmark "
        "therefore measures a test harness, not original-artifact behavior; PQC "
        "is not included."
    )

    if st.button(
        "Run real cryptographic switching benchmark",
        use_container_width=True,
    ):
        with st.spinner(
            "Executing RSA/ECDSA/Hybrid signing and verification operations..."
        ):
            crypto_trace, crypto_summary, crypto_note = (
                benchmark_real_crypto_switching(seed + 404_001, 30)
            )
            st.session_state["crypto_trace"] = crypto_trace
            st.session_state["crypto_summary"] = crypto_summary
            st.session_state["crypto_note"] = crypto_note

    if "crypto_summary" in st.session_state:
        st.dataframe(
            st.session_state["crypto_summary"].round(5),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(st.session_state["crypto_note"])
        crypto_trace = st.session_state["crypto_trace"]
        st.dataframe(
            crypto_trace.round(5),
            use_container_width=True,
            hide_index=True,
        )
        fig, ax = plt.subplots(figsize=(9, 3.5))
        ax.step(
            crypto_trace["event_id"],
            crypto_trace["suite_changed_from_previous_event"].astype(int),
            where="mid",
        )
        ax.set_yticks([0, 1], labels=["No switch", "Switch"])
        ax.set_xlabel("Event number")
        ax.set_title(
            "Observed cryptographic suite changes in the benchmark trace"
        )
        ax.grid(axis="x", alpha=0.25)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.download_button(
            "Download cryptographic operation trace CSV",
            crypto_trace.to_csv(index=False).encode(),
            "ao_laccp_crypto_switch_trace.csv",
            "text/csv",
        )

    st.subheader("Independent run-level results (not a sensitivity analysis)")
    st.dataframe(
        run_means.round(5),
        use_container_width=True,
        hide_index=True,
    )
    st.warning(
        "This run-to-run table measures variability, not parameter sensitivity. "
        "A true sensitivity analysis must rerun the complete evaluation under "
        "predeclared alternative transition probabilities, action-effectiveness "
        "values, scenario distributions, and reward weights."
    )

    st.subheader("Reproducibility record")
    config_json = json.dumps(config, indent=2, sort_keys=True)
    st.code(config_json, language="json")
    st.write(
        "Configuration SHA-256:",
        hashlib.sha256(config_json.encode("utf-8")).hexdigest(),
    )
    st.download_button(
        "Download detailed scenario results CSV",
        detail.to_csv(index=False).encode(),
        "ao_laccp_validation_detailed.csv",
        "text/csv",
    )
    st.download_button(
        "Download paired outcomes CSV",
        wide.to_csv(index=False).encode(),
        "ao_laccp_validation_paired.csv",
        "text/csv",
    )
    st.download_button(
        "Download statistical summary CSV",
        summary.to_csv(index=False).encode(),
        "ao_laccp_validation_statistics.csv",
        "text/csv",
    )
    st.warning(
        "The MDP logic is aligned to the current original code, but its outputs "
        "are not directly linked to the original dashboard metrics. The "
        "action-effect bridge remains assumed; sensitivity results test "
        "robustness to assumptions but do not calibrate them. The crypto "
        "benchmark executes RSA/ECDSA/Hybrid operations in a separate harness; "
        "it does not establish original-artifact switching or PQC agility."
    )


# Run when imported by dashboard.py or launched directly by Streamlit.
main()
