#!/usr/bin/env bash

privileged_user=ubuntu
GIT=/usr/bin/git

$(which git > /dev/null 2>&1)
FOUND_GIT=$?
if [ "$FOUND_GIT" -ne '0' ]; then
  echo 'Attempting to install git.'
  $(which apt-get > /dev/null 2>&1)
  FOUND_APT=$?

  if [ "${FOUND_APT}" -eq '0' ]; then
    sudo apt-get -q -y update
    sudo apt-get -q -y install git
    echo 'git installed.'
  else
    echo 'No package installer available. You may need to install git manually.'
  fi
else
  echo 'git found.'
fi

for i in /home/${privileged_user}/vaas_git_repo /home/${privileged_user}/vaas_git_repo.git;
do
    sudo mkdir -p $i
    sudo chown ${privileged_user}:${privileged_user} -R $i
done

cd /home/${privileged_user}/vaas_git_repo/
if [ ! -f /home/${privileged_user}/vaas_git_repo.git/HEAD ]; then
    ${GIT} init
    ${GIT} config user.email ${privileged_user}@vaas.vaas
    ${GIT} config user.name ${privileged_user}
    cd /home/${privileged_user}/vaas_git_repo.git
    ${GIT} init --bare
    echo "initial commit" > /home/${privileged_user}/vaas_git_repo/initial_commit
    cd /home/${privileged_user}/vaas_git_repo
    ${GIT} add --all .
    ${GIT} commit -m "initial commit"
    ${GIT} remote add origin file:///home/${privileged_user}/vaas_git_repo.git
    cd /home/${privileged_user}/vaas_git_repo.git
    /usr/bin/find objects -type d -exec chmod 02770 {} \;
    cd /home/${privileged_user}/vaas_git_repo
    ${GIT} push origin master
    ${GIT} branch --set-upstream-to=origin/master master
fi

echo "Git was configured" > /home/${privileged_user}/.git_configure
