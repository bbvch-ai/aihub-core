---
name: pr-demo-video
description: Analyze a screen recording and add a demo section to the current PR on bbvch-ai/aihub-core. Extracts frames with ffmpeg, describes what the video shows using vision, updates the PR body with a Demo section and video description, and checks off matching test plan items. Use when user says 'add demo video to PR', 'add video to PR', 'describe the video', 'add screen recording to PR', or 'pr demo'. Do NOT use for creating the PR itself (use /create-pr), reviewing code (use /review-diff), or recording videos.
allowed-tools: Bash, Read, Grep, Glob, AskUserQuestion
---

# PR Demo Video

Add a demo video description to the current branch's pull request on `bbvch-ai/aihub-core`.

## Step 1: Locate the Video

If the user provides a path, use that. Otherwise, find the most recent screen recording by detecting the OS-specific
default location:

```bash
# Detect OS and find screen recordings directory
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  # GNOME/Ubuntu: ~/Videos/Screencasts/
  CANDIDATES=("$HOME/Videos/Screencasts" "$HOME/Videos" "$HOME/Screencasts")
elif [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS: ~/Desktop/ or ~/Movies/
  CANDIDATES=("$HOME/Desktop" "$HOME/Movies")
else
  CANDIDATES=("$HOME/Videos" "$HOME/Desktop")
fi

for dir in "${CANDIDATES[@]}"; do
  LATEST=$(ls -t "$dir"/*.mp4 "$dir"/*.mov "$dir"/*.webm 2>/dev/null | head -1)
  [ -n "$LATEST" ] && break
done
echo "$LATEST"
```

If no recording is found in any default location, ask the user for the path.

## Step 2: Ask About Key Moments

Before extracting frames, ask the user what the video demonstrates and which moments are most important. Frame
extraction at fixed intervals is lossy — a 10-second gap can miss a crucial UI state, API response, or transition.

Use AskUserQuestion to ask:

> "What are the key moments or things shown in this video that I should capture in the demo description?"

Provide options based on common demo patterns in this repo (e.g., "API response in Swagger", "Agent chat interaction in
OpenWebUI", "Admin UI configuration", "Process workflow step"). Allow multi-select and free-text input.

Use the user's answer to:

1. Know what to look for when analyzing frames (so you don't misidentify UI elements)
2. Ensure every key moment the user mentions appears in the final demo description
3. Extract additional frames at higher density (fps=1/3) if the video is short, to avoid missing transitions

## Step 3: Extract Metadata and Frames

Get duration and resolution, then extract frames for analysis:

```bash
ffmpeg -i "$VIDEO_PATH" 2>&1 | grep -E "Duration|Video|Stream"
mkdir -p /tmp/video-frames
# For videos under 2 minutes, extract every 3 seconds to catch transitions
# For longer videos, extract every 10 seconds
ffmpeg -i "$VIDEO_PATH" -vf "fps=1/3" -q:v 2 /tmp/video-frames/frame_%02d.jpg -y
```

If the video is longer than 2 minutes, use `fps=1/10` instead to keep frame count manageable.

## Step 4: Analyze Frames

Read each extracted frame using the Read tool (which supports images). For each frame, note:

- What URL is visible in the browser address bar
- What UI elements or pages are shown
- What data is visible (API responses, network tab, console)
- What the user is demonstrating

Cross-reference against the key moments from Step 2. If any moment the user mentioned is NOT visible in the extracted
frames, flag it — the user may need to provide a timestamp or the frame extraction interval was too coarse.

Build a chronological narrative of what the video shows.

## Step 5: Get Current PR

Find the PR for the current branch:

```bash
gh pr view --json number,body -R bbvch-ai/aihub-core
```

## Step 6: Write the Demo Section

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

## Step 7: Update Test Plan

Read the existing `## Test plan` section. For each checklist item, check if the video visually demonstrates it. If so,
mark it as checked (`- [x]`). Do NOT uncheck already-checked items.

## Step 8: Update the PR

Use `gh pr edit` to update the PR body with the new Demo section and updated Test plan:

```bash
gh pr edit {PR_NUMBER} --body "$(cat <<'EOF'
{full updated PR body}
EOF
)"
```

## Step 9: Remind About Upload

Tell the user to manually upload the video file by dragging it into the PR description on GitHub, since `gh` CLI cannot
upload video attachments. Include the exact file path for convenience.

## Common Mistakes

- **Forgetting the video path hint**: Always include the drag-and-drop instruction with the full file path -- the user
  needs to upload manually since GitHub CLI can't attach videos.
- **Over-describing code changes**: The demo section describes what is VISIBLE in the video, not what was changed in the
  codebase. "API requests return 200" not "added tenant path parameter".
- **Unchecking test plan items**: Only ADD checkmarks to items the video demonstrates. Never uncheck items that were
  already checked.
- **Skipping the key moments question**: Always ask the user what the video shows before analyzing frames.
  Fixed-interval frame extraction misses transitions, and the user knows exactly which moments matter for the PR.
