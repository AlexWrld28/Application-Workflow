# Application Workflow

This repository tracks two pieces of application data:

- [`application_profile.json`](./application_profile.json): your private autofill profile.
- [`completed_applications.json`](./completed_applications.json): the log of applications you have already submitted.

## How to use it

1. Keep `application_profile.json` up to date with your contact, education, work authorization, and link data.
2. Use the autofill helper to prefill application forms, then review and submit them manually.
3. After submitting an application, add a new record to `completed_applications.json`.

## Adding an entry to `completed_applications.json`

`completed_applications.json` is a JSON array of application objects. New entries should be added in newest-first order so the most recent submission stays near the top. The first record's `application_number` is the current total number of applications submitted.

Use the same fields as the existing records:

- `application_number`
- `company`
- `title`
- `url`
- `location`
- `status`
- `submitted_at`
- `notes`

Example:

```json
{
  "application_number": 1,
  "company": "Example Co",
  "title": "Software Engineering Intern",
  "url": "https://example.com/jobs/123",
  "location": "New York, NY",
  "status": "submitted",
  "submitted_at": "2026-06-24T09:30:00",
  "notes": "Applied through company site"
}
```

Rules to keep in mind:

- Keep the file valid JSON.
- Add a comma between objects, but not after the final object.
- Increment `application_number` by 1 for each new application.
- Use ISO 8601 timestamps for `submitted_at`.
- Use empty strings for fields you do not know yet instead of inventing values.

## CLI workflow

Use the helper in [`main.py`](./main.py) to add an entry one field at a time:

```bash
python main.py applications add
```

The command will prompt for each field on its own line. Press Enter to accept the default for optional fields.
The `application_number` is added automatically.

If you want to paste values line by line without prompts, use stdin mode:

```bash
python main.py applications add --stdin
```

Values are read in this order:

1. `company`
2. `title`
3. `url`
4. `location`
5. `status`
6. `submitted_at`
7. `notes`

The trailing `/` in `python3 main.py applications add /` is not needed.

## Other tracked data

`application_profile.json` currently contains:

- contact information
- links
- education
- work authorization
- resume path
- EEO fields

That file is used by the autofill helper to populate common form fields before you review the application in the browser.
