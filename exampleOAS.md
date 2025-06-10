openapi: 3.0.0
info:
title: Sample API
description: Optional multiline or single-line description in [CommonMark](http://commonmark.org/help/) or HTML.
version: 0.1.9

servers:

- url: http://api.example.com/v1
  description: Optional server description, e.g. Main (production) server
- url: http://staging-api.example.com
  description: Optional server description, e.g. Internal staging server for testing

paths:
/users:
get:
summary: Returns a list of users.
description: Optional extended description in CommonMark or HTML.
responses:
"200": # status code
description: A JSON array of user names
content:
application/json:
schema:
type: array
item:
type: string

<!-- The 'domain' and 'sub-domain' fields are mandatory within the info section and are currently missing.
In the paths section, the 'item' property should be corrected to 'items' for the array schema. -->

openapi: 3.0.0
info:
title: HMRC Authorisation Requests API
version: 1.0.0
description: API for handling authorisation requests for agents.

paths:
/agents/{arn}/invitations:
get:
summary: Get all authorisation requests for the last 30 days
parameters: - in: path
name: arn
required: true
schema:
type: string
description: Agent Reference Number - in: header
name: Accept
required: true
schema:
type: string
example: application/vnd.hmrc.1.0+json
description: Accept header must be 'application/vnd.hmrc.1.0+json'
responses:
'200':
description: Returns a list of authorisation requests
content:
application/vnd.hmrc.1.0+json:
schema:
type: array
items:
type: object
properties: # Define the properties of an authorisation request here
id:
type: string
status:
type: string
date:
type: string
format: date
'204':
description: No authorisation requests in the last 30 days
'400':
description: Bad Request
'401':
description: Unauthorized
'403':
description: Forbidden
'406':
description: Not Acceptable
'500':
description: Internal Server Error

    post:
      summary: Create a new authorisation request
      parameters:
        - in: path
          name: arn
          required: true
          schema:
            type: string
          description: Agent Reference Number
        - in: header
          name: Accept
          required: true
          schema:
            type: string
            example: application/vnd.hmrc.1.0+json
          description: Accept header must be 'application/vnd.hmrc.1.0+json'
        - in: header
          name: Content-Type
          required: true
          schema:
            type: string
            example: application/json
          description: Content-Type header must be 'application/json'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              # Define the structure of the request body here (for example, MTD-IT or VAT-specific data)
              properties:
                service:
                  type: string
                  description: The service type (e.g., MTD-IT or VAT)
                # Include additional fields here based on your actual request body requirements
      responses:
        '204':
          description: Request accepted and created
        '400':
          description: Bad Request
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '406':
          description: Not Acceptable
        '500':
          description: Internal Server Error

1. remove the analyse oas button; make it on the change event
2. If it cant find anything, hide the right hand side
3. If it finds something, render the screen

OAS validator page
next to continue, validate button; black textarea is where you'll paste your OAS spec
