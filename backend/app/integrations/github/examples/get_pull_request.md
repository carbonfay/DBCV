# Example: GitHub Get Pull Request

Config example (use as `integration_config`):

```json
{
  "owner": "octocat",
  "repo": "Hello-World",
  "pull_number": 1
}
```

Credentials: provider `other`, strategy `api_key`. Payload should include `api_key` or `access_token` with a personal access token.

Successful result format:

```json
{
  "response": {
    "ok": true,
    "result": {
      "number": 1,
      "title": "Fix issue",
      "state": "open",
      "html_url": "https://github.com/octocat/Hello-World/pull/1",
      "user": {"login": "contributor", "id": 12345},
      ...
    }
  }
}
```
