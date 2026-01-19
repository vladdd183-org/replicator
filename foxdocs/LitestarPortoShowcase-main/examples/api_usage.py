"""Example of API usage."""

import asyncio
import httpx


async def main():
    """Example API calls."""
    base_url = "http://localhost:8000/api"
    
    async with httpx.AsyncClient() as client:
        # Create a book
        print("Creating a book...")
        book_data = {
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
            "isbn": "9780743273565",
            "description": "A classic American novel",
            "is_available": True
        }
        
        response = await client.post(f"{base_url}/books", json=book_data)
        if response.status_code == 200:
            created_book = response.json()
            book_id = created_book["id"]
            print(f"Created book: {created_book}")
        else:
            print(f"Error creating book: {response.text}")
            return
        
        # List all books
        print("\nListing all books...")
        response = await client.get(f"{base_url}/books")
        if response.status_code == 200:
            books = response.json()
            print(f"Found {len(books)} books")
            for book in books:
                print(f"  - {book['title']} by {book['author']}")
        
        # Get a specific book
        print(f"\nGetting book {book_id}...")
        response = await client.get(f"{base_url}/books/{book_id}")
        if response.status_code == 200:
            book = response.json()
            print(f"Book details: {book}")
        
        # Update the book
        print(f"\nUpdating book {book_id}...")
        update_data = {
            "description": "A masterpiece of American literature",
            "is_available": False
        }
        response = await client.patch(f"{base_url}/books/{book_id}", json=update_data)
        if response.status_code == 200:
            updated_book = response.json()
            print(f"Updated book: {updated_book}")
        
        # Delete the book
        print(f"\nDeleting book {book_id}...")
        response = await client.delete(f"{base_url}/books/{book_id}")
        if response.status_code == 204:
            print("Book deleted successfully")


if __name__ == "__main__":
    asyncio.run(main())
