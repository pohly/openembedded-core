#!/bin/sh
# Hook to add source component/revision info to commit message
# Parameter:
#   $1 patch-file
#   $2 revision
#   $3 reponame

patchfile=$1
rev=$2
reponame=$3

sed -i -e "0,/^Subject:/s#^Subject: \[PATCH\] \($reponame: \)*\(.*\)#Subject: \[PATCH\] $reponame: \2#" $patchfile
sed -i -e "0,/^Signed-off-by:/s#\(^Signed-off-by:.*\)#\($reponame rev: $rev\)\n\n\1#" $patchfile
