import sqlite3
import sys
import csv
from app import get_db, app

def print_banner():
    print("=======================================")
    print("Cutlist - Terminal Management")
    print("=======================================")

def list_links(cur):
    cur.execute('SELECT id, short_code, original_url, clicks FROM urls ORDER BY created_at DESC')
    urls = cur.fetchall()
    if not urls:
        print("No links found.")
        return
    
    print(f"{'ID':<5} | {'Code':<8} | {'Clicks':<8} | {'URL'}")
    print("-" * 50)
    for u in urls:
        print(f"{u['id']:<5} | {u['short_code']:<8} | {u['clicks']:<8} | {u['original_url'][:30]}...")

def delete_link(cur, conn):
    link_id = input("Enter the ID of the link to delete: ")
    try:
        cur.execute('DELETE FROM clicks WHERE url_id = ?', (link_id,))
        cur.execute('DELETE FROM urls WHERE id = ?', (link_id,))
        conn.commit()
        print("Link and associated analytics deleted successfully.")
    except Exception as e:
        print("Error deleting link:", e)

def view_stats(cur):
    short_code = input("Enter the short code to view stats: ")
    cur.execute('SELECT * FROM urls WHERE short_code = ?', (short_code,))
    url_row = cur.fetchone()
    
    if not url_row:
        print("Oops! Short code not found.")
        return
        
    print(f"\nStats for: {short_code}")
    print(f"Original URL: {url_row['original_url']}")
    print(f"Total Clicks: {url_row['clicks']}")
    print(f"Created At:   {url_row['created_at']}")
    print(f"Last Access:  {url_row['last_accessed'] or 'Never'}")
    
    cur.execute('SELECT country, city, referrer, click_time FROM clicks WHERE url_id = ? ORDER BY click_time DESC LIMIT 5', (url_row['id'],))
    clicks = cur.fetchall()
    
    if clicks:
        print("\nRecent 5 clicks:")
        for c in clicks:
            print(f" - {c['click_time']} | {c['country']}/{c['city']} | Referrer: {c['referrer']}")
    else:
        print("\nNo detailed click data available.")

def export_csv(cur):
    cur.execute('SELECT id, short_code, original_url, clicks, created_at FROM urls')
    urls = cur.fetchall()
    if not urls:
        print("No links to export.")
        return
        
    filename = "cutlist_export.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Short Code', 'Original URL', 'Clicks', 'Created At'])
        for u in urls:
            writer.writerow([u['id'], u['short_code'], u['original_url'], u['clicks'], u['created_at']])
            
    print(f"Exported successfully to {filename}")

def main():
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        
        while True:
            print_banner()
            print("1. List all links")
            print("2. Delete a link")
            print("3. View stats for a link")
            print("4. Export links to CSV")
            print("5. Exit")
            
            choice = input("Select an option: ")
            
            if choice == '1':
                list_links(cur)
            elif choice == '2':
                delete_link(cur, conn)
            elif choice == '3':
                view_stats(cur)
            elif choice == '4':
                export_csv(cur)
            elif choice == '5':
                print("Bye!")
                break
            else:
                print("Invalid choice, try again.")
            print()

if __name__ == "__main__":
    main()
