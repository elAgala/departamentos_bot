import os
import requests
import sqlite3

# Notion API token and database ID
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get("DATABASE_ID")
DB_PATH = os.environ.get('DB_PATH')
NOTIFICATIONS_CHANNEL = os.environ.get("PUSH_NOTIFICATIONS_CHANNEL")

# Headers for authentication and content type
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"  # Keep it updated to the latest version
}


def fetch_notion_id_by_listing_id(listing_id):
    notion_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    # Query the Notion database to find the page with the given listingId
    data = {
        "filter": {
            "and": [
                {
                    "property": "listingId",
                    "number": {
                        "equals": listing_id
                    }
                },
                {
                    "property": "Estado",
                    "select": {
                        "equals": "Activo"
                    }
                }
            ]
        }
    }

    response = requests.post(notion_url, headers=HEADERS, json=data)

    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            return results[0]["id"]  # Return the Notion page ID
        else:
            print(f"No Notion page found for listingId {listing_id}")
            return None
    else:
        print(f"Failed to query Notion: {response.text}")
        return None


def update_apartment_status_in_notion(apartment):
    notion_page_id = fetch_notion_id_by_listing_id(apartment["id"])
    notion_url = f"https://api.notion.com/v1/pages/{notion_page_id}"

    if not notion_page_id:
        return 0

    # Define the data payload
    data = {
        "properties": {
            "Estado": {
                "select": {"name": "Inactivo"}
            }
        }
    }

    # Send the request to Notion API
    response = requests.patch(notion_url, headers=HEADERS, json=data)

    if response.status_code == 200:
        print(f"Updated apartment [{apartment['id']}] to Inactivo in Notion.")
        return 1
    else:
        print(
            f"Failed to update apartment [{apartment['id']}] in Notion: {response.text}")
        return 0


def create_apartment_in_notion(apartment):
    notion_url = "https://api.notion.com/v1/pages"

    # Define the data payload
    data = {
        "parent": {"database_id": DATABASE_ID},
        "cover": {
            "external": {
                "url": apartment['image']
            }
        },
        "icon": {
            "emoji": "🏡"
        },
        "properties": {
            "Direccion": {
                "title": [{"text": {"content": apartment['address']}}]
            },
            "Localidad": {
                "rich_text": [{"text": {"content": apartment['location']}}]
            },
            "Precio": {
                "number": apartment["price"]
            },
            "Expensas": {
                "number": apartment["expenses"]
            },
            "Habitaciones": {
                "number": apartment["rooms"]
            },
            "m2": {
                "number": apartment["m2"]
            },
            "Imagen": {
                "url": apartment['image']
            },
            "Antiguedad": {
                "rich_text": [{"text": {"content": apartment['years']}}]
            },
            "Link": {
                "url": apartment['link']
            },
            "Estado": {
                "select": {"name": "Activo"}
            },
            "listingId": {
                "number": apartment["id"]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {
                        # Embed the image inside the page content
                        "url": apartment['image']
                    }
                }
            }
        ]
    }

    response = requests.post(notion_url, headers=HEADERS, json=data)

    if response.status_code == 200:
        print("Apartment added successfully!")
        return 1
    else:
        print(f"Failed to add apartment: {response.text}")
        return 0


# Function to update the apartment status in the SQLite database
def mark_apartment_as_added(apartment_id):
    if not DB_PATH:
        raise EnvironmentError(
            "DB_PATH environment variable is required but not set.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE listings
        SET is_new = 0
        WHERE id = ?
    """, (apartment_id,))
    conn.commit()
    conn.close()


def fetch_inactive_apartments():
    if not DB_PATH:
        raise EnvironmentError(
            "DB_PATH environment variable is required but not set.")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id
        FROM listings
        WHERE is_active = 0
    """)
    apartments = cursor.fetchall()
    conn.close()
    return [{"id": row[0]} for row in apartments]


def fetch_new_apartments():
    if not DB_PATH:
        raise EnvironmentError(
            "DB_PATH environment variable is required but not set.")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, link, price, expenses, location, address, rooms, m2, years, image
        FROM listings
        WHERE is_new = 1
    """)
    apartments = cursor.fetchall()
    conn.close()
    return apartments


def send_push_notification(total_added, total_inactive):
    if not NOTIFICATIONS_CHANNEL:
        raise EnvironmentError("NOTIFICATIONS_CHANNEL not specified")

    text = ""
    if total_added > 0:
        text = f"Se encontraron {total_added} nuevos departamentos!"
        if total_inactive > 0:
            text += f"\nAdemas, se eliminaron {total_inactive} publicaciones"
    elif total_inactive > 0:
        text = f"Se eliminaron {total_inactive} publicaciones"

    requests.post(
        NOTIFICATIONS_CHANNEL,
        data=text,
        headers={
            "Title": "Alerta departamentos",
            "Tags": "rotating_light"
        }
    )


def main():
    apartments = fetch_new_apartments()
    count = 0

    for apartment in apartments:
        # Map apartment data to a dictionary
        print(apartment)
        apartment_data = {
            "id": apartment[0],
            "link": apartment[1] or "",
            "price": apartment[2] or 0,
            "expenses": apartment[3] or 0,
            "location": apartment[4] or "",
            "address": apartment[5] or "",
            "rooms": apartment[6] or 0,
            "m2": apartment[7] or 0,
            "years": apartment[8] or "",
            "image": apartment[9] or "",
            "is_new": True
        }

        # Create the apartment in Notion
        result = create_apartment_in_notion(apartment_data)

        if result == 1:
            # Mark as added in the SQLite database
            mark_apartment_as_added(apartment_data['id'])
            count += 1

    print(f"FINISH :: Loaded [{count}] new apartments")

    # Fetch inactive apartments
    inactive_apartments = fetch_inactive_apartments()
    count_inactive = 0

    for apartment in inactive_apartments:
        # Update the apartment status in Notion
        count_inactive += update_apartment_status_in_notion(apartment)

    print(
        f"FINISH :: Updated [{count_inactive}] apartments to Inactivo in Notion")

    if count != 0 or count_inactive != 0:
        send_push_notification(count, count_inactive)


# Run the script
if __name__ == "__main__":
    main()
