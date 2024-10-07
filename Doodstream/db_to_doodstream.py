import sqlite3
import requests
import json

# Fungsi untuk membuat folder di DoodStream (dengan pengecekan nama folder)
def create_folder(api_key, folder_name):
    url = f"https://doodapi.com/api/folder/create?key={api_key}&name={folder_name}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == 200:
        print(f"Folder '{folder_name}' berhasil dibuat dengan fld_id: {data['result']['fld_id']}")
        return data['result']['fld_id']
    elif data['msg'] == "Folder already exists":
        print(f"Folder '{folder_name}' sudah ada.")
        return None
    else:
        print(f"Gagal membuat folder '{folder_name}', Pesan: {data['msg']}")
        return None

# Fungsi untuk melakukan remote upload link_id ke dalam folder
def remote_upload(api_key, link_id, fld_id):
    upload_url = f"https://doodapi.com/api/upload/url?key={api_key}&url=https://dood.li/e/{link_id}&fld_id={fld_id}"
    response = requests.get(upload_url)
    data = response.json()
    if data['status'] == 200:
        print(f"Link '{link_id}' berhasil di-upload ke folder ID: {fld_id}")
    else:
        print(f"Gagal upload link '{link_id}', Pesan: {data['msg']}")

# Fungsi utama untuk proses remote upload berdasarkan data di database
def process_uploads(api_key, db_path):
    # Koneksi ke database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Eksekusi query untuk mengambil semua data dari tabel chanel
    query = "SELECT folder, link_id FROM chanel"
    cursor.execute(query)
    rows = cursor.fetchall()

    # Buat dictionary untuk mengelompokkan link_id berdasarkan folder
    folder_dict = {}
    for row in rows:
        folder, link_id = row
        if folder in folder_dict:
            folder_dict[folder].append(link_id)
        else:
            folder_dict[folder] = [link_id]

    # Lakukan upload berdasarkan folder
    created_folders = {}  # Menyimpan folder yang sudah dibuat beserta fld_id
    for folder_name, link_ids in folder_dict.items():
        # Jika folder belum dibuat, buat folder
        if folder_name not in created_folders:
            fld_id = create_folder(api_key, folder_name)
            if fld_id:
                created_folders[folder_name] = fld_id  # Simpan fld_id
        else:
            fld_id = created_folders[folder_name]  # Gunakan fld_id yang sudah ada

        # Lakukan remote upload link_id ke folder yang sesuai
        if fld_id:
            for link_id in link_ids:
                remote_upload(api_key, link_id, fld_id)

    # Tutup koneksi ke database
    conn.close()

# Contoh penggunaan fungsi dengan API key dan path database
api_key = "350871o0uomobcm787efod"
db_path = "dood.db"
process_uploads(api_key, db_path)
