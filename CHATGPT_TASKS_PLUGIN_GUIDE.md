# ChatGPT Tasks Plugin Guide

## Why ChatGPT Was Seeing Only One Task

The `list_tasks` function is not limited to one task. It uses:

```python
row_limit = normalize_limit(limit, default=100)
queries = [Query.equal("userId", user_id), Query.limit(row_limit)]
```

So by default it can return up to 100 tasks for the user.

The problem is the output format you pasted. It is several independent JSON
objects printed one after another:

```json
{ "...": "task 1" }
{ "...": "task 2" }
{ "...": "task 3" }
```

That is not one valid JSON document. A JSON parser, plugin client, or ChatGPT
may read only the first object and ignore the remaining objects.

The output should be returned as one array or one object containing arrays:

```json
[
  { "...": "task 1" },
  { "...": "task 2" },
  { "...": "task 3" }
]
```

or grouped by project:

```json
{
  "projects": [
    {
      "projectId": "project-id",
      "tasks": []
    }
  ]
}
```

## Tool ChatGPT Should Use

Use the MCP tool:

```text
list_project_tasks
```

This returns one readable document shaped like this:

```json
[
  {
    "$id": "project-id",
    "name": "Project name",
    "tasks": [
      {
        "$id": "task-id",
        "content": "Task title",
        "isCompleted": false
      }
    ]
  }
]
```

When asking ChatGPT, use wording like:

```text
Use list_project_tasks for user_id 6a888c7b002ac73fd297 and show all tasks grouped by project. Do not call list_tasks with limit 1.
```

## Merged Task Output From The Pasted Data

```json
{
  "userId": "6a888c7b002ac73fd297",
  "tasksByProject": [
    {
      "projectId": "6a983c270000c4001371",
      "tasks": [
        {
          "$id": "6a983c4f00088b8785f3",
          "content": "Discuss on GIS Users",
          "priority": 1,
          "isCompleted": false,
          "dueDate": null
        }
      ]
    },
    {
      "projectId": "6a98743a00124a9ab1c7",
      "tasks": [
        {
          "$id": "6a98740b0028c8be1055",
          "content": "Validate Rovuma nap in gis cloud",
          "priority": 1,
          "isCompleted": false,
          "dueDate": null
        },
        {
          "$id": "6a9874f90039fc562a5a",
          "content": "Add users to Rovuma web map",
          "priority": 1,
          "isCompleted": false,
          "dueDate": null
        },
        {
          "$id": "6a98750b0008cbe4b11d",
          "content": "Reorganise Rovuma web map",
          "priority": 1,
          "isCompleted": false,
          "dueDate": null
        },
        {
          "$id": "6a987595003871db3c0b",
          "content": "Recreate Rovuma web map from agsportal to azure gis cloud",
          "priority": 1,
          "isCompleted": false,
          "dueDate": null
        }
      ]
    },
    {
      "projectId": "6a9711740022a0ba6a0a",
      "tasks": [
        {
          "$id": "6a98745e001a0211077c",
          "content": "Update SDE layers from staging file gdb",
          "priority": 1,
          "isCompleted": false,
          "dueDate": null
        },
        {
          "$id": "6a987484001053cfb77a",
          "content": "Prepare MSR",
          "priority": 1,
          "isCompleted": false,
          "dueDate": null
        }
      ]
    },
    {
      "projectId": "6a9874940009217e4d1b",
      "tasks": [
        {
          "$id": "6a9874af0033d6a62a77",
          "content": "Follow up on Vessel tracking",
          "priority": 1,
          "isCompleted": false,
          "dueDate": null
        },
        {
          "$id": "6a9874d9003aed548083",
          "content": "POC for PODS Viewer dashboard with Jasmine",
          "priority": 1,
          "isCompleted": false,
          "dueDate": null
        }
      ]
    },
    {
      "projectId": "6a97116e000bc3c92c07",
      "tasks": [
        {
          "$id": "6a9875cb0005efa8a3c5",
          "content": "Gregs meeting",
          "priority": 1,
          "isCompleted": false,
          "dueDate": "2026-09-04T00:00:00.000+00:00"
        }
      ]
    },
    {
      "projectId": null,
      "tasks": [
        {
          "$id": "6a9933bd002e162a7d61",
          "content": "Test",
          "priority": 1,
          "isCompleted": true,
          "dueDate": "2026-09-03T08:23:58.016+00:00"
        },
        {
          "$id": "6a9939c8001eed108b8d",
          "content": "Low",
          "priority": 1,
          "isCompleted": false,
          "dueDate": null
        },
        {
          "$id": "6a9939ce002e82166610",
          "content": "Medium",
          "priority": 2,
          "isCompleted": false,
          "dueDate": null
        },
        {
          "$id": "6a9939d2001a1ab8e07d",
          "content": "High",
          "priority": 1,
          "isCompleted": false,
          "dueDate": null
        },
        {
          "$id": "6a9939d8000e19858acd",
          "content": "Urgent",
          "priority": 1,
          "isCompleted": false,
          "dueDate": null
        }
      ]
    }
  ],
  "taskCount": 15
}
```

## Correct MCP Behavior

The MCP tool should return Python data structures, not printed JSON strings.

Good:

```python
return get_list_items(result, "rows")
```

Also good for grouped tasks:

```python
return [
    {
        **project,
        "tasks": tasks_by_project.get(project.get("$id") or project.get("id"), []),
    }
    for project in projects
]
```

Avoid returning or printing many standalone JSON objects one after another.

