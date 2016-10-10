#!/bin/bash

if [ -z "$1" ]
then
   echo "Usage: $0 <role_name>"
   exit
fi


NEW_ROLE="$1"
mkdir -p playbooks/$NEW_ROLE
touch playbooks/$NEW_ROLE/README.md
mkdir playbooks/$NEW_ROLE/defaults
touch playbooks/$NEW_ROLE/defaults/main.yml

mkdir playbooks/$NEW_ROLE/files

mkdir playbooks/$NEW_ROLE/handlers
touch playbooks/$NEW_ROLE/handlers/main.yml

mkdir playbooks/$NEW_ROLE/meta
touch playbooks/$NEW_ROLE/meta/main.yml

mkdir playbooks/$NEW_ROLE/tasks
touch playbooks/$NEW_ROLE/tasks/main.yml

mkdir playbooks/$NEW_ROLE/templates

mkdir playbooks/$NEW_ROLE/vars
touch playbooks/$NEW_ROLE/vars/main.yml
