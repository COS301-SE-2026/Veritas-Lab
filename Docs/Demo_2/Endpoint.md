# API Endpoints

## Authorization endpoints

### EP1: Register

**Endpoint:** `POST /api/register`

#### Request Headers

- `Content-Type: application/json`

#### Request Body

```json
{
  "username": "example_username",
  "password": "ExampleP@assword123",
  "email": "example@email.com"
}
```

#### Request Body Requirements

- The username must be unique.
- The password must meet the following requirements:
  - Must be at least 8 characters long.
  - Must include at least one uppercase character: `A-Z`.
  - Must include at least one digit: `0-9`.
  - Must include at least one lowercase character: `a-z`.
  - Must include at least one special character, for example: `!`, `@`, `#`.
- The email must be unique and meet the following requirements:
  - At least one of the following characters in any order: `0-9`, `A-Z`, `a-z`, `_`, `.`, `+`, or `-`.
  - An `@` character follows the requirement above.
  - At least one of the following characters in any order: `0-9`, `a-z`, `A-Z`, `.`, or `-`.
  - A `.` follows the requirement above.
  - At least two of the following characters in any order: `A-Z` or `a-z`.

#### Success Response

**Status Code:** `201`

```json
{
  "status": "success",
  "message": "Account created successfully"
}
```

#### Example Error Response

**Status Code:** `400`

```json
{
  "status": "error",
  "message": "Invalid or missing username"
}
```

#### Possible Error Response Codes

- `400` - Returned when there are invalid or missing fields in the request body.
- `409` - Returned when the email or username in the request body is not unique.
- `422` - Validation Error 

---

### EP2: Login

**Endpoint:** `POST /api/login`

#### Request Headers

- `Content-Type: application/json`

#### Request Body

```json
{
  "username": "example_username",
  "password": "ExampleP@assword123"
}
```

#### Request Body Requirements

- The password must meet the following requirements:
  - Must be at least 8 characters long.
  - Must include at least one uppercase character: `A-Z`.
  - Must include at least one digit: `0-9`.
  - Must include at least one lowercase character: `a-z`.
  - Must include at least one special character, for example: `!`, `@`, `#`.

#### Success Response

**Status Code:** `200`

```json
{
  "status": "success",
  "token": "Example_token_here"
}
```

#### Example Error Response

**Status Code:** `401`

```json
{
  "status": "error",
  "message": "Invalid or missing username"
}
```

#### Possible Error Response Codes

- `400` - Returned when the password or email in the request body does not meet requirements.
- `401` - Returned when the password is incorrect.
- `404` - Returned when the user does not exist.
- `409` - Returned when the email or username in the request body is not unique.
-  `422` - Validation Error  

----
### EP3: Fetch Users
Endpoint: Post /api/fetchUsers

#### Request Headers
	No parameters

#### Request Body

	No parameters


#### Success Response
status code: 200
application/json
```json
{
	"status": "success",
	"users": user[]
}
```
users would have a list of all the users and appropriate details
#### Example Error Response
application/json
status code: 403

```json
{
	"status":"error",
	"message": "User unauthorized"
}
```
#### Possible Error Response Codes

- 401- Returned when JWT is invalid
- 500 - Returned when an Unknown server error occurs
----
### EP4: Change a user's role
Endpoint: POST /api/changeUserRole

#### Request Headers
	No parameters

#### Request Body
json:
```json
{
  "userId": "string",
  "NewRole": "string"
}
```

#### Success Response
status code: 200
application/json
```json
{
"status": "success",
"message": "User role updated to {new_role} successfully"
}
```
{new_role} is the new role of the individual
#### Example Error Response
application/json
status code: 403

```json
{
	"status": "error",
	"message": "User unauthorized"
}
```
#### Possible Error Response Codes

- 400 - When a Bad request is sent to the endpoint
- 401- Returned when JWT is 
- 403 -When the admin tries to change their own role or the user does not have authorization to use this endpoint
- 404 - When the user is not found
- 500 - Returned when an Unknown server error occurs or database error
  
----
### EP5: Delete User
Endpoint: DELETE /api/users/{user_id}

#### Request Headers
	user_id : string 
	This is the user's uuid

#### Request Body
	No requesst Body
#### Success Response
status code: 200
application/json
```json
{
  "status": "success",
  "message": "User deleted successfully."
}
```

#### Example Error Response
application/json
status code: 403

```json
{
	"status": "error",
	"message": "User unauthorized"
}
```
#### Possible Error Response Codes

- 400 - When a Bad request is sent to the endpoint or when the Admin tries to delete themselves
- 401- Returned when JWT is 
- 403 -  the user does not have authorization to use this endpoint
- 404 - When the user is not found
- 500 - Returned when an Unknown server error occurs or database error

----
### EP6: Refresh token
Endpoint: /api/refreshToken

#### Request Headers
	 No paramters

#### Request Body
	No requesst Body
#### Success Response
status code: 200
application/json
```json
{
"status": "success",
"message": "Token does not need refreshing"
}
```
or
```json
{
"status": "success",
"message": "Token refreshed"
}
```
#### Example Error Response
application/json
status code: 401

```json
{
	"status": "error",
	"message": "Token missing required fields"
}
```
#### Possible Error Response Codes

- 401- When the user is not authenticated
- 500 - Returned when an Unknown server error occurs or database error

---

## Cases
### EP7: Create Case

**Endpoint:** `POST /api/createCase`

#### Request Headers

- `Content-Type: application/json`
- `Authorization: Bearer <token_here>`

#### Request Body

```json
{
  "title": "Example title here",
  "description": "Example description of the case here."
}
```

#### Request Body Requirements

- The title cannot be blank or missing.

#### Success Response

**Status Code:** `201`

```json
{
  "status": "success",
  "CaseId": "Example_case_id_here"
}
```

#### Example Error Response

**Status Code:** `403`

```json
{
  "status": "error",
  "message": "User unauthorized"
}
```

#### Possible Error Response Codes

- `400` - Returned when the request body does not meet the requirements.
- `401` - Returned when there is a JWT-related error.
- `403` - Returned when the user is not authorized to access the endpoint.

---

### EP8: Fetching Cases

**Endpoint:** `POST /api/getCases`

#### Request Headers

- `Content-Type: application/json`
- `Authorization: Bearer <token_here>`

#### Request Body

```json
{}
```

#### Success Response

**Status Code:** `201`

```json
{
  "status": "success",
  "cases": [
    {
      "CaseId": "Example id here",
      "CaseCreator": "Creator here",
      "CaseName": "Suspicious AI-generated claim",
      "CaseReviews": null,
      "CaseDescription": "Example description",
      "CaseClosed": false,
      "CaseCreationDate": "2026-05-21T11:30:00"
    }
  ]
}
```

#### Example Error Response

**Status Code:** `401`

```json
{
  "status": "error",
  "message": "JWT related error here"
}
```

#### Possible Error Response Codes

- `401` - Returned when there is a JWT-related error.

---

### EP9: Fetching Single Case

**Endpoint:** `POST /api/getCases`

#### Request Headers

- `Content-Type: application/json`
- `Authorization: Bearer <token_here>`

#### Request Body

```json
{
  "caseID": "Some case ID"
}
```

#### Request Body Requirements

- The `caseID` must not be missing or empty.
- The `caseID` must be a valid UUID.

#### Success Response

**Status Code:** `200`

```json
{
  "status": "success",
  "case": {
    "CaseId": "Example id here",
    "CaseCreator": "Creator here",
    "CaseName": "Suspicious AI-generated claim",
    "CaseReviews": null,
    "CaseDescription": "Example description",
    "CaseClosed": false,
    "CaseCreationDate": "2026-05-21T11:30:00"
  }
}
```

#### Example Error Response

**Status Code:** `404`

```json
{
  "status": "error",
  "message": "Case not found"
}
```

#### Possible Error Response Codes

- `400` - Returned when the `caseID` is missing.
- `401` - Returned when the `caseID` is not a valid UUID or there is a JWT-related error.
- `404` - Returned when the case does not exist.

---

### EP10: Uploading Evidence

**Endpoint:** `POST /api/cases/evidence`

#### Request Headers

- `Content-Type: multipart/form-data`
- `Authorization: Bearer <token_here>`

#### Request Body

```json
{
  "caseID": "Some case ID",
  "media": "uploaded file"
}
```

#### Request Body Requirements

- The `caseID` must not be missing or empty.
- The `caseID` must be a valid UUID.
- The media file must be uploaded.

#### Success Response

**Status Code:** `201`

```json
{
  "status": "success",
  "evidence": {
    "MediaId": "Example media UUID here",
    "url": "http://localhost:9000/example-bucket/example-file.png",
    "Status": "uploaded"
  }
}
```

#### Example Error Response

**Status Code:** `404`

```json
{
  "status": "error",
  "message": "Case not found"
}
```

#### Possible Error Response Codes

- `400` - Returned when the file extension is unsupported or the `caseID` is invalid.
- `401` - Returned when there are JWT or UUID errors.
- `403` - Returned when the user is unauthorized.
- `404` - Returned when the case does not exist.
- `422` - Returned by FastAPI when the case media is missing from the form.

---
### EP11: Closing Cases
Endpoint: POST /api/closeCase

#### Parameters
	No Parameters

#### Request Body

```json
{
  "CaseID": "string"
}
```

#### Success Response

**Status Code:** `200`

```json
{
	"status": "success",
	"message": "Case closed successfully."
}
```

#### Example Error Response
Status code: 500
```json
{
	"status": "error",
	"message": "Database error"
}
```

#### Possible Error Response Codes

- `400` - Returned when the `caseID` is missing or invalid JWT
- 404 - When the case is not found or you are unauthorised to use the endpoint
- 500 - When there was a database error or an internal server error

----
### EP12: Update Case
Endpoint: POST /api/updateCase

#### Parameters
	No Parameters

#### Request Body
*Required*
```json
{
  "CaseID": "string", 
  "CaseName": "string",
  "CaseDescription": "string"
}
```

#### Success Response

**Status Code:** `200`

```json
{
	"status": "success",
	"message": "Case updated successfully."
}
```

#### Example Error Response
Status code: 500
```json
{
	"status": "error",
	"message": "Database error"
}
```

#### Possible Error Response Codes

- `400` - Returned when the `caseID` is missing or invalid or if the request body does not have everything
- 401 - Returned if the JWT is invalid
- 404 - Returned if case not found or user unauthorised
- 500 - When there was a database error or an internal server error


----
### EP13: Update Comment
Endpoint: POST /api/editComment/case/{case_id}/comment/{comment_id}

#### Parameters
	case_id: string *required* 
	is the uuid of the case
	comment_id: integer *required*
	The id of the comment
	
#### Request Body
*Required*

```json
{
  "comment": "string"
}
```

#### Success Response

**Status Code:** `200`

```json
{
	"status": "success",
	"message": "Comment edit successfully."
}
```

#### Example Error Response
Status code: 500
```json
{
	"status": "error",
	"message": "Database error"
}
```

#### Possible Error Response Codes

- `400` - Returned when the `caseID` is missing or invalid
- 401 - Returned if the JWT is invalid
- 404 - Returned if case not found or user unauthorised
- 500 - When there was a database error or an internal server error

----
### EP14: Delete Comment
Endpoint: DELETE /api/deleteComment/comment/{comment_id}

#### Parameters
	comment_id: integer *required*
	The id of the comment
	
#### Request Body
*Required*

```json
{
  "comment": "string"
}
```

#### Success Response

**Status Code:** `200`

```json
{
	"status": "success",
	"message": "Comment edit successfully."
}
```

#### Example Error Response
Status code: 500
```json
{
	"status": "error",
	"message": "Database error"
}
```

#### Possible Error Response Codes

- `400` - Returned when the `caseID` is missing or invalid
- 401 - Returned if the JWT is invalid
- 404 - Returned if comment not found or user unauthorised
- 500 - When there was a database error or an internal server error

----
### EP15: Retrieve Comment
Endpoint: POST /api/getComments/{case_id}
#### Parameters

	case_id: string *required*
	The uuuid of the case


#### Success Response

**Status Code:** `200`

```json
{
	"status": "success",
	"comments": json of the comments
}
```

#### Example Error Response
Status code: 500
```json
{
	"status": "error",
	"message": "Database error"
}
```

#### Possible Error Response Codes

- 403 - Returned if the JWT is invalid 
- 500 - When there was a database error or an internal server error

---
### EP16: Delete Evidence
Endpoint: POST /api/delete/case/{case_id}/evidence/{media_id}

#### Parameters
	case_id: string *reguired*
	the uuid of the case
	media_id: string *regular*
	the uuid of the media

#### Success Response

**Status Code:** `200`

```json
{
	"status": "success",
	"Deleted": media_id
}
```

#### Example Error Response
Status code: 500
```json
{
	"status": "error",
	"message": "Database error"
}
```

#### Possible Error Response Codes

- 400 - Invalid uuid for case id
- 401 - Returned if the JWT is invalid 
- 403 - Unauthorized to delete this evidence or record not found
- 404 - Returned if the media was not found or user unauthorised
- 500 - When there was a database error or an internal server error

---
### EP17: Create Comment
Endpoint: POST /api/cases/comments
#### Parameters
	no paramters
#### Request body

```json
{
  "case_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "comment": "string"
}
```

#### Success Response

**Status Code:** `201`

```json
{
	"status": "success",
	"comment": THe new comment
}
```

#### Example Error Response
Status code: 500
```json
{
	"status": "error",
	"message": "Database error"
}
```

#### Possible Error Response Codes

- 400 - Returned if the comment is empty
- 401 - Returned if the JWT is invalid 
- 500 - When there was a database error or an internal server error


---
### EP18: Delete Case
Endpoint: DELETE /api/deleteCase

#### Parameters
	no paramters
#### Request body

```json
{
  "CaseID": "string"
}
```


#### Success Response

**Status Code:** `201`

```json
{
	"status": "success",
	"message": "Case deleted successfully"
}
```

#### Example Error Response
Status code: 403

```json
{
  "status": "error",
  "message": "Invalid token or database failure"
}
```

#### Possible Error Response Codes

- 400 - Returned if the caseID is empty
- 401 - Returned if the case id is invalid 
- 403 - Returned if any other than the case owner tries to delete the case
- 404 - Returned if the case is not found
- 500 - When there was a database error or an internal server error

---
### EP19: Save Report Annotations
Endpoint: POST /api/saveAnnotations

#### Parameters
	no paramters
#### Request body

```json
{
  "reportId": "string",
  "annotations": [
    {
      "additionalProp1": {}
    }
  ]
}
```


#### Success Response

**Status Code:** `200`

```json
{
  "status": "success"
}
```

#### Example Error Response
Status code: 401

```json
{
  "status": "error",
  "message": "Signature has expired."
}
```

#### Possible Error Response Codes

- 401 - Returned if the JWT expired or if the UUID is malformed
- 403 - User unauthorized
- 404 - Returned if the case is not found
- 500 - When there was a database error or an internal server error

---
