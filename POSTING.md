# Posting procedure (one run = one clip)

This repo is a queue of Kai Cenat GTA 6 clips for the TikTok account "kai Clips" (@handle051).
Each scheduled run sends the NEXT clip to that account's TikTok drafts. The owner posts it from the app.

1. `queue.json` is a list, best first. Take the FIRST entry: `file`, `hook`, `caption`.
   If the list is empty, stop and report: "The clip queue is empty. Ask Claude to clip more Kai Cenat streams."
2. The clip's public link is
   `https://raw.githubusercontent.com/peacedurowaiye77-bot/kai-clips/main/<file>`
3. In the Composio remote workbench (COMPOSIO_REMOTE_WORKBENCH), in ONE cell:
   - download that link with `requests.get(url, timeout=150)` to `/home/user/<basename>`
   - `res, err = upload_local_file(path)` and take `res["s3key"]`
   - `run_composio_tool("TIKTOK_UPLOAD_VIDEO", {"file_to_upload": {"name": <basename>, "mimetype": "video/mp4", "s3key": <s3key>}, "publish": False}, account="tiktok_adhere-buba")`
   - print the returned `publish_id` and any error.
   The TikTok app is not audited yet, so `publish` MUST stay False (draft). Never post publicly.
4. Check it with TIKTOK_FETCH_PUBLISH_STATUS (account `tiktok_adhere-buba`). PROCESSING_UPLOAD with all bytes uploaded counts as success.
5. Only if the upload succeeded: `git rm` the clip, remove that entry from `queue.json`, commit, and push to `main`.
   If it failed, leave the queue unchanged so the next run retries it, and report the error.
6. Finish with a short message for the owner, exactly in this shape:

   New Kai clip in your TikTok drafts: <hook>
   Post at <1:00 PM or 10:00 PM> Nigeria time. Caption to paste:
   <caption>
   (<N> clips left in the queue)
