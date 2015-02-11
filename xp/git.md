<global>
git config --global user.name "Yang Gu"
git config --global user.email "yang.gu@intel.com"
git config --global color.ui true
git config --global alias.co checkout
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.br branch
git config --global core.autocrlf false
git config --global core.editor vi
</global>

<log>
git log --pretty=short --no-merges |git shortlog -nse  # rank the contribution
git log --follow -- file  # log with deleted file
git log <since>..<until>
git log master..yourbranch --pretty=oneline | wc -l  # commit number
git log --summary 223286b.. | grep "Author:" | wc -l  # Count git commits since specific commit
git format-patch -1 hash  # Generate patch for a specific hash
git log --grep="Something in the message"
</log>

<remote>
git remote -v
git remote show <name>
</remote>

<patch>
git am <patch>

# if problematic with patch
git apply --reject <patch>
git add <all modified files>
git am --resolved

patch -p1 <patch>
</patch>

<stash>
git stash apply
git stash list
git stash apply stash@{1}
git stash clear
</stash>

<misc>
git reset HEAD -- path/to/file  # remove from stage
git branch | grep -v "master" | sed 's/^[ *]*//' | sed 's/^/git branch -D /' | bash  # Remove all branches other than master
</misc>