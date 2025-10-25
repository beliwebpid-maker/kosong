import sys
import os
import requests
import subprocess
from urllib.parse import urlparse
from tqdm import tqdm  # Impor library progress bar

def download_file(url, filename):
    """Downloads a file from a URL with a tqdm progress bar."""
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            
            # Dapatkan total ukuran file dari header
            total_size = int(r.headers.get('content-length', 0))
            
            # Tentukan ukuran chunk
            chunk_size = 8192
            
            print(f"Starting download: {filename}")
            
            # Konfigurasi progress bar (tqdm)
            with tqdm(
                total=total_size, 
                unit='B',            # Satuan adalah Byte
                unit_scale=True,     # Tampilkan sbg KB, MB, GB
                unit_divisor=1024,   # Pembaginya 1024
                desc="Downloading"   # Label di depan bar
            ) as bar:
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        f.write(chunk)
                        bar.update(len(chunk)) # Update progress bar
            
            # Cek jika ukuran download tidak sesuai (jika server menyediakan info)
            if total_size != 0 and bar.n != total_size:
                print(f"Error: Download size mismatch. Expected {total_size}, got {bar.n}")
                return False

        print(f"Download complete: {filename}\n") # Beri baris baru
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return False
    except IOError as e:
        print(f"Error writing file to disk: {e}")
        return False

def upload_to_rclone(filename, remote_name):
    """Uploads a file to the specified rclone remote."""
    # Note: Progress bar untuk upload sudah otomatis dari rclone
    remote_destination = f"{remote_name}:"
    command = ['rclone', 'copy', filename, remote_destination, '--progress']
    
    try:
        print(f"Uploading: {filename} to {remote_destination}")
        subprocess.run(command, check=True)
        print(f"\nUpload complete: {filename}") # Beri baris baru
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during rclone upload: {e}")
        return False
    except FileNotFoundError:
        print("Error: 'rclone' command not found.")
        print("Pastikan rclone terinstal dan ada di PATH sistem Anda.")
        return False

def main():
    # 1. Minta URL (Hanya URL)
    url = input("Masukkan URL: ").strip()
    if not url:
        print("URL tidak boleh kosong.")
        sys.exit(1)

    # 2. Remote rclone di-set otomatis (hardcoded)
    remote_name = "gdrive"
    print(f"Target remote Rclone: {remote_name}:")
    
    # 3. Ekstrak nama file
    filename = "" 
    try:
        path = urlparse(url).path
        # ----- INI YANG DIPERBAIKI -----
        filename = os.path.basename(path) 
        # -----------------------------
        if not filename:
            print("Error: Tidak dapat menentukan nama file dari URL.")
            sys.exit(1)
    except Exception as e:
        print(f"Error parsing URL: {e}")
        sys.exit(1)

    # 4. Proses Inti (Download & Upload)
    try:
        if download_file(url, filename):
            upload_to_rclone(filename, remote_name)
        else:
            print("Download failed, skipping upload.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
    finally:
        # 5. Auto-Delete (Selalu Dijalankan)
        print("-" * 20)
        print("Running cleanup (auto-delete)...")
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"Successfully deleted local file: {filename}")
            except OSError as e:
                print(f"Error deleting local file: {e}")
        else:
            print(f"Local file '{filename}' not found, no cleanup needed.")
        print("-" * 20)

if __name__ == "__main__":
    main()
