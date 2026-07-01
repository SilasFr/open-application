# Contract: Contacts

Base: `/api/v1/applications/{application_id}/contacts`. Requires
`Authorization: Bearer <token>`. Parent-application ownership enforced → **404** otherwise.

Router: `backend/app/api/v1/routers/contacts.py` (thin) → `ContactService`.

## GET `/api/v1/applications/{application_id}/contacts`

- **200** → `ContactRead[]` · **401** · **404** application not found/owned

## POST `/api/v1/applications/{application_id}/contacts`

- Body `ContactCreate`:
  `{ "name": "string (non-empty)", "role"?: string, "email"?: string(email),
     "phone"?: string, "linkedin_url"?: string(url), "notes"?: string }`
- **201** → `ContactRead`
- **422** empty name / malformed email or url · **404** application not found/owned · **401**

## PATCH `/api/v1/applications/{application_id}/contacts/{contact_id}`

- Body `ContactUpdate`: any subset of the mutable fields above.
- **200** → `ContactRead` · **404** not found/owned · **422** validation · **401**

## DELETE `/api/v1/applications/{application_id}/contacts/{contact_id}`

- **204** · **404** not found/owned · **401**

## Schemas

```
ContactRead {
  id: uuid, application_id: uuid, name: string, role: string|null,
  email: string|null, phone: string|null, linkedin_url: string|null,
  notes: string|null, created_at: datetime
}
```
