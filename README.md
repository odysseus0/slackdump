# Scratch Pad

- Data
  - Still need to select all the channels I need to scrap
  - There is a specific requirement from Mateusz so make a custom prompt for him
  - For everyone else, use a generic prompt
- Market research
  - Start testing structured data extraction
  - Need to have a pipeline for adding entries (blob of markdown text) as a page to a Notion database.
    - I do need to get a table that is basically (project name, Notion page ID), so that I can map project name extracted from the structured data to the actual Notion page to add it.
    - The pipeline should take a blob of markdown text and project name as input and then create a new page in Notion's Stakeholder DB that is properly linked to the right project entry in the CRM DB.
  - Will not for now worry too much about deduplication. If the note happen to be there, someone who found it could just easily delete it anyway. So not really that big of an issue.
- Generic data extraction
  - Won't do structured data extraction
  - Just output plain text and dump it as a bunch of markdown files into a Notion page

## Flow

- Use slackdump to get the slack data into a plain text file. [example](data/C04HSTQAK0S.txt).
- Use reverse engineering tricks to get the stakeholder CRM database structure into a [JSON file](data/stakeholder_crm.json), which would contain both the page ID and the page name.
- Use `src/extract_page_id_mapping.py` to get the mapping of page name to ID. Described in [Get Project name <> ID mapping](#get-project-name--id-mapping).
- Use `src/chunking.py` to chunk the slack dump file into smaller chunks. This is to avoid the token limit for the LLM.
- Use `src/structured_extract.py` to extract structured data from the slack dump file. The output of this will be a list of `StakeholderNote` objects defined in [schema.py](src/schema.py).
- Use `src/postprocess.py` to do some post-processing on the extracted data, in particular to add the relevant Slack thread in full text, and map the project name to the project ID.
- Use `src/notion.py` to add the post-processed data into the stakeholder CRM.

## Get Project name <> ID mapping

- To properly link the stakeholder note to the right project in the CRM, I need the mapping of project name to ID.
- This I unfortunately have to get in a super hacky way.
  - Again as a callback, it is not possible to directly use the Notion API as I don't have the integration token not being the owner of the workspace. It would also introduce too much OpSec issues if I request to have it as it will allow me to access too much information.
  - Notion does allow you to do account based OAuth flow inside 3rd party integration that is already developed, like Zapier and Pipedream. You will be able to access the data you have access to in Notion.
  - However, the API provided there is still very limited and often does not work. For example, there is a retrieve content from DB API, but it could only get max 100 rows from the DB with no way to increase the limit or do pagination. The Stakeholder DB I am trying to access has around 500 rows so it won't work.
  - In the end I have to reverse engineer the internal API used by Notion inside the browser.

```bash
curl 'https://www.notion.so/api/v3/queryCollection?src=initial_load' \
  -H 'accept: */*' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H 'content-type: application/json' \
  -H 'cookie: intercom-device-id-gpfdrxfd=757c7900-a501-4a83-8dc7-fd4c2d98f9b7; notion_browser_id=45ff7b08-258a-46c2-bf82-853a1d8326d1; NEXT_LOCALE=en-US; token_v2=v02%3Auser_token_or_cookies%3AxtWxPm1qEqg5UKpF4YAz8Ww8CDm2FHNFXdWK5j4w9tfbtyZDcQJeR12yHZ50gM414GBiipYHK-K-9rcanFHzPlsQCuwLXEJy7cPSy-ZmxUneUnc6n-3316iJZEgYIa4gYxip; notion_user_id=d7c12816-b193-4136-9761-b82c26cecc68; notion_users=[%22d7c12816-b193-4136-9761-b82c26cecc68%22]; notion_cookie_consent={%22id%22:%2236d95e96-d414-44ab-9ef5-40b275618520%22%2C%22permission%22:{%22necessary%22:true%2C%22targeting%22:true%2C%22preference%22:true%2C%22performance%22:true}%2C%22policy_version%22:%22v9%22}; device_id=0b56d3f0-f854-49d6-b381-130d5f1cd14b; AMP_6745a3116e=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJmZWUxMzRlNi1mNjg3LTQ1ODctOTQ4Yi0yZmY4MDc0OGQwNGMlMjIlMkMlMjJ1c2VySWQlMjIlM0ElMjI4MjMwNTAzNC1kMGU4LTRlM2MtODg4Yi01ZTI5MGNmZjdkNmElMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzA4ODk2NDQ2NTE5JTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTcwODg5NjYwNDQwMSUyQyUyMmxhc3RFdmVudElkJTIyJTNBMTIlN0Q=; p_sync_session=%7B%22tokenId%22%3A%22v02%3Async_session%3AbmdSEfN0CiK64qMWSQ5pEAwA1qhrQaAJKAPyrm0vkVzHjVVqYNN5sBAA_rytawc6x84NTSj7Hzrz0404vjk_t8LRxUg0rysd6tQTPZlnYYsvGw12IuXdmlxs8tFnocE1V6n0%22%2C%22userIds%22%3A%5B%22d7c12816-b193-4136-9761-b82c26cecc68%22%5D%7D; amp_af43d4=45ff7b08258a46c2bf82853a1d8326d1.ZDdjMTI4MTZiMTkzNDEzNjk3NjFiODJjMjZjZWNjNjg=..1i86he6cr.1i86he6cr.20.3.23; notion_check_cookie_consent=false; notion_cookie_sync_completed=%7B%22completed%22%3Atrue%2C%22version%22%3A4%7D; __cf_bm=1SoGGssdFP1xtLTnwO_E.KAKTWExc1NuZwcyv9tKKRw-1727701449-1.0.1.1-KvraHJ_MVrHU4MiStYxmtb7Ids1lrs0dsHWB7O.RGYyqcZqShueBAUpcyP.l5VKCBj9Y4NJhRDM_tJyDkpR7_Q; _cfuvid=iLttH1Db9oy12mDjTJnNZw3U1RbQfazNAJuvdOxpMME-1727701449444-0.0.1.1-604800000; amp_unused=45ff7b08258a46c2bf82853a1d8326d1.ZDdjMTI4MTZiMTkzNDEzNjk3NjFiODJjMjZjZWNjNjg=..1i91fh7bv.1i91h1nlm.7e.2.7g; notion_locale=en-US%2Flegacy' \
  -H 'dnt: 1' \
  -H 'notion-audit-log-platform: web' \
  -H 'notion-client-version: 23.13.0.471' \
  -H 'origin: https://www.notion.so' \
  -H 'priority: u=1, i' \
  -H 'referer: https://www.notion.so/flashbots/4e31c9295f344ab1af32085bc62e7c9e?v=6f411326dd7d42aaaf115e0b6352246c' \
  -H 'sec-ch-ua: "Chromium";v="129", "Not=A?Brand";v="8"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36' \
  -H 'x-notion-active-user-header: d7c12816-b193-4136-9761-b82c26cecc68' \
  --data-raw '{"source":{"type":"collection","id":"1f6e6757-34a9-46d2-9698-50ca285396dd","spaceId":"df6156be-4a40-4dc3-9a41-d3def62df57a"},"collectionView":{"id":"6f411326-dd7d-42aa-af11-5e0b6352246c","spaceId":"df6156be-4a40-4dc3-9a41-d3def62df57a"},"loader":{"reducers":{"collection_group_results":{"type":"results","limit":50}},"sort":[],"searchQuery":"","userId":"d7c12816-b193-4136-9761-b82c26cecc68","userTimeZone":"Asia/Kuala_Lumpur"},"aggregationStatus":"stripped"}'
```

After simplification, the minimal request you need to make it work is just this:

```bash
curl 'https://www.notion.so/api/v3/queryCollection' \
  -H 'content-type: application/json' \
  -H 'cookie: token_v2=YOUR_TOKEN;' \
  --data-raw '{
  "source": {
    "type": "collection",
    "id": "1f6e6757-34a9-46d2-9698-50ca285396dd",
    "spaceId": "df6156be-4a40-4dc3-9a41-d3def62df57a"
  },
  "collectionView": {
    "id": "6f411326-dd7d-42aa-af11-5e0b6352246c",
    "spaceId": "df6156be-4a40-4dc3-9a41-d3def62df57a"
  },
  "loader": {
    "reducers": {
      "collection_group_results": { "type": "results", "limit": 50 }
    }
  }
}'
```

Good thing is that to make it work I actually do not even need to do any pagination. I just increased the limit to 500 and it worked.

The response is of course still quite noisy (check out `data/stakeholder_crm.json`), and it is a bit too big to just stuff it into LLM to ask it to figure out for me what is needed. So I have to use a JSON visualizer to look at the path needed to extract the data I need.

I just used a quite popular tool <https://codebeautify.org/jsonviewer> to look at the data. After poking around for a bit, I found the path I need is basically:

`recordMap -> block -> [block_id] -> value -> value -> properties -> title -> [0] -> [0]`

Then I can just write a small script to extract it, which I did in `src/extract_page_id_mapping.py`.

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

## Pipedream Notion API limit testing

- For each block, it can handle at least 1000 words.
- For the number of blocks
  - The behavior is also quite interesting. I am watching the page live and it seems that it is adding like 100 blocks each time. Maybe that is the max number of blocks each call of Notion API can handle. Then Pipedream is basically just separating it into multiple calls.
  - So it seems that Pipedream can keep going for quite long. It managed to successfully add a page with 1000 blocks.
  - It did time out at 400 blocks for a previous attempt. But after I increased the timeout limit, it was able to successfully add a page with 1000 blocks.
  - Of course I could continue to push the limit by increasing the timeout and the number of blocks. But 1000 blocks seem to be sufficient for now. I don't expect to have single note with more than 1000 paragraphs.
- Okay, I probably also should test total word count. But I will just move on to the next step.
- Since we don't know exactly the limit of API, it could be the case that it starts failing when it hits certain thresholds in production. Because of this, I will do logging properly so that I can easily check which request is failing.

## Performance Optimization

- The most significant improvement would be to implement parallel processing and asynchronous I/O operations. This can be achieved using Python's asyncio library and aiohttp for asynchronous HTTP requests.
- Structured Extraction ([structured_extract.py](src/structured_extract.py)):
  - Implement concurrency using semaphore to process multiple chunks concurrently.
  - Use backoff to handle rate limiting and other potential issues.
- Notion Integration ([notion.py](src/notion.py)):
  - Implement asynchronous HTTP requests using aiohttp.
  - Batch Notion page creations to reduce the number of API calls.
