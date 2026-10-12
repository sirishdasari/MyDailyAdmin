# MyDaily MCP v2.3

MCP Python SDK v2 server for the existing MyDaily Appwrite schema.

## Guitar practice records

Curriculum sessions are stored in `guitarpractice`; completed/actual practice entries are stored in `guitarPracticeRecords`. Configure the latter with `APPWRITE_GUITAR_PRACTICE_RECORDS_TABLE_ID`, which defaults to `guitarPracticeRecords`. Both use `APPWRITE_GUITAR_ENDPOINT`, `APPWRITE_GUITAR_PROJECT_ID`, and `APPWRITE_GUITAR_DATABASE_ID`.

The new `list_guitar_practice_records` tool returns each record's original fields plus a nested `session` object looked up through `record.sessionId == guitarpractice.$id`. The linked session contains `$id`, `sessionName`, `category`, `level`, `suggestedTime`, and `link`. `sessionId = "general-practice"` represents standalone practice and returns `session: null`. Missing curriculum links are kept as records with `session: null`.

**Duration semantics:** `guitarPracticeRecords.duration` is actual practice time in integer seconds. It is returned unchanged, never substituted by curriculum `duration` or `suggestedTime`, and is summed into `totalDurationSeconds` only over records returned by the current filters and limit. The tool is read-only and does not modify `dailyPracticeTime`.

### Tool parameters

- `session_id`: optional exact `sessionId` match
- `practice_date`: optional exact `YYYY-MM-DD` date
- `completed`: optional nullable boolean
- `limit`: defaults to 25; clamped to 1–100

Results request `startedAt` descending order. Add an Appwrite index on `startedAt` for server-side ordering. If it is not available, the service falls back to `$createdAt` ordering and sorts that fetched page locally; this fallback does not guarantee globally newest results when additional records exist beyond the page. Appwrite may also require equality indexes on `sessionId`, `practiceDate`, or `completed` depending on the deployed query schema.

Example response (illustrative):

```json
{
  "documentType": "guitarPracticeRecords",
  "filters": {
    "session_id": null,
    "practice_date": "2026-10-13",
    "completed": true,
    "limit": 25
  },
  "recordCount": 1,
  "totalDurationSeconds": 1200,
  "records": [
    {
      "$id": "record-id",
      "sessionId": "curriculum-session-id",
      "practiceDate": "2026-10-13",
      "startedAt": "2026-10-13T09:00:00.000Z",
      "endedAt": "2026-10-13T09:20:00.000Z",
      "duration": 1200,
      "completed": true,
      "session": {
        "$id": "curriculum-session-id",
        "sessionName": "Beginner Fingerstyle Practice",
        "category": "Fingerstyle",
        "level": "Beginner",
        "suggestedTime": 1800,
        "link": "https://example.com/lesson"
      }
    }
  ]
}
```

## Environment variables

The standard MyDaily services use `APPWRITE_ENDPOINT`, `APPWRITE_PROJECT_ID`, `APPWRITE_API_KEY`, and `APPWRITE_DATABASE_ID`. Guitar services use the shared/open configuration:

```env
APPWRITE_GUITAR_ENDPOINT=https://fra.cloud.appwrite.io/v1
APPWRITE_GUITAR_PROJECT_ID=your_guitar_project_id
APPWRITE_GUITAR_DATABASE_ID=your_guitar_database_id
APPWRITE_GUITAR_PRACTICE_TABLE_ID=guitarpractice
APPWRITE_GUITAR_PRACTICE_RECORDS_TABLE_ID=guitarPracticeRecords
```

If Appwrite table IDs differ from these names, set the corresponding environment variables in Render or the local `.env`.

## MCP tools

Existing user, profile, project, task, and guitar curriculum CRUD tools remain available. Guitar tools include `add_guitar_practice`, `list_guitar_practice`, `list_guitar_practice_records`, `get_guitar_practice`, `update_guitar_practice`, `complete_guitar_practice`, and `delete_guitar_practice`.

## Install and run

```powershell
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

MCP endpoint: `http://127.0.0.1:8000/mcp`.

## Important

The standard MyDaily services use a server-side Appwrite API key. Guitar tools use separate shared/open Appwrite configuration and do not use that API key. Consider caller authentication/authorization before exposing the MCP publicly.
