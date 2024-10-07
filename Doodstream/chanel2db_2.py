import sqlite3
import http.client
import json
from urllib.parse import urlencode

# Fungsi untuk membuat folder di DoodStream (dengan pengecekan nama folder)
def create_folder(api_key, folder_name):
    conn = http.client.HTTPSConnection("doodapi.com")
    params = urlencode({'key': api_key, 'name': folder_name})
    url = f"/api/folder/create?{params}"
    conn.request("GET", url)
    response = conn.getresponse()
    data = response.read().decode()
    data = json.loads(data)
    conn.close()
    
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
def remote_upload(api_key, link_id, fld_id, folder_name, cursor, conn):
    conn_api = http.client.HTTPSConnection("doodapi.com")
    params = urlencode({'key': api_key, 'url': f"https://dood.li/e/{link_id}", 'fld_id': fld_id})
    url = f"/api/upload/url?{params}"
    conn_api.request("GET", url)
    response = conn_api.getresponse()
    data = response.read().decode()
    data = json.loads(data)
    conn_api.close()
    
    # Simpan hasil upload ke database
    if data['status'] == 200:
        status = 'success'
        message = 'Upload berhasil'
        print(f"Link '{link_id}' berhasil di-upload ke folder ID: {fld_id}")
    else:
        status = 'failed'
        message = data.get('msg', 'Unknown error')
        print(f"Gagal upload link '{link_id}', Pesan: {message}")
    
    # Simpan hasil ke tabel uploaded
    cursor.execute("INSERT INTO uploaded (link_id, folder_name, fld_id, status, message) VALUES (?, ?, ?, ?, ?)", 
                   (link_id, folder_name, fld_id, status, message))
    conn.commit()

# Fungsi utama untuk proses remote upload berdasarkan data di database
def process_uploads(api_key, db_path):
    # Koneksi ke database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Pastikan tabel 'uploaded' ada, jika belum buat tabelnya
    cursor.execute('''CREATE TABLE IF NOT EXISTS uploaded (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        link_id TEXT,
                        folder_name TEXT,
                        fld_id TEXT,
                        status TEXT,
                        message TEXT)''')
    
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
                remote_upload(api_key, link_id, fld_id, folder_name, cursor, conn)

    # Tutup koneksi ke database
    conn.close()

# Contoh penggunaan fungsi dengan API key dan path database
api_key = "350871o0uomobcm787efod"
db_path = "dood.db"
process_uploads(api_key, db_path)
