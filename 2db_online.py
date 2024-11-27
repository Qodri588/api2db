import sqlitecloud
import requests

# Konfigurasi API Key dan URL
api_key = "350871o0uomobcm787efod"
base_url = "https://doodapi.com/api"

# Konfigurasi SQLiteCloud
db_url = "sqlitecloud://cob2gqunnz.sqlite.cloud:8860/chinook.sqlite?apikey=GDcfqocXdh3DzHe0GLVFecwcluoTKQFoZhZDf4knjIc"
conn = sqlitecloud.connect(db_url)

# Membuat tabel folders dan files jika belum ada
def setup_database():
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                fld_id TEXT PRIMARY KEY,
                name TEXT,
                parent_id TEXT
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                file_code TEXT PRIMARY KEY,
                title TEXT,
                download_url TEXT,
                single_img TEXT,
                length INTEGER,
                views INTEGER,
                uploaded TEXT,
                fld_id TEXT,
                name TEXT
            );
        """)
        print("Tabel berhasil dibuat atau sudah ada.")
    except Exception as e:
        print("Error membuat tabel:", e)

# Fungsi untuk mengambil list folder dari API Doodstream
def get_folder_list(api_key):
    try:
        url = f"{base_url}/folder/list?key={api_key}&fld_id=0"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Gagal mengambil daftar folder:", e)
        return None

# Fungsi untuk mengambil list file dari folder tertentu
def get_file_list_by_folder(api_key, folder_id):
    try:
        url = f"{base_url}/file/list?key={api_key}&fld_id={folder_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Gagal mengambil daftar file untuk folder {folder_id}:", e)
        return None

# Fungsi untuk menyimpan folder ke database
def save_folder_to_database(fld_id, name, parent_id):
    try:
        conn.execute("""
            INSERT OR IGNORE INTO folders (fld_id, name, parent_id) VALUES (?, ?, ?);
        """, (fld_id, name, parent_id))
        print(f"Folder {name} berhasil disimpan.")
    except Exception as e:
        print(f"Error menyimpan folder {name}:", e)

# Fungsi untuk menyimpan file ke database
def save_file_to_database(file):
    try:
        conn.execute("""
            INSERT OR IGNORE INTO files (file_code, title, download_url, single_img, length, views, uploaded, fld_id, name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            file["file_code"], file["title"], file["download_url"], file["single_img"], 
            file["length"], file["views"], file["uploaded"], file["fld_id"], file["name"]
        ))
        print(f"File {file['title']} berhasil disimpan.")
    except Exception as e:
        print(f"Error menyimpan file {file['title']}:", e)

# Fungsi utama untuk mengumpulkan dan menyimpan data
def main():
    setup_database()
    folder_data = get_folder_list(api_key)

    if not folder_data or folder_data.get("msg") != "OK":
        print("Gagal mengambil folder.")
        return

    for folder in folder_data["result"]["folders"]:
        save_folder_to_database(folder["fld_id"], folder["name"], "0")
        print(f"Folder: {folder['name']}")

        file_data = get_file_list_by_folder(api_key, folder["fld_id"])
        if not file_data or file_data.get("msg") != "OK":
            print(f"Tidak ada file di folder {folder['name']}.")
            continue

        print("- Files:")
        for file in file_data["result"]["files"]:
            save_file_to_database({
                "file_code": file["file_code"],
                "title": file["title"],
                "download_url": file["download_url"],
                "single_img": file["single_img"],
                "length": file["length"],
                "views": file["views"],
                "uploaded": file["uploaded"],
                "fld_id": folder["fld_id"],
                "name": folder["name"]
            })
            print(f"  * {file['title']}")
        print("**************")

if __name__ == "__main__":
    try:
        main()
    finally:
        conn.close()
        print("Koneksi SQLiteCloud ditutup.")
