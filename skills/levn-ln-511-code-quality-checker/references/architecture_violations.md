# Architecture Violations Reference

<!-- SCOPE: Clean Architecture violation patterns ONLY. Contains layer hierarchy, dependency rules, cross-cutting concerns. -->
<!-- DO NOT add here: DRY rules → dry_violations.md, KISS rules → kiss_violations.md, YAGNI rules → yagni_violations.md -->

Clean Architecture principles: Separation of concerns, layer independence, dependency inversion.

## Layer Hierarchy

```
┌─────────────────┐
│  Controllers    │  (HTTP handlers, routes)
│    (routes/)    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│    Services     │  (Business logic)
│  (services/)    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Repositories   │  (Data access)
│ (repositories/) │
└─────────────────┘
```

**Rule:** Only call downward. Controller → Service → Repository.

## Violation Patterns

### 1. Layer Skipping

**Violation:**
```python
# controllers/user_controller.py
from repositories.user_repository import UserRepository  # VIOLATION!

def get_user(user_id):
    user_repo = UserRepository()  # Skips Service layer
    return user_repo.get(user_id)
```

**Fix:**
```python
# controllers/user_controller.py
from services.user_service import UserService

def get_user(user_id):
    user_service = UserService()
    return user_service.get_user(user_id)

# services/user_service.py
from repositories.user_repository import UserRepository

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    def get_user(self, user_id):
        return self.user_repo.get(user_id)
```

**Severity:** HIGH

---

### 2. Circular Dependencies

**Violation:**
```python
# module_a.py
from module_b import function_b

def function_a():
    return function_b()

# module_b.py
from module_a import function_a  # CIRCULAR!

def function_b():
    return function_a()
```

**Detection:**

| Scope | Method | Detects |
|-------|--------|---------|
| Story-level (ln-511) | Parse imports in changed files, check pairwise | A <-> B cycles in touched files |
| Codebase-level (ln-644) | Full dependency graph + DFS | Pairwise, transitive (A->B->C->A), folder-level cycles |

**Fix strategies** (Clean Architecture Ch14):
1. **DIP** — extract interface in depended-upon module, implement in depending module
2. **Extract Shared Component** — move shared code to new module both depend on
3. **Domain Events** — for cross-domain cycles, decouple via async communication

**Severity:** HIGH (pairwise), CRITICAL (transitive)

---

### 3. Business Logic in Wrong Layer

**Violation:**
```python
# controllers/user_controller.py
def create_user(data):
    # Business logic in controller! VIOLATION!
    if not data.get('email') or '@' not in data['email']:
        return {"error": "Invalid email"}

    if len(data.get('password', '')) < 8:
        return {"error": "Password too short"}

    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return {"success": True}
```

**Fix:** Move business logic to Service layer

---

### 4. Dependency Direction (SDP)

Per Clean Architecture Ch14: "Depend in the direction of stability."

**Rule:** A stable module (low Instability) MUST NOT depend on an unstable module (high Instability). Changes to unstable modules would force changes to stable modules, cascading through all their dependents.

| Metric | Formula | Description |
|--------|---------|-------------|
| I (Instability) | Ce / (Ca + Ce) | 0 = stable (many dependents), 1 = unstable (no dependents) |

**Detection:** Full dependency graph via ln-644-dependency-graph-auditor (invoked by ln-640)

**Fix:** Apply DIP — extract interface in the stable module, let the unstable module implement it

**Severity:** HIGH

---

## Detection

```python
def detect_layer_violations(files):
    violations = []

    for file in files:
        # Parse imports
        imports = extract_imports(file)

        # Check layer
        if 'controllers' in file.path or 'routes' in file.path:
            # Controller layer
            for imp in imports:
                if 'repositories' in imp:
                    violations.append({
                        'type': 'Architecture',
                        'severity': 'HIGH',
                        'file': file.path,
                        'description': 'Controller imports Repository (skips Service)',
                        'suggestion': 'Import from services/ instead'
                    })

    return violations
```

---

**Version:** 1.0.0
**Last Updated:** 2025-11-13
