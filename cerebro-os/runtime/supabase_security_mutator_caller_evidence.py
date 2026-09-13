from __future__ import annotations

# Conservative caller/wrapper evidence for the 15 authenticated SECURITY DEFINER mutators.
# Evidence-only: no RPC execution, grants/RLS changes, PROD mutation, or retirement.

MUTATORS = {
    "fenix_prod_chat_attachment_add_user": {"family": "chat", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_chat_attachment_add_v2_user": {"family": "chat", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_chat_conversation_create_user": {"family": "chat", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_chat_group_create_user": {"family": "chat", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_chat_send_user": {"family": "chat", "wrapper_evidence": "SERVER_WRAPPER_OBSERVED", "caller_evidence": "PARTIAL"},
    "fenix_prod_chat_send_v2_user": {"family": "chat", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_contact_create": {"family": "contacts", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_contact_create_v2": {"family": "contacts", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_exp_create": {"family": "expediente_followup", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_exp_update": {"family": "expediente_followup", "wrapper_evidence": "SERVER_WRAPPER_OBSERVED", "caller_evidence": "PARTIAL"},
    "fenix_prod_inmo_followup_update_v1": {"family": "expediente_followup", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_notification_mark_user": {"family": "notifications", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_profile_socials_update_user": {"family": "profile", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_profile_update_user": {"family": "profile", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_sign_create": {"family": "signature", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING", "human_gate": "SIGNATURE_REQUIRED"},
}

EDGE_SURFACE_EVIDENCE = {
    "fenix-app-gateway": {"version": 16, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True},
    "fenix-profile-api": {"version": 1, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True},
    "fenix-directory-actions": {"version": 8, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True},
    "fenix-special-cases-api": {"version": 9, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True, "sensitive_confirmation_explicitly_gated": True},
    "fenix-communications-gateway": {"version": 8, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True},
    "fenix-evidence-api": {"version": 13, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True},
    "fenix-expediente-stage": {"version": 8, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True},
    "fenix-b2b-actions": {"version": 9, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": False, "alternative_scoped_backend_observed": True, "source_read_only_inspected": True},
    "fenix-task-api": {"version": 12, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True},
    "fenix-bank-api": {"version": 8, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True},
    "fenix-user-admin": {"version": 2, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True, "admin_actor_allowlist_observed": True},
    "fenix-ana-api": {"version": 10, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True, "human_learning_gate_observed": True},
    "fenix-expediente-people": {"version": 2, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True},
    "fenix-economia-api": {"version": 8, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True, "read_only_surface_observed": True},
    "fenix-document-actions": {"version": 9, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True, "expected_version_guard_observed": True},
    "fenix-reports-api": {"version": 8, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True, "read_only_surface_observed": True},
    "fenix-ana-canonical": {"version": 9, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": False, "alternative_scoped_backend_observed": True, "source_read_only_inspected": True, "read_only_surface_observed": True, "canonical_only_observed": True, "test_rows_excluded_observed": True},
    "fenix-ana-knowledge": {"version": 9, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": False, "alternative_scoped_backend_observed": True, "source_read_only_inspected": True, "human_learning_gate_observed": True, "authority_gate_observed": True},
    "fenix-memory-api": {"version": 9, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": False, "alternative_scoped_backend_observed": True, "source_read_only_inspected": True, "idempotency_guard_observed": True, "scope_validation_observed": True},
    "fenix-directory-api": {"version": 9, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True, "read_only_surface_observed": True},
    "fenix-document-intelligence": {"version": 12, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True, "low_confidence_human_gate_observed": True, "policy_conflict_human_gate_observed": True, "explicit_overwrite_confirmation_observed": True, "scoped_direct_table_write_observed": True},
    "fenix-whatsapp-webhook": {"version": 4, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": False, "alternative_scoped_backend_observed": True, "source_read_only_inspected": True, "hmac_signature_verification_observed": True, "event_write_observed": False},
    "fenix-web-lead": {"version": 3, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True, "origin_allowlist_observed": True, "payload_size_limit_observed": True, "idempotency_guard_observed": True},
    "social-lead-ingest": {"version": 5, "environment": "PROD", "direct_15_mutator_name_reference_observed": False, "server_rpc_routing_observed": True, "source_read_only_inspected": True, "credential_verification_observed": True, "idempotency_guard_observed": True},
}


def assess_mutator_caller_evidence() -> dict:
    wrapper_observed = tuple(name for name, row in MUTATORS.items() if row["wrapper_evidence"] == "SERVER_WRAPPER_OBSERVED")
    exact_caller_green = tuple(name for name, row in MUTATORS.items() if row["caller_evidence"] == "GREEN")
    pending = tuple(name for name in MUTATORS if name not in exact_caller_green)
    inspected_edges = tuple(name for name, row in EDGE_SURFACE_EVIDENCE.items() if row["source_read_only_inspected"])
    inspected_direct_mutator_absence_proven = all(row["source_read_only_inspected"] and not row["direct_15_mutator_name_reference_observed"] for row in EDGE_SURFACE_EVIDENCE.values())
    server_or_scoped_backend_proven = all(row.get("server_rpc_routing_observed", False) or row.get("alternative_scoped_backend_observed", False) for row in EDGE_SURFACE_EVIDENCE.values())
    return {
        "mutator_count": len(MUTATORS),
        "wrapper_observed_count": len(wrapper_observed),
        "wrapper_observed": wrapper_observed,
        "exact_caller_green_count": len(exact_caller_green),
        "pending_exact_caller_evidence": pending,
        "all_exact_callers_proven": not pending,
        "inspected_edge_surface_count": len(inspected_edges),
        "inspected_edge_surfaces": inspected_edges,
        "inspected_edge_direct_mutator_absence_proven": inspected_direct_mutator_absence_proven,
        "inspected_edge_server_or_scoped_backend_proven": server_or_scoped_backend_proven,
        "special_cases_sensitive_confirmation_gated": EDGE_SURFACE_EVIDENCE["fenix-special-cases-api"]["sensitive_confirmation_explicitly_gated"],
        "user_admin_allowlist_observed": EDGE_SURFACE_EVIDENCE["fenix-user-admin"]["admin_actor_allowlist_observed"],
        "ana_human_learning_gate_observed": EDGE_SURFACE_EVIDENCE["fenix-ana-api"]["human_learning_gate_observed"] and EDGE_SURFACE_EVIDENCE["fenix-ana-knowledge"]["human_learning_gate_observed"],
        "ana_authority_gate_observed": EDGE_SURFACE_EVIDENCE["fenix-ana-knowledge"]["authority_gate_observed"],
        "ana_canonical_read_only_observed": EDGE_SURFACE_EVIDENCE["fenix-ana-canonical"]["read_only_surface_observed"],
        "document_expected_version_guard_observed": EDGE_SURFACE_EVIDENCE["fenix-document-actions"]["expected_version_guard_observed"],
        "memory_idempotency_and_scope_guards_observed": EDGE_SURFACE_EVIDENCE["fenix-memory-api"]["idempotency_guard_observed"] and EDGE_SURFACE_EVIDENCE["fenix-memory-api"]["scope_validation_observed"],
        "document_intelligence_human_gates_observed": EDGE_SURFACE_EVIDENCE["fenix-document-intelligence"]["low_confidence_human_gate_observed"] and EDGE_SURFACE_EVIDENCE["fenix-document-intelligence"]["policy_conflict_human_gate_observed"],
        "document_intelligence_overwrite_confirmation_observed": EDGE_SURFACE_EVIDENCE["fenix-document-intelligence"]["explicit_overwrite_confirmation_observed"],
        "whatsapp_signature_verification_observed": EDGE_SURFACE_EVIDENCE["fenix-whatsapp-webhook"]["hmac_signature_verification_observed"],
        "web_lead_ingest_guards_observed": EDGE_SURFACE_EVIDENCE["fenix-web-lead"]["origin_allowlist_observed"] and EDGE_SURFACE_EVIDENCE["fenix-web-lead"]["payload_size_limit_observed"] and EDGE_SURFACE_EVIDENCE["fenix-web-lead"]["idempotency_guard_observed"],
        "social_lead_ingest_guards_observed": EDGE_SURFACE_EVIDENCE["social-lead-ingest"]["credential_verification_observed"] and EDGE_SURFACE_EVIDENCE["social-lead-ingest"]["idempotency_guard_observed"],
        "frontend_or_other_direct_callers_still_pending": True,
        "security_remediation_allowed": False,
        "automatic_prod_mutation_allowed": False,
        "automatic_grant_or_rls_change_allowed": False,
        "automatic_retirement_allowed": False,
        "signature_human_gate": "SIGNATURE_REQUIRED",
        "status": "TWENTY_FOUR_PROD_EDGE_SURFACES_CLEARED_OTHER_CALLERS_PENDING" if inspected_direct_mutator_absence_proven and server_or_scoped_backend_proven else "CALLER_EVIDENCE_PARTIAL_WRAPPERS_OBSERVED",
    }
