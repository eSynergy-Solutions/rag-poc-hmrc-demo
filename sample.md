---
openapi: 3.0.3
info:
  title: HIP Board Game Store
  description: Description
  version: 0.1.0
  x-integration-catalogue:
    status: ALPHA
    platform: HIP
    backends:
    - backend_a
    domain: DOMAIN
    api-type: SIMPLE
    reviewed-date: 2025-04-01T08:01:17.850486966Z
    short-description: a description
    sub-domain: SUB_DOMAIN
    API-Generation: V2
servers:
- url: https://api.ipaas.prod.eis.ns2p.corp.hmrc.gov.uk/apim
  description: Corporate - Production
- url: https://api.ipaas.preprod.eis.ns2p.corp.hmrc.gov.uk/apim
  description: Corporate – Pre-Production
- url: https://api.ipaas.test.eis.ns2n.corp.hmrc.gov.uk/apim
  description: Corporate - Test
- url: https://hip.ws.hmrc.gov.uk/apim
  description: MDTP - Production
- url: https://hip.ws.ibt.hmrc.gov.uk/apim
  description: MDTP - QA
paths:
  /v1/route/{boardGameId}:
    delete:
      summary: Deletes a board game
      description: Description
      operationId: deleteBoardGame
      parameters:
      - name: boardGameId
        in: path
        description: Board game id to delete
        required: true
        schema:
          format: int64
          type: integer
        style: simple
        explode: false
      responses:
        "200":
          description: successful operation
        "400":
          description: Invalid boardGameId or boardGameName supplied
          content:
            application/json:
              schema:
                required:
                - origin
                - response
                type: object
                properties:
                  origin:
                    $ref: '#/components/schemas/HIP-originEnum'
                  response:
                    oneOf:
                    - $ref: '#/components/schemas/HIP-failureResponse'
                    - $ref: '#/components/schemas/ErrorResponse'
                additionalProperties: false
              examples:
                invalidParameter:
                  $ref: '#/components/examples/InvalidParameter'
                HIP-originResponse:
                  description: HIP-originResponse
                  value:
                    origin: HIP
                    response:
                    - type: Type of Failure
                      reason: Reason for Failure
        "404":
          description: Board game not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                notFound:
                  $ref: '#/components/examples/NotFound'
        "500":
          description: Internal Server Error
          content:
            application/json;charset=UTF-8:
              schema:
                $ref: '#/components/schemas/HIP-originResponse'
        "503":
          description: Service Unavailable
          content:
            application/json;charset=UTF-8:
              schema:
                $ref: '#/components/schemas/HIP-originResponse'
      security:
      - oAuth2:
        - read:exemplar-route
components:
  schemas:
    Category:
      type: object
      properties:
        id:
          format: int64
          type: integer
          example: 1
        name:
          type: string
          example: Card Games
    Tag:
      type: object
      properties:
        id:
          format: int64
          type: integer
        name:
          type: string
          example: Most Popular
    BoardGame:
      required:
      - category
      - name
      type: object
      properties:
        id:
          format: int64
          type: integer
          example: 10
        name:
          type: string
          example: Exploding Kittens
        category:
          $ref: '#/components/schemas/Category'
        photoUrls:
          type: array
          items:
            type: string
        tags:
          type: array
          items:
            $ref: '#/components/schemas/Tag'
        status:
          description: Board game status in the store
          enum:
          - available
          - pending
          - sold
          type: string
          example: available
      additionalProperties: false
    ErrorResponse:
      description: Schema defining the format of the error response
      type: object
      properties:
        code:
          description: A code identifying the type of error
          type: string
          example: NOT_FOUND
        message:
          description: A summary message indicating what the error is
          type: string
          example: The order does not exist.
    HIP-originEnum:
      enum:
      - HIP
      - HoD
      type: string
    HIP-failureResponse:
      required:
      - failures
      type: object
      properties:
        failures:
          minItems: 1
          uniqueItems: true
          type: array
          items:
            required:
            - type
            - reason
            type: object
            properties:
              type:
                type: string
              reason:
                type: string
            additionalProperties: false
    HIP-originResponse:
      required:
      - origin
      - response
      type: object
      properties:
        origin:
          $ref: '#/components/schemas/HIP-originEnum'
        response:
          $ref: '#/components/schemas/HIP-failureResponse'
      additionalProperties: false
  examples:
    NotFound:
      summary: Example of a 404 Not Found
      value:
        code: NOT_FOUND
        description: The board game does not exist.
    InvalidPayload:
      summary: Example of an invalid payload
      value:
        code: INVALID_PAYLOAD
        description: The payload provided was invalid.
    InvalidParameter:
      summary: Example of an invalid parameter
      value:
        code: INVALID_PARAMETER
        description: One of the parameters provided was invalid.
  securitySchemes:
    oAuth2:
      type: oauth2
      description: OAuth2 Client Credentials Flow
      flows:
        clientCredentials:
          tokenUrl: /tokenUrl/not-required
          scopes:
            read:exemplar-scope: Scope for demo api-name
