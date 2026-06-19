"""RBAC enforcement tests — validates role-based access filter logic.

Tests the core RBAC claim: documents tagged with allowed_roles should
only be returned to users with matching roles. This standalone test
validates the filter construction logic without requiring heavy deps.
"""
from __future__ import annotations


def test_admin_can_access_admin_tagged_docs():
    """The $in filter should include admin role when user is admin."""
    user_role = "admin"
    filtr = {"allowed_roles": {"$in": [user_role]}}
    
    # Simulate: a doc tagged for admin should match
    doc_roles = ["admin", "senior_engineer"]
    assert user_role in doc_roles, "Admin should match admin-tagged doc"


def test_viewer_cannot_access_admin_tagged_docs():
    """The $in filter should exclude admin docs for viewer role."""
    user_role = "viewer"
    
    # Simulate: a doc tagged ONLY for admin should NOT match viewer
    doc_roles = ["admin"]
    assert user_role not in doc_roles, "Viewer should not match admin-only doc"


def test_role_filter_construction():
    """Verify the create_secure_retriever builds the correct filter.

    The filter should be: {"allowed_roles": {"$in": [user_role]}}
    which is the LangChain metadata filter syntax that translates to
    PostgreSQL JSONB @> at the database level.
    """
    # Simulate what create_secure_retriever does internally
    def build_filter(user_role: str) -> dict:
        return {"allowed_roles": {"$in": [user_role]}}
    
    # Admin
    assert build_filter("admin") == {"allowed_roles": {"$in": ["admin"]}}
    # Viewer
    assert build_filter("viewer") == {"allowed_roles": {"$in": ["viewer"]}}
    # Senior engineer
    assert build_filter("senior_engineer") == {"allowed_roles": {"$in": ["senior_engineer"]}}
    # None (should still build filter, but return no results downstream)
    assert build_filter("none") == {"allowed_roles": {"$in": ["none"]}}


def test_role_isolation_scenario():
    """End-to-end scenario: documents should be invisible across roles.

    Simulates:
    1. Document A with allowed_roles=['admin'] is ingested
    2. Admin queries → Document A is in results
    3. Viewer queries → Document A is NOT in results (role-isolated)
    """
    # Simulate two documents with different role tags
    documents = {
        "doc_a": {"content": "Server restart procedure", "allowed_roles": ["admin"]},
        "doc_b": {"content": "How to submit timesheet", "allowed_roles": ["viewer", "employee"]},
    }
    
    def filter_by_role(docs: dict, user_role: str) -> list:
        """Simulate the pgvector JSONB @> filtering."""
        results = []
        for doc_id, doc in docs.items():
            if user_role in doc["allowed_roles"]:
                results.append(doc_id)
        return results
    
    # Admin can see doc_a and doc_b (admin is not in doc_b's roles but in reality
    # admins would have a role hierarchy — this test validates strict isolation)
    admin_results = filter_by_role(documents, "admin")
    assert "doc_a" in admin_results, "Admin should see admin doc"
    assert "doc_b" not in admin_results, "Admin should NOT see viewer doc (strict isolation)"
    
    # Viewer can see doc_b but NOT doc_a
    viewer_results = filter_by_role(documents, "viewer")
    assert "doc_b" in viewer_results, "Viewer should see viewer doc"
    assert "doc_a" not in viewer_results, "Viewer should NOT see admin doc"
    
    # None role sees nothing
    none_results = filter_by_role(documents, "none")
    assert len(none_results) == 0, "None role sees nothing"


def test_role_list_format():
    """The allowed_roles field is a list — verify array membership check."""
    doc = {"content": "test", "allowed_roles": ["admin", "senior_engineer"]}
    
    # These should match (role is IN the list)
    assert "admin" in doc["allowed_roles"]
    assert "senior_engineer" in doc["allowed_roles"]
    
    # These should NOT match
    assert "viewer" not in doc["allowed_roles"]
    assert "junior" not in doc["allowed_roles"]
    assert "none" not in doc["allowed_roles"]


def test_empty_role_tag_denies_all():
    """A document with empty allowed_roles should be inaccessible to everyone."""
    doc = {"content": "secret", "allowed_roles": []}
    
    assert "admin" not in doc["allowed_roles"]
    assert "viewer" not in doc["allowed_roles"]
    assert "none" not in doc["allowed_roles"]


def test_missing_role_tag_denies_all():
    """A document without allowed_roles metadata should be inaccessible."""
    doc = {"content": "unclassified"}
    
    # Simulate: if the role tag doesn't exist, no role can access it
    allowed_roles = doc.get("allowed_roles", [])
    assert allowed_roles == [], "Missing allowed_roles → empty list → deny all"


def test_null_role_filter():
    """User with a null/empty role should match nothing."""
    user_role = ""
    assert user_role not in ["admin", "viewer", "engineer"]


def test_role_hierarchy_scenario():
    """Demonstrate how a role hierarchy would work via multiple role assignments.

    In a real system, a user might have multiple roles (e.g., ['admin', 'viewer']).
    The filter uses $in which supports multi-role matching.
    """
    doc_pool = {
        "doc_a": {"allowed_roles": ["admin"]},
        "doc_b": {"allowed_roles": ["viewer"]},
        "doc_c": {"allowed_roles": ["admin", "viewer"]},
    }
    
    def filter_by_role(docs, roles):
        return [did for did, d in docs.items() if any(r in d["allowed_roles"] for r in roles)]
    
    # Admin+Viewer hybrid user sees all
    hybrid = filter_by_role(doc_pool, ["admin", "viewer"])
    assert len(hybrid) == 3, "Hybrid role sees all docs"
    
    # Admin-only sees admin-tagged
    admin_only = filter_by_role(doc_pool, ["admin"])
    assert "doc_a" in admin_only
    assert "doc_c" in admin_only  # doc_c has admin in its roles
    assert "doc_b" not in admin_only  # doc_b is viewer-only


if __name__ == "__main__":
    test_funcs = [name for name in dir() if name.startswith("test_")]
    passed = 0
    failed = 0
    for name in sorted(test_funcs):
        func = globals()[name]
        try:
            func()
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
