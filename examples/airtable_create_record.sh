#! /bin/bash
source ../.env

#echo $AIRTABLE_PARTICIPANTS

curl -X POST https://api.airtable.com/v0/appZI2AenYNrfVqCL/live \
  -H "Authorization: Bearer ${AIRTABLE_PARTICIPANTS}" \
  -H "Content-Type: application/json" \
  --data '{
  "records": [
    {
      "fields": {
        "name": "home",
        "daily pv wh": "25",
        "flex wh": "150",
        "id": "123"
      }
    }
  ]
}'
