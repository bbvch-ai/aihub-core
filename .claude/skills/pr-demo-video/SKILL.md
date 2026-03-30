---
name: pr-demo-video
description: Analyze a screen recording and add a demo section to the current PR on bbvch-ai/aihub-core. Extracts frames with ffmpeg, describes what the video shows using vision, updates the PR body with a Demo section and video description, and checks off matching test plan items. Use when user says 'add demo video to PR', 'add video to PR', 'describe the video', 'add screen recording to PR', or 'pr demo'. Do NOT use for creating the PR itself (use /create-pr), reviewing code (use /review-diff), or recording videos.
allowed-tools: Bash, Read, Grep, Glob
---

# PR Demo Video

Add a demo video description to the current branch's pull request on `bbvch-ai/aihub-core`.

## Step 1: Locate the Video

If the user provides a path, use that. Otherwise find the most recent screen recording:

```bash
ls -t ~/Videos/Screencasts/*.mp4 | head -1
```

Screen recordings are stored at `~/Videos/Screencasts/` as `Screencast from YYYY-MM-DD HH-MM-SS.mp4`.

## Step 2: Extract Metadata and Frames

Get duration and resolution, then extract one frame every 10 seconds for analysis:

```bash
ffmpeg -i "$VIDEO_PATH" 2>&1 | grep -E "Duration|Video|Stream"
mkdir -p /tmp/video-frames
ffmpeg -i "$VIDEO_PATH" -vf "fps=1/10" -q:v 2 /tmp/video-frames/frame_%02d.jpg -y
```

## Step 3: Analyze Frames

Read each extracted frame using the Read tool (which supports images). For each frame, note:

- What URL is visible in the browser address bar
- What UI elements or pages are shown
- What data is visible (API responses, network tab, console)
- What the user is demonstrating

Build a chronological narrative of what the video shows.

## Step 4: Get Current PR

Find the PR for the current branch:

```bash
gh pr view --json number,body -R bbvch-ai/aihub-core
```

## Step 5: Write the Demo Section

Format the demo section following this repo's PR body convention:

```markdown
## Demo

> **Video description:** {One-line summary of what the video demonstrates} ({duration}).
> 1. {First thing shown} -- {what it proves}
> 2. {Second thing shown} -- {what it proves}
> ...

_(Upload video here -- drag `{VIDEO_PATH}` into this text area)_
```

Key rules:

- Lead with a one-line summary including duration (e.g., "1m24s")
- Each numbered item describes what is VISIBLE, not what was changed in code
- Connect each item to what it PROVES about the feature (e.g., "confirming health is outside tenant scope")
- Include the full path to the video file so the user can drag-and-drop

## Step 6: Update Test Plan

Read the existing `## Test plan` section. For each checklist item, check if the video visually demonstrates it. If so,
mark it as checked (`- [x]`). Do NOT uncheck already-checked items.

## Step 7: Update the PR

Use `gh pr edit` to update the PR body with the new Demo section and updated Test plan:

```bash
gh pr edit {PR_NUMBER} --body "$(cat <<'EOF'
{full updated PR body}
EOF
)"
```

## Step 8: Remind About Upload

Tell the user to manually upload the video file by dragging it into the PR description on GitHub, since `gh` CLI cannot
upload video attachments. Include the exact file path for convenience.

## Common Mistakes

- **Forgetting the video path hint**: Always include the drag-and-drop instruction with the full file path -- the user
  needs to upload manually since GitHub CLI can't attach videos.
- **Over-describing code changes**: The demo section describes what is VISIBLE in the video, not what was changed in the
  codebase. "API requests return 200" not "added tenant path parameter".
- **Unchecking test plan items**: Only ADD checkmarks to items the video demonstrates. Never uncheck items that were
  already checked.
