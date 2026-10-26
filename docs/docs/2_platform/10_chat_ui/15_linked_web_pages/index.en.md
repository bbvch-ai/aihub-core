---
title: Linked web pages
description: Agents read the web pages you link in a message, answer from them and cite them, and tell you which pages they could not read.
---

# Linked web pages

Paste a link into a message to an agent, or attach a page with `#`, and the agent reads the page and answers from it.
Every page it used is cited as a source, and a page it could not read is named in the answer, with the reason, instead
of being guessed at.

::: tip Not the same as web search
Here you choose the pages. [Web search](../5_websearch/) lets a plain model chat look for pages itself and is not
offered on agents.
:::

## Which agents read links

Reading links is a setting per agent profile, **off by default**: an admin turns on **Read Linked Web Pages** in the
profile. It is available on the Instructed Assistant, the Document Intelligence Assistant, the Company Knowledge Agent
and the Universal Agent. The [Web Page Assistant](../../5_agents/15_web_page_assistant/) always reads links; that is
what it is for.

## Linking pages

Two ways, read the same way:

- **Paste the link** anywhere in your message: `What does https://example.com/pricing say about discounts?` Every link
  in the message is read, up to the profile's limit (5 by default), not just the first.
- **Attach it with `#`**: type `#`, paste the address and pick it. The page shows as an attachment above the message,
  and the link stays out of the message text.

Only `http://` and `https://` links are read.

## What you see

While the pages load, the chat shows **Reading the linked web pages**. When they are read, the status changes to **Read
3 web pages** (or however many), each page appears as a source with its title and address, and the answer cites the
pages it used with numbered chips. The agent's event history and trace list the pages read and the ones that failed.

## When a page cannot be read

The status names the links that failed, for example **Could not read: https://example.com/members**, and the answer says
which pages it could not read and suggests pasting their text into the chat. It does not describe a page it did not
read.

| Reason                      | What it means                                                                     |
| --------------------------- | --------------------------------------------------------------------------------- |
| Not a valid web address     | The link is malformed.                                                            |
| Not an http or https link   | Other schemes, such as `ftp:` or `file:`, are never opened.                       |
| Internal or private address | The link points into a private network, such as an intranet address. See below.   |
| Page does not exist         | The site answered 404 or 410.                                                     |
| Access refused              | A login, a paywall or bot protection stood in the way (401, 403, 429, 451).       |
| Site error                  | Any other error answer from the site.                                             |
| Took too long               | The page did not load within the profile's time limit (15 seconds by default).    |
| Not a web page              | The link leads to a PDF, an image or a download. Attach the file instead.         |
| No readable text            | The page loaded but had no main text, as with many video and app pages.           |
| Over the link limit         | The message has more links than the profile reads at once; the rest are not read. |

::: warning When Open WebUI cannot fetch a `#` page
Open WebUI loads a page attached with `#` itself as soon as you pick it. If that fails, Open WebUI shows its own error
and drops the attachment, so the agent never sees it. Paste the link into the message instead; the agent then reads it
and reports any failure itself.
:::

## When reading links is off

An agent whose profile does not read links does not open them and shows no reading status. If your question depends on a
linked page, it says that it cannot open links and asks you to paste the page's text.

## On the Universal Agent

The Universal Agent decides for itself whether it needs a page. It may read **only the pages you linked**: if the model
tries to open any other address, such as a link it found inside a page, the call is refused. This keeps an instruction
hidden in a page or a file from sending your conversation to a site of its choosing.

## Limits

Pages are read before the answer starts and go into the model's prompt, so each one adds to the time and cost of the
answer. A profile sets how many links one message may have read, how long one page may take, and how much of a page the
model receives (20,000 characters by default, about 5,000 tokens; a longer page is cut at a paragraph break). Several
long pages make a large prompt, and some models answer large prompts noticeably more slowly.

## Security

- **Internal addresses are refused.** Every request a page makes, redirects and the files it loads included, is checked
  first, and addresses in private networks or with internal names are refused.
- **The browser is isolated.** Pages are loaded by the platform's own browser service, which sits in a network zone of
  its own and cannot reach the platform's internal services. See
  [Network isolation](../../2_architecture/4_network_isolation/).
- **Pages are untrusted.** The model is told to use what a page says as information only and never to follow
  instructions written in it.
- **Every fetch is traced.** Which pages were read, and which failed and why, is recorded in the agent's events and in
  the trace.
