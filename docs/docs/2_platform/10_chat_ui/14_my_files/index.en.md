---
title: My Files
---

# My Files

**My Files** is your own file space: every file you attach in an agent chat, every file an agent makes for you, and
everything you upload yourself, in one place. You can open, download, upload, rename, move into folders and delete them,
and agents can read them when you let them.

The files live in your home in the code sandbox, the same place the
[Universal Agent](../../5_agents/13_universal_agent/) runs code and OpenWebUI's terminal works. Nobody else sees them.

## Where to find it

- **On its own**: open **My Files** in the app menu.
- **Next to a chat**: click the folder icon under an agent's answer. My Files opens beside the chat, at that chat's
  folder.

## How it is organised

- **`conversations/`** holds a folder per agent chat, shown with the chat's title. Every file you attach in that chat
  lands there, and so do files an agent made in it.
- Everything else is yours to organise: create folders and move files into them.

Files whose names start with a dot are hidden; they belong to the sandbox and its tools.

## What you can do

| Action         | How                                                                                   |
| -------------- | ------------------------------------------------------------------------------------- |
| Open a folder  | Click it; the path above the list takes you back.                                     |
| Preview a file | Click it. Text, images and PDFs show beside the list.                                 |
| Download       | The download icon. Every file downloads exactly as stored, office documents included. |
| Upload         | **Upload**, or drop files onto the list. A file with the same name is replaced.       |
| New folder     | **New folder**.                                                                       |
| Rename         | The pencil icon.                                                                      |
| Move           | The folder icon: into a folder in the current one, or up one level.                   |
| Delete         | The bin icon. A folder is deleted with everything in it.                              |

Changes take effect right away: code an agent runs afterwards sees them.

## Letting an agent read your files

In a chat with the Universal Agent, switch on **My Files** in the chat's toggles. The agent can then list your folders
and read your files, including PDF and office documents as text, to answer you. It never changes or deletes them; to
create files, it uses [Code Interpreter](../6_coding/).

## Good to know

- **Your file space is set up with your chat account.** If My Files says it is not set up yet, open the chat once.
- **Files are kept.** They are copied to the platform's storage every few minutes; a file you delete is kept there for a
  week before it is gone.
- **One shared sandbox.** Each user's home is separate, but all users share one sandbox container; see
  [Coding](../6_coding/) for what that means.
