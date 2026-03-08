# Course Enrollment

## Overview

Enrollment management for courses. Users can enroll in active courses, track progress, and manage enrollment lifecycle (cancel/resume). All endpoints live under `/api/` and require JWT authentication.

---

## Enrollment Flow

```
User                    Frontend              Backend
 |                         |                     |
 |-- Browse courses ------>|                     |
 |                         |-- GET /courses ---->|
 |                         |<-- course list -----|
 |-- Tap "Enroll" -------->|                     |
 |                         |-- POST /enroll ---->|
 |                         |<-- enrollment (201) |
 |                         |                     |
 |-- View my courses ----->|                     |
 |                         |-- GET /enrollments >|
 |                         |<-- enrollment list -|
 |                         |                     |
 |-- Cancel enrollment --->|                     |
 |                         |-- POST /cancel ---->|
 |                         |<-- updated (200) ---|
 |                         |                     |
 |-- Re-enroll ----------->|                     |
 |                         |-- POST /enroll ---->|
 |                         |<-- reactivated (200)|
```

### Enrollment Status Lifecycle

```
            enroll
              |
              v
  resume -> ACTIVE -> cancel -> CANCELED
              |                    ^
              |                    |
              v                    |
           PAUSED ---- cancel -----+
              ^
              |
           (future: inactivity timeout)

  COMPLETED (terminal — cannot cancel or resume)
```

- **active**: default state on enrollment
- **paused**: reserved for future use (inactivity timeout)
- **canceled**: user explicitly left the course; can re-enroll
- **completed**: all assignments done; terminal state

---

## API Endpoints

All endpoints require `Authorization: Bearer <access_token>` header. Unauthenticated requests return `401`.

### 1. `POST /api/courses/{course_id}/enroll/`

Enroll in a course. Idempotent — safe to call multiple times.

**Request:** No body required.

**Created Response (201):**
```json
{
    "id": 1,
    "course": {
        "id": 5,
        "slug": "touch-typing-basics",
        "title": "Touch Typing Basics"
    },
    "status": "active",
    "progress_percent": 0.0,
    "current_lesson_id": null,
    "started_at": "2026-03-08T10:00:00Z",
    "completed_at": null,
    "last_activity_at": "2026-03-08T10:00:00Z"
}
```

**Behavior:**

| Scenario | Status Code | Result |
|---|---|---|
| New enrollment | 201 | Creates active enrollment |
| Already enrolled (active/completed) | 200 | Returns existing enrollment as-is |
| Previously canceled or paused | 200 | Reactivates to `active`, updates `last_activity_at` |
| Course not found or inactive | 404 | `{"detail": "Not found."}` |

### 2. `GET /api/enrollments/`

List all enrollments for the authenticated user. Paginated.

**Response (200):**
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "course": {
                "id": 5,
                "slug": "touch-typing-basics",
                "title": "Touch Typing Basics"
            },
            "status": "active",
            "progress_percent": 45.5,
            "current_lesson_id": 3,
            "started_at": "2026-03-08T10:00:00Z",
            "completed_at": null,
            "last_activity_at": "2026-03-08T12:30:00Z"
        }
    ]
}
```

### 3. `GET /api/enrollments/{id}/`

Get a single enrollment by ID. Returns `404` if the enrollment belongs to another user.

**Response (200):** Same shape as a single item from the list above.

### 4. `GET /api/courses/{course_id}/enrollment/`

Get enrollment by course ID. Useful when you have the course context and want to check enrollment status.

**Response (200):** Same enrollment shape.

**Errors:**

| Scenario | Status Code |
|---|---|
| Not enrolled in this course | 404 |

### 5. `POST /api/enrollments/{id}/cancel/`

Cancel an enrollment. No request body needed.

**Response (200):**
```json
{
    "id": 1,
    "course": { "id": 5, "slug": "touch-typing-basics", "title": "Touch Typing Basics" },
    "status": "canceled",
    "progress_percent": 45.5,
    "current_lesson_id": 3,
    "started_at": "2026-03-08T10:00:00Z",
    "completed_at": null,
    "last_activity_at": "2026-03-08T12:30:00Z"
}
```

**Allowed transitions:** `active` -> `canceled`, `paused` -> `canceled`

**Errors:**

| Scenario | Status Code | Response |
|---|---|---|
| Already canceled | 400 | `{"detail": "Cannot cancel enrollment with status 'canceled'."}` |
| Completed | 400 | `{"detail": "Cannot cancel enrollment with status 'completed'."}` |

### 6. `POST /api/enrollments/{id}/resume/`

Resume a canceled or paused enrollment. No request body needed.

**Response (200):** Returns enrollment with `status: "active"` and updated `last_activity_at`.

**Allowed transitions:** `canceled` -> `active`, `paused` -> `active`

**Errors:**

| Scenario | Status Code | Response |
|---|---|---|
| Already active | 400 | `{"detail": "Cannot resume enrollment with status 'active'."}` |
| Completed | 400 | `{"detail": "Cannot resume enrollment with status 'completed'."}` |

---

## Response Fields

| Field | Type | Description |
|---|---|---|
| `id` | integer | Enrollment ID |
| `course` | object | Nested course: `{id, slug, title}` |
| `status` | string | `"active"`, `"completed"`, `"paused"`, or `"canceled"` |
| `progress_percent` | float | 0.0 to 100.0 — percentage of distinct active assignments completed |
| `current_lesson_id` | integer or null | ID of the first lesson (by order) with at least one incomplete assignment. `null` if all done or no assignments exist |
| `started_at` | datetime | ISO 8601 timestamp of initial enrollment |
| `completed_at` | datetime or null | When enrollment was marked completed; `null` otherwise |
| `last_activity_at` | datetime | Updated on enroll, resume, and activity |

---

## Frontend Integration Notes

### Checking enrollment status on course page

Use `GET /api/courses/{course_id}/enrollment/` to check if the user is enrolled. A `404` means not enrolled — show the "Enroll" button. A `200` means enrolled — show progress and status.

### Progress bar

Use `progress_percent` directly for the progress bar width. The value is pre-calculated server-side as `(completed_assignments / total_active_assignments) * 100`, rounded to 1 decimal.

### "Continue" button

Use `current_lesson_id` to link to the next lesson the user should work on. If `null`, all assignments are complete.

### Re-enrollment

The enroll endpoint is idempotent. If a user previously canceled, calling `POST /enroll/` again will reactivate their enrollment and preserve their progress.
