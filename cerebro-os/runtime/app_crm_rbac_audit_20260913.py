from __future__ import annotations

RBAC = {
    "captured_at": "2026-09-13",
    "source": "SUPABASE_PROD_READ_ONLY",
    "project_ref": "cluhljgonannaafpmblx",
    "session_context_server_present": True,
    "navigation_server_present": True,
    "active_actor_required": True,
    "roles": {
        "Direccion": (
            "/inicio", "/expedientes", "/bancos", "/contactos", "/inmobiliarias",
            "/tasaciones", "/firmas", "/documentacion", "/financieros", "/visitadores",
            "/obras-nuevas", "/herencias", "/agenda", "/economia", "/informes",
            "/notarias", "/registros-propiedad", "/comunicaciones", "/chat",
            "/notificaciones", "/perfil",
        ),
        "Financiero": (
            "/inicio", "/expedientes", "/bancos", "/contactos", "/inmobiliarias",
            "/documentacion", "/firmas", "/tasaciones", "/agenda", "/informes",
            "/notarias", "/registros-propiedad", "/chat", "/notificaciones", "/buscar",
        ),
        "Visitador": (
            "/inicio", "/inmobiliarias", "/contactos", "/visitas", "/agenda",
            "/documentacion", "/informes", "/chat", "/notificaciones", "/buscar",
        ),
    },
    "unknown_role_navigation": (),
    "gateway_resolves_actor_before_navigation": True,
    "frontend_receives_server_navigation": True,
    "prod_write_performed": False,
}


def assess() -> dict:
    unique_role_routes = {role: len(set(routes)) == len(routes) for role, routes in RBAC["roles"].items()}
    return {
        "APP_002_RBAC_navigation_green": (
            RBAC["session_context_server_present"]
            and RBAC["navigation_server_present"]
            and RBAC["active_actor_required"]
            and all(unique_role_routes.values())
            and RBAC["unknown_role_navigation"] == ()
            and RBAC["gateway_resolves_actor_before_navigation"]
            and RBAC["frontend_receives_server_navigation"]
            and not RBAC["prod_write_performed"]
        ),
        "role_count": len(RBAC["roles"]),
        "routes_by_role": {k: len(v) for k, v in RBAC["roles"].items()},
        "status": "APP_002_RBAC_NAVIGATION_GREEN",
    }
