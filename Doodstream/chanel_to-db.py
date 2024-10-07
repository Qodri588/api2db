import os
import re
import sqlite3
import requests
from bs4 import BeautifulSoup

# Inisialisasi database SQLite
conn = sqlite3.connect('dood.db')
c = conn.cursor()

# Buat tabel jika belum ada
c.execute('''
    CREATE TABLE IF NOT EXISTS chanel (
        chanel TEXT,
        folder TEXT,
        folder_id TEXT,
        link_id TEXT,
        UNIQUE(folder_id, link_id) -- Hindari duplikasi data
    )
''')

# Fungsi untuk mengambil elemen h1 dan link dengan path /e/
def process_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ambil h1
            h1 = soup.find('h1').get_text(strip=True) if soup.find('h1') else ''
            
            # Ambil semua link dengan path /e/
            e_links = [a['href'] for a in soup.find_all('a', href=True) if '/e/' in a['href']]
            
            return h1, e_links
        else:
            return None, []
    except Exception as e:
        return None, []

# Fungsi untuk mengambil folder_id dan link_id dari URL
def extract_id(url, path):
    match = re.search(f'{path}([^/]+)', url)
    return match.group(1) if match else None

# Folder tempat file .txt berada
folder_path = 'chanel'

# Baca setiap file txt di folder
for file_name in os.listdir(folder_path):
    if file_name.endswith('.txt'):
        file_path = os.path.join(folder_path, file_name)
        
        # Buka dan baca isi file
        with open(file_path, 'r') as file:
            content = file.read()
            
            # Cari semua link yang memiliki path /f/
            f_links = re.findall(r'https?://[^\s]+/f/[^\s]+', content)
            
            print(f"\nChanel {file_name.replace('.txt', '')} [{len(f_links)}]")
            
            for f_link in f_links:
                # Ambil folder_id (setelah /f/)
                folder_id = extract_id(f_link, '/f/')
                
                # Ambil h1 dan link dengan path /e/ dari link /f/
                h1, e_links = process_url(f_link)
                
                if h1 and folder_id:
                    print(f"- {h1}")
                    
                    for idx, e_link in enumerate(e_links, start=1):
                        # Ambil link_id (setelah /e/)
                        link_id = extract_id(e_link, '/e/')
                        
                        if link_id:
                            print(f"  - [{idx}] {link_id}")
                            
                            # Simpan data ke SQLite
                            try:
                                c.execute('''
                                    INSERT OR IGNORE INTO chanel (chanel, folder, folder_id, link_id) 
                                    VALUES (?, ?, ?, ?)
                                ''', (file_name.replace('.txt', ''), h1, folder_id, link_id))
                            except Exception as e:
                                print(f"Error inserting data: {e}")

# Commit perubahan dan tutup koneksi database
conn.commit()
conn.close()

print(f"\nProses selesai! Data disimpan di database SQLite.")