# Architecture Decision: Monolithic vs Split Packages

## The Problem

We have two interconnected but different components:
1. **`coscientist/`**: Core research engine (agents, framework, state management)
2. **`coscientist_interact/`**: UI and resume functionality

### The Tight Coupling Issue

**Critical dependency**: `coscientist_interact` **must** import from `coscientist`:
- Uses `CoscientistState` to load checkpoints (pkl files)
- Uses `CoscientistFramework` to continue research
- Uses `CoscientistStateManager` for state operations
- **If versions drift, pickle incompatibility = data loss**

**Example**:
```python
# coscientist_interact/common.py
from coscientist.global_state import CoscientistState  # Must match version!

state = CoscientistState.load_latest(goal="...")  # Uses pkl format from coscientist
```

**Risk**: If `coscientist` changes the pkl format, old `.pkl` files become incompatible.

---

## Decision: Monolithic Package

### Current Structure

```
open-coscientist-agents/
├── coscientist/              ← Core engine
├── coscientist_interact/     ← UI (depends on coscientist)
└── pyproject.toml            ← Single package
```

### Why This Works

1. **Same version**: Both components ship together
2. **No drift**: Version locked to same release
3. **Import safety**: `coscientist_interact` always gets compatible `coscientist`
4. **Simple install**: `pip install open-coscientist-agents`

### Installation

```bash
# Everything installed together
uv pip install -e .
```

**Includes**:
- `coscientist` (engine)
- `coscientist_interact` (UI)
- All dependencies (LangChain, Streamlit, etc.)

**Entry point**: `coscientist-interact` command available

---

## Alternative: Split Packages (NOT RECOMMENDED)

If we split them:

```
open-coscientist/           ← Core package
open-coscientist-ui/        ← UI package (depends on open-coscientist)
```

### Problems with split

1. **Version drift**:
   ```bash
   pip install open-coscientist==0.1.0
   pip install open-coscientist-ui==0.2.0  # BREAKS!
   ```
   UI expects different pkl format than what engine produces.

2. **Import coupling**:
   ```python
   # In open-coscientist-ui
   from coscientist.global_state import CoscientistState
   # Must EXACTLY match the installed open-coscientist version
   ```

3. **Compatibility matrix nightmare**:
   - Which UI version works with which engine version?
   - How to test all combinations?
   - Users install wrong combinations

4. **Data loss risk**:
   - Engine updates pkl format
   - Old UI can't load new files
   - **Research data becomes unrecoverable**

---

## Why Monolithic Is Right For Us

### Reason 1: Tight Coupling

```
coscientist_interact imports:
- CoscientistState (pkl format!)
- CoscientistFramework (API!)
- CoscientistStateManager (methods!)

ANY change in these breaks resume functionality.
```

### Reason 2: Pickle Version Locking

Python pickle is **version-sensitive**. If `CoscientistState` class changes:
- Old pkl files → New code = `ImportError` or `AttributeError`
- **Data loss**

**Solution**: Ship both together, guarantee compatibility.

### Reason 3: Resume Is Core Feature

"Resume from checkpoint" isn't optional—it's **essential**:
- Research runs for hours
- Can't lose progress
- Must work 100% of the time

If UI and engine drift, resume **breaks catastrophically**.

---

## Optional-Dependencies Approach (Future Consideration)

If we want to make UI optional:

### Option 1: Keep together, mark UI as optional install

```toml
[project]
dependencies = [
    # All core deps including Streamlit (install always)
]
```

```bash
pip install open-coscientist-agents  # Everything
```

**Advantage**: Simplicity, guaranteed compatibility

**Disadvantage**: Users get Streamlit even if they don't use UI

### Option 2: Extras for UI

```toml
[project]
dependencies = [
    # Core deps (NO Streamlit)
]

[project.optional-dependencies]
interact = [
    "streamlit>=1.50.0",
    "st-cytoscape>=0.0.5",
]
```

```bash
pip install open-coscientist-agents          # Core only
pip install open-coscientist-agents[interact]  # With UI
```

**Advantage**: Optional dependencies

**Disadvantage**: Resume functionality in core depends on UI → Still need to keep together

---

## Recommended Approach: Current (Monolithic)

**Keep everything in one package**:

- ✅ **No version drift**
- ✅ **Guaranteed compatibility**
- ✅ **Resume always works**
- ✅ **Simple installation**
- ✅ **No breaking changes**

**Trade-off**: All dependencies installed (but that's fine - it's one package for one purpose)

---

## When to Consider Splitting

**Only if**:

1. **Separate projects**: Different teams, different repos, different release cycles
2. **Different use cases**: Engine has 100 users, UI has 5 users
3. **Different dependencies**: Engine has 5 deps, UI has 50 deps (not our case - similar deps)

**Our case**: 
- Single project
- Same team
- Same release cycle
- Resume is core feature
- **Keep together**

---

## Conclusion

**Current architecture is correct**:
- Monolithic package (everything in `open-coscientist-agents`)
- `coscientist/` and `coscientist_interact/` as subpackages
- Same version, no drift, guaranteed compatibility
- Resume works because pkl format always matches

**Do not split** - the coupling is too tight and the risk is too high.

