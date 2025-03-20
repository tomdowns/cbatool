
# Git Branching Strategy (Improved)  

## Branch Structure  

- **`main`**:  
  - Production-ready code only.  
  - Merges occur from `develop` after full testing and approval.  
  - Protected branch (no direct commits).  

- **`develop`**:  
  - Integration branch for all feature branches.  
  - Must remain stable and pass all tests before merging to `main`.  

- **`feature/*`**:  
  - Used for new features, improvements, or refactors.  
  - Derived from `develop` and merged back into `develop`.  

---

## Branch Naming Convention  

Use clear, descriptive branch names:  
```
feature/<scope>-<descriptive-task>
```
**Examples:**  
- `feature/refactor-app-worker-utils`  
- `feature/ui-component-factory`  
- `feature/config-management-rework`  
- `feature/fix-report-export-edge-cases`  

### For large multi-stage refactors, use milestone suffixes:
- `feature/refactor-app-stage-1-worker-extraction`  
- `feature/refactor-app-stage-2-ui-components`  

---

## Feature Branch Workflow  

### 1. Create Your Branch  
```bash
git checkout develop  
git pull --rebase  
git checkout -b feature/<scope>-<description>  
```  

### 2. Work Incrementally  
- Make small, atomic commits that are logically grouped.  
- Each commit should maintain a working state (or document why if not).  
- Use descriptive commit messages in this format:  
```
<scope>: <short description of change>
```
**Examples:**  
- `worker_utils: extract depth analysis worker`  
- `ui_components: add file selection widget factory`  

### 3. Push and Backup Frequently  
```bash
git push --set-upstream origin feature/<branch-name>
```
- Create draft PRs early for visibility and feedback.  
- Tag stable points in your feature work with:  
```bash
git tag <feature>-checkpoint-<milestone>
git push --tags
```  

---

## Merging Process  

### Feature Branch → Develop  
- Ensure feature is complete and all tests pass.  
- Rebase onto `develop` to avoid merge conflicts:  
```bash
git checkout feature/<branch-name>  
git pull --rebase  
git checkout develop  
git pull  
git merge feature/<branch-name>  
git push  
```  

### Develop → Main  
- Performed only at release milestones or stable states.  
- After full testing and review of `develop`:  
```bash
git checkout main  
git pull  
git merge develop  
git push  
```  

---

## Backups and Safety  

Before starting large refactors or milestone stages:  
1. Confirm `develop` is up to date.  
2. Create a local archive of the repo:  
```bash
zip -r backup-$(date +%Y%m%d)-before-<milestone>.zip .  
```  
3. Tag current develop state:  
```bash
git checkout develop  
git tag safe-point-before-<milestone>  
git push --tags  
```  

---

## Commit Message Guidelines  

- Start with the scope (e.g., `worker_utils`, `ui_components`, `config`).  
- Describe the change in one line.  
- If needed, include a body explaining reasoning, refactoring patterns applied, or changes in design.  

---

## Recommended Git Aliases for Efficiency  

```bash
git config --global alias.co checkout  
git config --global alias.br branch  
git config --global alias.ci commit  
git config --global alias.st status  
git config --global alias.last 'log -1 HEAD'  
git config --global alias.graph 'log --oneline --graph --decorate'  
```

---

### ✅ Would you like me to draft a `.gitlab-ci.yml` or `.github/workflows/main.yml` template to automate checks for feature branches?  
Let me know if you’d like that added!
