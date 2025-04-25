#! /bin/bash
source ../.env

curl -X POST https://api.airtable.com/v0/appZI2AenYNrfVqCL/participants \
  -H "Authorization: $AIRTABLE" \
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