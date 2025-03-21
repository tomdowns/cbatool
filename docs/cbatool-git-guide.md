# CBATool Git Workflow and Best Practices

## Overview

This document provides a comprehensive guide to the Git workflow and best practices used in the CBATool project. It covers branch management, commit guidelines, merging processes, and recommended Git configurations.

## Branch Structure

The CBATool project uses a three-tier branching strategy:

- **`main`**: Production-ready code only. Merges occur from `develop` after full testing and approval. Protected branch (no direct commits).
- **`develop`**: Integration branch for all feature branches. Must remain stable and pass all tests before merging to `main`. 
- **`feature/*`**: Used for new features, improvements, or refactors. Derived from `develop` and merged back into `develop`.

## Branch Naming Convention

Use clear, descriptive branch names following this format:
```
feature/&lt;scope&gt;-&lt;descriptive-task&gt;
```

Examples:
- `feature/refactor-app-worker-utils`
- `feature/ui-component-factory` 
- `feature/config-management-rework`
- `feature/fix-report-export-edge-cases`

For large multi-stage refactors, use milestone suffixes:
- `feature/refactor-app-stage-1-worker-extraction`
- `feature/refactor-app-stage-2-ui-components`

## Feature Branch Workflow

1. **Create Your Branch**
   ```bash
   git checkout develop
   git pull --rebase
   git checkout -b feature/&lt;scope&gt;-&lt;description&gt;
   ```

2. **Work Incrementally**
   - Make small, atomic commits that are logically grouped.
   - Each commit should maintain a working state (or document why if not).
   - Use descriptive commit messages in this format:
     ```
     &lt;scope&gt;: &lt;short description of change&gt;
     ```
     Examples:
     - `worker_utils: extract depth analysis worker`
     - `ui_components: add file selection widget factory`

3. **Push and Backup Frequently**
   ```bash 
   git push --set-upstream origin feature/&lt;branch-name&gt;
   ```
   - Create draft PRs early for visibility and feedback.
   - Tag stable points in your feature work with:
     ```bash
     git tag &lt;feature&gt;-checkpoint-&lt;milestone&gt;
     git push --tags
     ```

## Merging Process

### Feature Branch → Develop
- Ensure feature is complete and all tests pass.
- Rebase onto `develop` to avoid merge conflicts:
  ```bash
  git checkout feature/&lt;branch-name&gt;
  git pull --rebase
  git checkout develop  
  git pull
  git merge feature/&lt;branch-name&gt;
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

## Commit Message Format

```
&lt;type&gt;(&lt;scope&gt;): &lt;short summary&gt;

&lt;detailed description&gt;

Refs #&lt;issue-number&gt;
```

Where:
- **type**: feat, fix, docs, style, refactor, test, chore
- **scope**: analyzer, visualizer, ui, etc.  
- **short summary**: concise description in present tense
- **detailed description**: explains the what and why
- **issue-number**: reference to the associated issue

Example:
```
refactor(analyzer): extract BaseAnalyzer class

Extract common analyzer functionality into an abstract base class
to improve code organization and enable specialized analyzers.

Refs #42
```

## Backups and Safety

Before starting large refactors or milestone stages:

1. Confirm `develop` is up to date.
2. Create a local archive of the repo:
   ```bash
   zip -r backup-$(date +%Y%m%d)-before-&lt;milestone&gt;.zip . 
   ```
3. Tag current develop state:
   ```bash
   git checkout develop
   git tag safe-point-before-&lt;milestone&gt;
   git push --tags
   ```

## Best Practices  

1. **Never Develop Directly on Develop Branch**: Always create a feature branch.
2. **Complete the Cycle**: Always finish one feature by merging it back to develop before starting the next. 
3. **Merge Completed Features Promptly**: Don't let feature branches live too long.
4. **Update Feature Branches Regularly**: Merge develop into feature branches often.
5. **Use Descriptive Branch Names**: Name branches in the format `feature/descriptive-name`.
6. **Write Clear Commit Messages**: Use conventional commit format (e.g., "feat:", "fix:", "docs:").
7. **Create Single-Purpose Branches**: Each branch should represent one logical feature or fix.
8. **Test Before Merging**: Always verify functionality before merging to develop.

## Recommended Git Aliases for Efficiency

```bash
git config --global alias.co checkout
git config --global alias.br branch  
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.last 'log -1 HEAD'
git config --global alias.graph 'log --oneline --graph --decorate'
```

## Common Git Commands Reference

| Purpose | Command | Explanation |
|---------|---------|-------------|
| View status | `git status` | Shows changed files |
| Switch branches | `git checkout branch-name` | Moves to another branch |
| Create new branch | `git checkout -b branch-name` | Creates and switches to new branch |
| Get latest changes | `git pull` | Updates current branch from remote |
| Stage changes | `git add .` | Stages all changes |
| Commit changes | `git commit -m "message"` | Commits staged changes |
| Merge branches | `git merge branch-name` | Brings changes from branch-name into current branch |
| Publish changes | `git push` | Sends commits to remote repository |
| View branch graph | `git log --graph --oneline --all` | Shows branch structure graphically |
| View differences | `git diff` | Shows uncommitted changes |

## Handling Merge Conflicts  

When you encounter merge conflicts:

1. **Understand the conflict**: Look for conflict markers (`&lt;&lt;&lt;&lt;&lt;&lt;&lt;`, `=======`, `&gt;&gt;&gt;&gt;&gt;&gt;&gt;`)
2. **Edit the files**: Manually resolve each conflict  
3. **Stage the resolutions**: `git add [resolved files]`
4. **Complete the merge**: `git commit` (Git will provide a default merge commit message)

Remember, regular communication with team members about active feature branches helps avoid conflicts and integration problems.
