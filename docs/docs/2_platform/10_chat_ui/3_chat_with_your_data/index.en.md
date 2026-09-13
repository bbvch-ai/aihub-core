---
title: Chat with your Data
---

To upload files click the "More" button.

![Click More Button](../../../../media/open_webui/click_more_button.jpeg)

Then select "Upload Files". In the pop up navigate to the files you want to use and upload them.

![Select Upload Files](../../../../media/open_webui/select_upload_files.jpeg)

After uploading the files write ask a question.

![Ask Question with Files](../../../../media/open_webui/ask_question_with_files.jpeg)

The model will use the files to answer the question.

![Answer Using Files](../../../../media/open_webui/answer_using_files.jpeg)

Click on a reference to view which parts where used to answer the question.

![Click Reference Citation](../../../../media/open_webui/click_reference_citation.jpeg)

The citation gives a clear rundown of the different parts used to generate the answer.

![Citation Details](../../../../media/open_webui/citation_details_displayed.jpeg)

## Attaching files to an agent

Agents read attached files too, and they keep working across turns: attach a second file later in the
conversation and the agent answers from it, while the earlier one stays available for questions that call for
it. Up to 20 files can be attached to one chat.

An agent searches each attachment rather than reading it whole, so it says which attachments it could not
read — a file the upload has not finished indexing, or one that could not be parsed — instead of answering as
if it were never sent.

A knowledge collection attached from the chat is **not** read by an agent. Agents answer from the knowledge
bases configured on their own profile; attach one in the chat and the agent says so rather than ignoring it
silently.
