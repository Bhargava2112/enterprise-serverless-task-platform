# HTTP API specification

Base URL: `https://<api-id>.execute-api.<region>.amazonaws.com/v1`.
All routes except `GET /health` require `Authorization: Bearer <Cognito ID token>`.

| Method | Route | Body | Success |
|---|---|---|---|
| GET | `/health` | — | `200 {"status":"ok"}` |
| POST | `/tasks` | `{"title":"Task","description":"Optional"}` | `201` + task |
| GET | `/tasks?limit=25&cursor=...` | — | `200 {"items":[],"nextCursor":null}` |
| GET | `/tasks/{taskId}` | — | `200` + task |
| PATCH | `/tasks/{taskId}` | `{"version":1,"status":"DONE"}` | `200` + updated task |
| DELETE | `/tasks/{taskId}?version=2` | — | `204` |
| GET | `/audit?limit=25&cursor=...` | — | `200 {"items":[],"nextCursor":null}` (admin) |

Status values: `OPEN`, `IN_PROGRESS`, `DONE`.
Task IDs are UUIDs. An owner or tenant admin may mutate tasks. Every mutation produces an immutable audit record in the same database transaction. Stale versions return 409; cross-tenant tasks appear as 404. The owner index is eventually consistent.
