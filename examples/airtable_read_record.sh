#! /bin/bash
source ../.env

#echo $AIRTABLE_PARTICIPANTS

curl https://api.airtable.com/v0/appZI2AenYNrfVqCL/meta/recQXZAAoj8T7bW6d \
 -H "Authorization: Bearer ${AIRTABLE_PARTICIPANTS}"  