# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import sqlite3
import os

DB_PATH = os.environ.get('DB_PATH')


class ArgenpropPipeline:
    def process_item(self, item, spider):
        return item


class SQLitePipeline:
    def open_spider(self, spider):
        # Initialize the database connection and cursor
        if not DB_PATH:
            raise EnvironmentError(
                "DB_PATH environment variable is required but not set."
            )

        self.connection = sqlite3.connect(DB_PATH)
        self.cursor = self.connection.cursor()

        # Create the table if it doesn't exist
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT,
                price INTEGER,
                expenses INTEGER,
                location TEXT,
                address TEXT,
                rooms INTEGER,
                m2 INTEGER,
                years TEXT,
                image TEXT,
                is_new BOOLEAN,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        self.current_links = set()

    def process_item(self, item, spider):
        self.current_links.add(item.get("link"))

        # Check if the link already exists in the database
        self.cursor.execute(
            "SELECT 1 FROM listings WHERE link = ?", (item.get("link"),))
        existing_item = self.cursor.fetchone()

        if existing_item:
            # If the link exists, we skip inserting this item (duplicate)
            return item  # This prevents the item from being processed further

        # Insert the scraped item into the database if the link is not found
        self.cursor.execute("""
            INSERT INTO listings (link, price, expenses, location, address, rooms, m2, years, image, is_new)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("link"),
            item.get("price"),
            item.get("expenses"),
            item.get("location"),
            item.get("address"),
            item.get("rooms"),
            item.get("m2"),
            item.get("years"),
            item.get("image"),
            True
        ))
        self.connection.commit()  # Commit after each insert
        return item

    def close_spider(self, spider):
        # Update database to detect inactive listings
        self.cursor.execute("""
            UPDATE listings
            SET is_active = 0
            WHERE link NOT IN ({})
        """.format(",".join(["?"] * len(self.current_links))), tuple(self.current_links))

        # Commit changes and close the database connection
        self.connection.commit()
        self.connection.close()
