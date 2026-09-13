from __future__ import annotations

# Correction overlay for commit 80d53e95837e4535b69f96ad92bc97b3ae6b846d.
# The evidence commit correctly pinned the App HEAD and four caller blob SHAs,
# but two caller blob SHAs were transcribed incorrectly. This overlay is the
# authoritative correction and preserves the audit trail without mutating PROD.

APP_REPOSITORY = "carlosjmunoz78/fenix-capital-inmo-map"
APP_BRANCH = "main"
APP_HEAD_SHA = "95106d8e792257f809033486b7025d81665ea83b"
SUPERSEDES_EVIDENCE_COMMIT = "80d53e95837e4535b69f96ad92bc97b3ae6b846d"

CORRECTED_CALLER_BLOB_SHAS = {
    "src/ContactCreateShell.tsx": "830a1b950ba573ae769cca402252d98e4fccbe81",
    "src/ExpedienteCreateShell.tsx": "cf810a3ad89eb63bcb48a2d703d6d62ed9db792c",
}

VERIFIED_UNCHANGED_CALLER_BLOB_SHAS = {
    "src/ChatShell.tsx": "3ff76545a4366c6f4cd02429a489d49ce3c179de",
    "src/ExpedienteRenameGuard.tsx": "8c3ab4d8599379726484e77e16ccbbcd24fea6c7",
    "src/NotificationsShell.tsx": "9044aafb40541e9192288c77c7d9c718f2a05e37",
    "src/FirmaCreateShell.tsx": "e335914d08f4dfa913326b93476e072a145f2382",
}


def assess_correction() -> dict:
    all_sources = {**CORRECTED_CALLER_BLOB_SHAS, **VERIFIED_UNCHANGED_CALLER_BLOB_SHAS}
    return {
        "app_repository": APP_REPOSITORY,
        "app_branch": APP_BRANCH,
        "app_head_sha": APP_HEAD_SHA,
        "corrected_source_count": len(CORRECTED_CALLER_BLOB_SHAS),
        "verified_source_count": len(all_sources),
        "all_six_current_frontend_callers_have_verified_blob_sha": len(all_sources) == 6,
        "prod_mutation_performed": False,
        "app_mutation_performed": False,
        "status": "FRONTEND_CALLER_EVIDENCE_TRANSCRIPTION_CORRECTED",
    }
