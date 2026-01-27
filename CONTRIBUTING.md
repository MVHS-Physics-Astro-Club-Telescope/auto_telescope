# GitHub Commands

git clone (https link) --> allows you to clone the main branch onto your software, DO NOT CHANGE THE MAIN BRANCH, you only need to clone the repository **once**

cd auto_telescope --> directs to telescope project

git status --> shows whether your on main branch or not

git checkout -b (name) --> creates and switches to a new branch, only do this one time

git pull --> pulls main branch changes from github

git add . --> adds new changes almost like a draft

git commit -m "(message)" --> allows you to commit your changes to your own branch and add a message

git push --> will diplay a new command, paste that in and enter, copy or click on the new link in your browser and then follow through with the pull request (add a description and assign people to look over it, make sure that atleast 2 reviewers look over your code before you merge it into the main branch).

Special Case/FAQs:

If you merged but someone updated and you dont want to lose your code --> First, add and commit your changes, then get the latest made changes with "git rebase origin/main".


