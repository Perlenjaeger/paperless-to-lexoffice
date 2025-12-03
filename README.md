# paperless-to-lexoffice

This tool allows to synchronize (selected) documents from paperless-ngx unidirectional to lexoffice.

## Prerequisites

You need to prepare some information so that paperless-to-lexoffice is able to connect with both paperless-ngx as well as the lexoffice Public API.

- Make sure your lexoffice plan includes the usage of the Public API. Unfortunately not all plans do so.
- Generate a token in paperless-ngx (the corresponding user must have the rights to view documents and edit tags).
- Generate a token in lexoffice for using the Public API.
- Create one tag in paperless-ngx that indicates that something needs to be done with this document (if not already existing, like e.g., Inbox tag). I am using my "Inbox" tag, but you can create a separate one just for lexoffice inbox if you like.
- Create one tag in paperless-ngx that is used for marking documents that shall be synced with lexoffice (I am using the tag "lexoffice")

## Playwright UI options

Alternatively to using the lexoffice Public API, you can also use the lexware Playwright UI uploader to upload documents to lexoffice via browser automation.

This has the advantage that no special lexoffice plan is required, but the disadvantage that the docker image becomes much larger (because of the Playwright browsers) and that the upload process is slower and more error-prone (because of possible UI changes on lexoffice side).

to activate this option, modify the docker-compose.yml to use the Dockerfile.playwright as dockerfile in the build section (this is already prepared in the provided docker-compose.yml).

also define the lexware username (email address) and password in the .env file and activate the PL2LO_LEXWARE_PASSWORD variable with value "playwright".

### Upload script only

The script lexware_playwright.py can also be used standalone to upload documents to lexoffice via the Playwright UI automation.

## Installation

To install paperless-to-lexoffice, you can use the provided docker-compose files in the docker directory.
Modify the docker-compose.env with your tokens, your paperless-ngx URL as well as the tag ids of the tags mentioned in the prerequisites.

In the directory of docker-compose.yml and docker-compose.env execute:
```
docker-compose up -d
```

## Limitations
This tool is still in a very early development stage and has been used for my own document management only so far.
So feedback is welcome!

## Special thanks
Thanks to the developers of paperless-ngx in the first place. You did and are doing a great job making it so easy to develop simple tools like this to interact with paperless-ngx!
