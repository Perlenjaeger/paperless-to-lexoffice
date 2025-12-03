import paperless
import lexoffice
import lexware_playwright
import os
import asyncio

# Config

polling_interval = int(os.getenv("PL2LO_POLLING_INTERVAL_S"))

# paperless-ngx
paperless_token = os.getenv('PL2LO_PAPERLESS_TOKEN')
paperless_url = os.getenv('PL2LO_PAPERLESS_URL')
inbox_tag_id = os.getenv('PL2LO_INBOX_TAG_ID')
lexoffice_tag_id = os.getenv('PL2LO_LEXOFFICE_TAG_ID')

# lexoffice
lexoffice_token = os.getenv('PL2LO_LEXOFFICE_TOKEN')
lexoffice_url = os.getenv('PL2LO_LEXOFFICE_URL')
upload_provider = os.getenv('PL2LO_UPLOAD_PROVIDER', 'lexware_api')
lexware_username = os.getenv('PL2LO_LEXWARE_USERNAME')
lexware_password = os.getenv('PL2LO_LEXWARE_PASSWORD')

# Helper files and directories
tmp_dir = "tmp"
LOCK_FILE = 'script.lock'

def create_lock():
    """Create a lock file."""
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

def remove_lock():
    """Remove the lock file."""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def is_locked():
    """Check if the lock file exists."""
    return os.path.exists(LOCK_FILE)

async def sync_paperless_to_lexoffice():
    if is_locked():
        print("Script is already running. Exiting.")
        return
    
    # Create the lock file
    create_lock()

    try:
        # Your main script logic here
        print("Check for new documents in paperless-ngx tagged for upload...")
        print(f"Using upload provider: {upload_provider}")
        #document_ids = paperless.search_documents(paperless_token, paperless_url, search_string)
        document_ids = paperless.filter_documents_by_tags(paperless_token, paperless_url, [inbox_tag_id, lexoffice_tag_id])

        # None type if error occurred (e.g., paperless-ngx not reachable)
        if document_ids is not None:

            # Download PDFs into temp folder

            for id in document_ids:
                file_content = paperless.download_document(paperless_token, paperless_url, id)
                filepath = os.path.join(tmp_dir, f"{id}.pdf")

                with open(filepath, "wb") as file:
                    file.write(file_content)

                # Upload PDF to lexoffice or lexware depending on env
                if upload_provider == 'playwright':
                    try:
                        response = await lexware_playwright.upload_voucher(lexware_username, lexware_password, filepath)
                    except Exception as e:
                        # If Playwright raised a DocumentUploadError or other error, treat as upload failed
                        print(f"Upload via lexware_playwright failed: {e}")
                        response = None
                else:
                    response = lexoffice.upload_voucher(lexoffice_token, lexoffice_url, filepath)

                # Upload successful
                if response.status_code == 202:
                    print("Upload successful. Deleting file from tmp...")
                    os.remove(filepath)
                    
                    paperless.remove_tag(paperless_token, paperless_url, id, [inbox_tag_id])

                # Upload failed    
                else:
                    print(f"Upload not successful. Leave file in tmp. HTTP error {response.status_code}")
        
    
    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Ensure the lock file is removed even if an error occurs
        remove_lock()

async def periodic_main(interval_seconds):
    while True:
        await sync_paperless_to_lexoffice()
        await asyncio.sleep(interval_seconds)

def main():
    os.makedirs(tmp_dir, exist_ok=True)
    asyncio.run(periodic_main(polling_interval))



if __name__ == "__main__":
    main()