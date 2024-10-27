# Scratch Pad

- Generic data extraction
  - Won't do structured data extraction
  - Just output plain text and dump it as a bunch of markdown files into a Notion page

## Flow

- Use slackdump to get the slack data into a plain text file. [example](data/C04HSTQAK0S.txt). Integrate this step into the Python main.py script so that the user does not needs to manually run it.
- Use `src/chunking.py` to chunk the slack dump file into smaller chunks. This is to avoid the token limit for the LLM.
- Use `src/structured_extract.py` to extract structured data from the slack dump file. The output of this will be a list of `StakeholderNote` objects defined in [schema.py](src/schema.py).
- Use `src/postprocess.py` to do some post-processing on the extracted data, in particular to add the relevant Slack thread in full text, and map the project name to the project ID.
- Use `src/md_dump.py` to dump all the post-processed data into a bunch of markdown files.

## How to provide reference to the slack thread for the note

So every message starts with a fingerprint like this > Quintus [U03HT20PJES] @ 02/03/2024 02:51:07 Z:

I just added this as a field in the StakeholderNote schema.

```py
relevant_slack_threads: List[str] = Field(
    description="A list of unique identifiers for Slack threads related to this note. Each identifier should be in the format 'Username [UserID] @ Timestamp'. For example: 'Quintus [U03HT20PJES] @ 16/03/2024 14:09:39 Z:'"
)
```

It is quite shocking to me that this basically just works.

Then after extraction I can just go back to the Slack chat history and use the fingerprint to find the original thread to add it.

Of course, to efficiently do this I still need to set up a mapping that effectively map the fingerprint to the actual Slack thread text.
