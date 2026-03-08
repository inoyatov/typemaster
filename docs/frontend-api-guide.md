# Frontend API Guide: Assignment Completion & Progress Tracking

## What's New

Three new capabilities added to the API:

1. **Assignment Completion** — submit typing results after completing an assignment
2. **Lesson Progress** — check how many assignments are done in a lesson
3. **Enriched Enrollment Response** — all enrollment endpoints now return detailed progress fields

---

## New Endpoints

### 1. Complete an Assignment

```
POST /api/courses/{course_slug}/lessons/{lesson_id}/assignments/{assignment_id}/completion/
```

**Auth:** JWT required

**Request body:**

```json
{
  "action_type": "complete",
  "average_speed": 120,
  "mistakes_count": 3
}
```

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `action_type` | string | Required. Must be `"complete"` | Type of completion action |
| `average_speed` | integer | Required. Min: 1 | Average typing speed in chars/min |
| `mistakes_count` | integer | Required. Min: 0 | Number of mistakes made |

**Response (201 Created — first submission):**

```json
{
  "id": 1,
  "action_type": "complete",
  "average_speed": 120,
  "mistakes_count": 3,
  "completed_at": "2026-03-08T13:10:00Z",
  "lesson_progress": {
    "lesson_id": 5,
    "status": "in_progress",
    "completed_assignments": 7,
    "total_assignments": 10,
    "progress_percent": 70.0,
    "completed_at": null
  }
}
```

**Response (200 OK — re-submission updates existing record):**

Same shape as above. The `average_speed`, `mistakes_count`, and `completed_at` are updated. Only one completion record exists per user+assignment pair.

**Idempotent:** Submitting again for the same assignment updates the existing record instead of creating a duplicate.

**Error responses:**

| Status | Condition |
|--------|-----------|
| 400 | Validation error (missing fields, invalid `action_type`, `average_speed < 1`, `mistakes_count < 0`) |
| 401 | Not authenticated |
| 403 | No active enrollment for this course |
| 403 | Paid lesson without active subscription |
| 404 | Invalid course_slug, lesson_id, or assignment_id |
| 404 | Course, lesson, or assignment is inactive |

**Side effects:**
- Updates `last_activity_at` on the enrollment
- If all active assignments in the course are now completed, the enrollment status automatically changes to `"completed"` and `completed_at` is set

---

### 2. Get an Existing Completion

```
GET /api/courses/{course_slug}/lessons/{lesson_id}/assignments/{assignment_id}/completion/
```

**Auth:** JWT required

**Response (200 OK):**

```json
{
  "id": 1,
  "action_type": "complete",
  "average_speed": 120,
  "mistakes_count": 3,
  "completed_at": "2026-03-08T13:10:00Z"
}
```

Note: No `lesson_progress` field on GET — only on POST.

**Error responses:**

| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 404 | Assignment not found or not completed by this user |

**Access:** No enrollment or subscription check on GET. Users can view their past completions regardless of enrollment status.

---

### 3. Get Lesson Progress

```
GET /api/courses/{course_slug}/lessons/{lesson_id}/progress/
```

**Auth:** JWT required

**Response (200 OK):**

```json
{
  "lesson_id": 5,
  "status": "in_progress",
  "completed_assignments": 7,
  "total_assignments": 10,
  "progress_percent": 70.0,
  "completed_at": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `lesson_id` | integer | The lesson ID |
| `status` | string | `"in_progress"` or `"completed"` |
| `completed_assignments` | integer | Number of active assignments the user has completed |
| `total_assignments` | integer | Total number of active assignments in the lesson |
| `progress_percent` | float | 0.0 to 100.0 (one decimal place) |
| `completed_at` | string/null | ISO 8601 timestamp when the last assignment was completed (only set when `status` is `"completed"`) |

When `total_assignments` is 0 (no active assignments), `progress_percent` is `0.0` and `status` is `"in_progress"`.

**Error responses:**

| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | Not enrolled in this course (any enrollment status is accepted — active, paused, canceled, or completed) |
| 404 | Invalid course or lesson, or lesson/course is inactive |

---

## Changed Endpoints: Enriched Enrollment Response

All enrollment endpoints now return additional progress fields. This is a **breaking change** — new fields are added to the response.

**Affected endpoints:**
- `GET /api/enrollments/` (list)
- `GET /api/enrollments/{id}/` (detail)
- `POST /api/courses/{slug}/enroll/`
- `GET /api/courses/{slug}/enrollment/`
- `POST /api/enrollments/{id}/cancel/`
- `POST /api/enrollments/{id}/resume/`

**Previous response shape:**

```json
{
  "id": 1,
  "course": { "id": 5, "slug": "russian-touch-typing", "title": "..." },
  "status": "active",
  "progress_percent": 30.0,
  "current_lesson_id": 8,
  "started_at": "2026-03-08T10:00:00Z",
  "completed_at": null,
  "last_activity_at": "2026-03-08T12:30:00Z"
}
```

**New response shape (4 fields added):**

```json
{
  "id": 1,
  "course": { "id": 5, "slug": "russian-touch-typing", "title": "..." },
  "status": "active",
  "progress_percent": 30.0,
  "current_lesson_id": 8,
  "completed_assignments": 24,
  "total_assignments": 80,
  "completed_lessons": 3,
  "total_lessons": 10,
  "started_at": "2026-03-08T10:00:00Z",
  "completed_at": null,
  "last_activity_at": "2026-03-08T12:30:00Z"
}
```

**New fields:**

| Field | Type | Description |
|-------|------|-------------|
| `completed_assignments` | integer | Number of active assignments the user has completed across the entire course |
| `total_assignments` | integer | Total number of active assignments in the course |
| `completed_lessons` | integer | Number of lessons where all active assignments are completed |
| `total_lessons` | integer | Total number of active lessons in the course |

**Existing fields (unchanged):**

| Field | Type | Description |
|-------|------|-------------|
| `progress_percent` | float | Based on assignments: `completed_assignments / total_assignments * 100` |
| `current_lesson_id` | integer/null | ID of the first lesson that still has incomplete assignments. `null` when all done |
| `status` | string | `"active"`, `"paused"`, `"canceled"`, or `"completed"` |
| `started_at` | string | ISO 8601 enrollment timestamp |
| `completed_at` | string/null | Set when all assignments are completed (auto-completion) |
| `last_activity_at` | string | Updated on enroll, resume, and assignment completion |

---

## Typical Frontend Flow

### When user finishes typing an assignment:

```
POST /api/courses/russian/lessons/5/assignments/12/completion/
{
  "action_type": "complete",
  "average_speed": 245,
  "mistakes_count": 2
}
```

From the response:
1. Show completion feedback using `average_speed` and `mistakes_count`
2. Update lesson progress bar using `lesson_progress.progress_percent`
3. If `lesson_progress.status === "completed"`, show lesson completion state
4. Optionally refresh enrollment data to update course-level progress

### To show lesson progress (e.g. on lesson page):

```
GET /api/courses/russian/lessons/5/progress/
```

### To show course progress (e.g. on dashboard):

Use enrollment endpoints — progress data is already included:

```
GET /api/courses/russian/enrollment/
```

or

```
GET /api/enrollments/
```

---

## Access Rules Summary

| Endpoint | Enrollment Required | Enrollment Status | Subscription (Paid Lessons) |
|----------|--------------------|--------------------|----------------------------|
| `POST .../completion/` | Yes | Must be `active` | Required |
| `GET .../completion/` | No | Any | Not required |
| `GET .../progress/` | Yes | Any (active, paused, canceled, completed) | Not required |

---

## Enrollment Auto-Completion

When a user completes the last remaining active assignment in a course, the enrollment automatically transitions:

- `status` changes from `"active"` to `"completed"`
- `completed_at` is set to the current timestamp

This happens within the `POST .../completion/` call. The frontend can detect this by re-fetching the enrollment after a completion, or by checking if `lesson_progress.status === "completed"` on the last lesson.
