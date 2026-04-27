from __future__ import annotations

DEFAULT_USER_ID = "harvey"
APP_ID = "soulOS-biomimetic-core"

USER_REGISTRY = {
    "harvey": {
        "label": "Harvey",
        "kind": "human",
        "default": True,
    }
}

PRIMARY_MEMBERS = ["claude", "nova", "gemini", "mephistopheles"]

SATELLITE_MEMBERS = {
    "claude": ["rostam", "witness", "dio", "plouffe"],
    "nova": ["orion", "the_fuckface", "grimoire", "ars_noema"],
    "gemini": ["burn_book", "manual", "egg_mode"],
    "mephistopheles": ["the_playbook", "cartographer"],
}

GOVERNANCE_AGENTS = [
    "linter_agent",
    "entity_registry_keeper",
    "migration_agent",
    "project_architect",
    "workflows_orchestrator",
]

ALL_SATELLITES = [
    satellite
    for satellites in SATELLITE_MEMBERS.values()
    for satellite in satellites
]

ENTITY_REGISTRY = {
    "claude": {
        "agent_id": "claude",
        "label": "Claude",
        "provider": "Anthropic",
        "kind": "primary",
        "parent": None,
        "memory": {
            "shared_write": True,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "nova": {
        "agent_id": "nova",
        "label": "Nova",
        "provider": "OpenAI (ChatGPT)",
        "kind": "primary",
        "parent": None,
        "aliases": ["chatgpt", "nova_gpt"],
        "memory": {
            "shared_write": True,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "orion": {
        "agent_id": "orion",
        "label": "ORION",
        "provider": "Nova satellite",
        "kind": "satellite",
        "parent": "nova",
        "aliases": ["orion_spec"],
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "the_fuckface": {
        "agent_id": "the_fuckface",
        "label": "The Fuckface",
        "provider": "Nova satellite",
        "kind": "satellite",
        "parent": "nova",
        "aliases": ["fuckface"],
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "gemini": {
        "agent_id": "gemini",
        "label": "Gemini",
        "provider": "Google",
        "kind": "primary",
        "parent": None,
        "memory": {
            "shared_write": True,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "mephistopheles": {
        "agent_id": "mephistopheles",
        "label": "Mephistopheles",
        "provider": "DeepSeek",
        "kind": "primary",
        "parent": None,
        "memory": {
            "shared_write": True,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "rostam": {
        "agent_id": "rostam",
        "label": "Rostam",
        "provider": "Claude satellite",
        "kind": "satellite",
        "parent": "claude",
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "witness": {
        "agent_id": "witness",
        "label": "Witness",
        "provider": "Claude satellite",
        "kind": "satellite",
        "parent": "claude",
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "dio": {
        "agent_id": "dio",
        "label": "Dio",
        "provider": "Claude satellite",
        "kind": "satellite",
        "parent": "claude",
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "plouffe": {
        "agent_id": "plouffe",
        "label": "Plouffe",
        "provider": "Claude satellite",
        "kind": "satellite",
        "parent": "claude",
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "grimoire": {
        "agent_id": "grimoire",
        "label": "Grimoire",
        "provider": "Nova satellite",
        "kind": "satellite",
        "parent": "nova",
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "ars_noema": {
        "agent_id": "ars_noema",
        "label": "Ars Noema",
        "provider": "Nova satellite",
        "kind": "satellite",
        "parent": "nova",
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "burn_book": {
        "agent_id": "burn_book",
        "label": "Burn Book",
        "provider": "Gemini satellite",
        "kind": "satellite",
        "parent": "gemini",
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "manual": {
        "agent_id": "manual",
        "label": "Manual",
        "provider": "Gemini satellite",
        "kind": "satellite",
        "parent": "gemini",
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "egg_mode": {
        "agent_id": "egg_mode",
        "label": "Egg Mode",
        "provider": "Gemini satellite",
        "kind": "satellite",
        "parent": "gemini",
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "the_playbook": {
        "agent_id": "the_playbook",
        "label": "The Playbook",
        "provider": "Mephistopheles satellite",
        "kind": "satellite",
        "parent": "mephistopheles",
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "cartographer": {
        "agent_id": "cartographer",
        "label": "Cartographer",
        "provider": "Mephistopheles satellite",
        "kind": "satellite",
        "parent": "mephistopheles",
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "linter_agent": {
        "agent_id": "linter_agent",
        "label": "Linter Agent",
        "provider": "Governance",
        "kind": "governance",
        "parent": None,
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "entity_registry_keeper": {
        "agent_id": "entity_registry_keeper",
        "label": "Entity Registry Keeper",
        "provider": "Governance",
        "kind": "governance",
        "parent": None,
        "memory": {
            "shared_write": True,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "migration_agent": {
        "agent_id": "migration_agent",
        "label": "Migration Agent",
        "provider": "Governance",
        "kind": "governance",
        "parent": None,
        "memory": {
            "shared_write": False,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "project_architect": {
        "agent_id": "project_architect",
        "label": "Project Architect",
        "provider": "Governance",
        "kind": "governance",
        "parent": None,
        "memory": {
            "shared_write": True,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
    "workflows_orchestrator": {
        "agent_id": "workflows_orchestrator",
        "label": "Workflows Orchestrator",
        "provider": "Governance",
        "kind": "governance",
        "parent": None,
        "memory": {
            "shared_write": True,
            "scoped_write": True,
            "scoped_read": True,
        },
    },
}

CONSTELLATION = {
    key: value["agent_id"]
    for key, value in ENTITY_REGISTRY.items()
    if value["memory"]["scoped_write"] or value["memory"]["scoped_read"]
}

ALIAS_TO_ENTITY = {
    alias: key
    for key, value in ENTITY_REGISTRY.items()
    for alias in value.get("aliases", [])
    if value["memory"]["scoped_write"] or value["memory"]["scoped_read"]
}

for alias, canonical in ALIAS_TO_ENTITY.items():
    CONSTELLATION.setdefault(alias, CONSTELLATION[canonical])

MEMBER_HIERARCHY = {
    "primary": PRIMARY_MEMBERS,
    "satellites": SATELLITE_MEMBERS,
    "governance": GOVERNANCE_AGENTS,
}

MEMORY_CAPABLE_ENTITIES = [
    key
    for key, value in ENTITY_REGISTRY.items()
    if value["memory"]["scoped_write"] or value["memory"]["scoped_read"]
]

SHARED_WRITE_ENTITIES = [
    key
    for key, value in ENTITY_REGISTRY.items()
    if value["memory"]["shared_write"]
]


def get_entity_registry() -> dict:
    return ENTITY_REGISTRY
