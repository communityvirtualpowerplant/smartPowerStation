#! /bin/bash
source ../.env

echo AIRTABLE

# curl -X POST https://api.airtable.com/v0/appZI2AenYNrfVqCL/participants \
#   -H "Authorization: Bearer YOUR_SECRET_API_TOKEN" \
#   -H "Content-Type: application/json" \
#   --data '{
#   "records": [
#     {
#       "fields": {
#         "name": "case",
#         "daily pv wh": "300",
#         "flex wh": "800",
#         "id": "321",
#         "baseline Wh": "50"
#       }
#     },
#     {
#       "fields": {
#         "name": "home",
#         "daily pv wh": "25",
#         "flex wh": "150",
#         "id": "123"
#       }
#     }
#   ]
# }'