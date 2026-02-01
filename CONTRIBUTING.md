# GitHub Workflow & Commands Guide

This guide covers **all essential Git/GitHub commands**, the **standard team workflow**, and **common problem cases**. Follow this to avoid breaking `main` and to keep your work safe.

---

## 1. One-Time Setup (Only Do This Once)

### Clone the repository


git clone <HTTPS_REPO_LINK>


* Downloads the repository to your computer
* **Do NOT clone again** unless something is seriously broken

### Move into the project directory


cd auto_telescope


---

## 2. Understanding Branches (IMPORTANT)

* `main` → **stable production code** (DO NOT code directly here)
* feature branches → where **all your work happens**

Check your current branch:


git status


Switch to a new branch (always do this before coding):


git checkout -b <your-branch-name>


Example:


git checkout -b camera-tracking-fix


---

## 3. Daily Workflow (What You Do Every Time)

### Step 1: Get latest changes from `main`

Instead of `git pull`, we use **fetch + rebase** (cleaner history).


git fetch origin
git rebase origin/main


* `fetch` downloads updates
* `rebase` applies your work on top of the newest `main`

---

### Step 2: Make code changes

Edit files as needed.

---

### Step 3: Stage your changes


git add .


* Stages **all modified files**

Check what’s staged:


git status


---

### Step 4: Commit your changes


git commit -m "Clear, descriptive message"


Good examples:

* `Fix PID overshoot in azimuth control`
* `Add error handling for camera disconnect`

---

### Step 5: Push your branch to GitHub


git push origin <your-branch-name>


Example:


git push origin camera-tracking-fix


This will create a **Pull Request (PR)** link.

---

## 4. Sharing Your Branch & Pull Requests (REQUIRED)

### How others view your branch

When you push your branch:


git push origin <your-branch-name>


* Your branch now exists **on GitHub**
* Teammates can:

  * Check out your branch locally
  * Review your code online
  * Run and test your changes

To check out someone else’s branch:


git fetch origin
git checkout <their-branch-name>


---

### Creating a Pull Request (PR)

After pushing your branch:

1. Open the PR link shown in the terminal **or** go to GitHub → Pull Requests
2. Select:

   * **Base:** `main`
   * **Compare:** your branch
3. Add a **clear description** of:

   * What you changed
   * Why you changed it
4. Assign **at least 2 reviewers**

🚫 **Never merge your own PR without approval**

---

### Receiving review comments

When reviewers leave comments:

* They may request:

  * Bug fixes
  * Code cleanup
  * Logic changes
  * Better naming or documentation

This is **normal and expected** in collaborative coding.

---

### Updating your code after comments (MOST COMMON CASE)

1. Make the requested code changes
2. Stage and commit them:


git add .
git commit -m "Address PR review comments"


3. Push again:


git push origin <your-branch-name>


✅ The Pull Request updates **automatically**
✅ Reviewers will see the new changes

---

### After approval

Once approved:

* Click **Merge Pull Request** on GitHub
* Your branch is merged into `main`
* You may safely delete your branch

---

## 5. Common Scenarios & Fixes

### Case 1: Main was updated while you were working

**You want new changes without losing your work**


git add .
git commit -m "Save work before rebase"
git fetch origin
git rebase origin/main


If conflicts appear:

* Fix files manually
* Then run:


git rebase --continue


---

### Case 2: Merge conflicts during rebase

1. Git will pause and show conflicted files
2. Open files and fix conflict markers:

   
   <<<<<<<
   =======
   >>>>>>>
   
3. After fixing:


git add .
git rebase --continue


---

### Case 3: You committed to the wrong branch


git checkout correct-branch
git cherry-pick <commit-hash>


Then reset the wrong branch if needed.

---

### Case 4: You want to discard ALL local changes

⚠️ **This deletes your work**


git reset --hard origin/main


---

### Case 5: Your branch is behind but has no local changes


git fetch origin
git rebase origin/main


---

## 6. Helpful Commands You Should Know

### Branching & Navigation


git branch                     # List all local branches
git branch -r                  # List remote branches
git checkout <branch>          # Switch branches
git checkout -b <branch>       # Create + switch branch


### Syncing with Main


git fetch origin
git rebase origin/main


### Staging & Committing


git status                     # Check repo status
git add .                      # Stage all changes
git commit -m "message"        # Commit changes


### Pushing & Sharing


git push origin <branch>       # Push your branch
git pull --rebase              # (If explicitly allowed)


### Reviewing Changes


git diff                       # Unstaged changes
git diff --staged              # Staged changes
git log --oneline              # Commit history


### Temporary Saves


git stash                      # Save work temporarily
git stash pop                  # Restore stashed work


---

## 7. Golden Rules (DO NOT BREAK THESE)

✅ Always work on a **feature branch**

❌ Never code directly on `main`

✅ Push early so others can see your work

✅ Respond to review comments with commits

✅ Rebase from `origin/main` frequently

✅ One PR = one focused change

❌ Do NOT force-push unless explicitly told

---

## 8. Typical Collaboration Flow (Summary)

1. Clone repo (once)
2. Create a branch
3. Fetch + rebase from `main`
4. Write code
5. Commit changes
6. Push branch
7. Open Pull Request
8. Receive comments
9. Fix code → commit → push again
10. Get approval → merge

If something seems confusing or risky, **stop and ask**.
That’s how good teams avoid breaking things.
