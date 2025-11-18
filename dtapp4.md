# dtapp4 – Decision Tree Android app: RQ + statusinfo + GmailReader

Date: 2025-11-17

I updated the Decision Tree Android app (mobile module) in the
`github.com/we6jbo/decision-tree-assistant` repo to improve how it talks
to the Raspberry Pi and how it surfaces status.

Key points:

- MainActivity now creates a time-based **Request ID (RQ)** only when
  “Send to Raspberry Pi” is pressed. The RQ is stored via
  `RequestIdStore`, so the same RQ survives app restarts until I send a
  new question.

- Outgoing questions use subjects like:
  `dt-in RQ:<requestId>` and include the RQ in the body. This gives the Pi
  a stable key to echo back in `dt-out` responses.

- The app has a dedicated **Status Info** TextView (`txtStatusInfo`)
  that displays status messages from the Raspberry Pi separately from
  the main Decision Tree answer.

- `GmailReader` now:
  - Fetches the latest **Decision Tree reply** using a Gmail search of:
    `to:we6jbo+decisiontree@gmail.com subject:"dt-out RQ:<requestId>"`
  - Fetches the latest **status message** using:
    `to:we6jbo+decisiontree@gmail.com subject:statusinfo`
  - Decodes and returns the plain-text body for both.

- The status messages are intended to look like:
  subjects beginning with `statusinfo` plus a time-based tag, with the
  body describing Pi health (slow responses, critical issues, etc.).

- Both reply and status lookups run with a 15s timeout and are wrapped
  in non-fatal error handling. Hangs use code **AQeD** and exceptions
  use **WEC2**, with auto-generated debug text copied to clipboard and
  offered via Android’s share sheet for ChatGPT debugging.

Overall, **dtapp4** = “Android Decision Tree app upgraded with RQ-based
matching, statusinfo support, and robust GmailReader error handling.”

Planned follow-up: I will write and publish a blog entry about this
update on **https://j03.page/** by **2025-11-19 17:30** (local time).
