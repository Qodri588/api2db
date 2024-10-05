<?php
// Konfigurasi API Key dan URL
$api_key = '350871o0uomobcm787efod';
$base_url = "https://doodapi.com/api";

// Membuat atau membuka database SQLite
$db = new PDO('sqlite:dood.db');
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

// Membuat tabel folders dan files jika belum ada
$db->exec("CREATE TABLE IF NOT EXISTS folders (
    fld_id TEXT PRIMARY KEY,
    name TEXT,
    parent_id TEXT
)");

$db->exec("CREATE TABLE IF NOT EXISTS files (
    file_code TEXT PRIMARY KEY,
    title TEXT,
    download_url TEXT,
    single_img TEXT,
    length INTEGER,
    views INTEGER,
    uploaded TEXT,
    fld_id TEXT,
    name TEXT -- Menambahkan kolom name untuk menyimpan nama folder
)");

// Query untuk menyimpan folder dan file
$folderStmt = $db->prepare("INSERT OR IGNORE INTO folders (fld_id, name, parent_id) VALUES (:fld_id, :name, :parent_id)");
$fileStmt = $db->prepare("INSERT OR IGNORE INTO files (file_code, title, download_url, single_img, length, views, uploaded, fld_id, name) VALUES (:file_code, :title, :download_url, :single_img, :length, :views, :uploaded, :fld_id, :name)");

// Query untuk memeriksa apakah folder sudah ada
$checkFolderStmt = $db->prepare("SELECT fld_id FROM folders WHERE fld_id = :fld_id LIMIT 1");

// Fungsi untuk mengambil list folder dari API Doodstream
function getFolderList($api_key, $base_url) {
    $url = "$base_url/folder/list?key=$api_key&fld_id=0"; // fld_id=0 untuk root folder
    $response = file_get_contents($url);

    // Penanganan error
    if ($response === false) {
        echo "Failed to retrieve folder list.\n";
        return [];
    }
    $data = json_decode($response, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        echo "Failed to decode JSON response: " . json_last_error_msg() . "\n";
        return [];
    }
    return $data;
}

// Fungsi untuk mengambil list file dari folder tertentu
function getFileListByFolder($api_key, $base_url, $folder_id) {
    $url = "$base_url/file/list?key=$api_key&fld_id=$folder_id";
    $response = file_get_contents($url);

    // Penanganan error
    if ($response === false) {
        echo "Failed to retrieve file list for folder $folder_id.\n";
        return [];
    }
    $data = json_decode($response, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        echo "Failed to decode JSON response: " . json_last_error_msg() . "\n";
        return [];
    }
    return $data;
}

// Mulai transaksi database untuk mempercepat proses batch
$db->beginTransaction();

// Mengambil daftar folder dari API
$data = getFolderList($api_key, $base_url);

// Cek apakah respon sukses
if ($data['msg'] === 'OK') {
    // Looping melalui setiap folder
    foreach ($data['result']['folders'] as $folder) {
        // Periksa apakah folder sudah ada di database
        $checkFolderStmt->execute([':fld_id' => $folder['fld_id']]);
        $exists = $checkFolderStmt->fetchColumn();

        if ($exists) {
            // Folder sudah ada di database, lewati
            echo "Folder: " . $folder['name'] . " (already exists)\n";
            continue;
        }

        // Simpan folder ke database tanpa duplikasi
        $folderStmt->execute([
            ':fld_id' => $folder['fld_id'],
            ':name' => $folder['name'],
            ':parent_id' => 0 // Karena ini root folder
        ]);

        // Tampilkan proses ke CLI
        echo "Folder: " . $folder['name'] . "\n";
        echo "- Files:\n";

        // Mengambil list file dari folder tertentu
        $file_data = getFileListByFolder($api_key, $base_url, $folder['fld_id']);

        // Cek apakah ada file yang diambil
        if ($file_data['msg'] === 'OK') {
            foreach ($file_data['result']['files'] as $file) {
                // Simpan file ke database tanpa duplikasi
                $fileStmt->execute([
                    ':file_code' => $file['file_code'],
                    ':title' => $file['title'],
                    ':download_url' => $file['download_url'],
                    ':single_img' => $file['single_img'],
                    ':length' => $file['length'],
                    ':views' => $file['views'],
                    ':uploaded' => $file['uploaded'],
                    ':fld_id' => $file['fld_id'],
                    ':name' => $folder['name'] // Menyimpan nama folder
                ]);

                // Tampilkan nama file di CLI
                echo "  * " . $file['title'] . "\n";
            }
        } else {
            echo "  * No files found\n";
        }

        echo "**************\n";
    }
} else {
    echo "Failed to retrieve folders.\n";
}

// Commit transaksi untuk menyimpan perubahan ke database
$db->commit();

?>
