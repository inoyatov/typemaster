# Swagger UI in Staging

Swagger UI and ReDoc are available in the staging environment, restricted to authenticated superusers/staff.

## Endpoints

- Swagger UI: `https://api.staging.keypro.uz/swagger/`
- ReDoc: `https://api.staging.keypro.uz/redoc/`

## Access

Only Django staff users (`is_staff=True`) can access these endpoints. Non-staff users will receive a `403 Forbidden` response.

## Setup

1. Create a superuser (if one doesn't exist):

   ```bash
   python src/manage.py createsuperuser
   ```

2. Log in to the Django admin at `https://api.staging.keypro.uz/admin/` with your superuser credentials. This establishes a session cookie.

3. Navigate to `/swagger/` or `/redoc/` in the same browser. The session cookie authenticates you automatically.

## Notes

- The schema is **not public** (`public=False`), so only endpoints accessible to the logged-in user are shown.
- In the **development** environment, Swagger is open to everyone without authentication.
- Swagger is **not available** in production.
