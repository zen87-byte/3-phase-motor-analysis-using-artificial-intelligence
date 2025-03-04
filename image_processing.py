import cv2
import pytesseract
import numpy as np
import pandas as pd
import re
import os
from tqdm import tqdm

# Konfigurasi path Tesseract (sesuaikan jika perlu)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Fungsi untuk mendapatkan path Desktop pengguna
def get_desktop_path():
    return os.path.join(os.path.expanduser("~"), "Desktop")

# Fungsi untuk preprocessing gambar
def preprocess_image(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Grayscale
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # Thresholding
    kernel = np.ones((2,2), np.uint8)
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)  # Morphological close untuk noise
    return morph

# Fungsi untuk membaca angka dari frame menggunakan OCR
def read_number_from_frame(frame):
    preprocessed = preprocess_image(frame)
    text = pytesseract.image_to_string(preprocessed, config='--psm 6 -c tessedit_char_whitelist=0123456789.')  # Hanya angka & titik
    match = re.search(r'\d+\.\d+|\d+', text)  # Mencari angka desimal atau bilangan bulat
    if match:
        number = float(match.group())  # Konversi ke float
        if 54 <= number <= 56:  # Hanya simpan jika dalam rentang 54-56
            return number
    return None

# Fungsi untuk membaca waktu sampling dari file Excel
def load_sampling_times(file_path):
    df = pd.read_excel(file_path, header=None)  # Membaca file Excel tanpa header
    sampling_times = df.iloc[:, 0].dropna().tolist()  # Ambil nilai dari kolom pertama
    return sorted(sampling_times)  # Pastikan urutan waktu terurut

# Fungsi utama untuk memproses video dengan sampling pada waktu tertentu
def process_video(video_path, sampling_times):
    cap = cv2.VideoCapture(video_path)
    results = []
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Total frame video
    pbar = tqdm(total=frame_count, desc="Processing Video")  # Progress bar

    sampling_index = 0  # Indeks waktu sampling yang sedang ditargetkan
    last_valid_number = None  # Menyimpan angka terakhir yang terbaca
    tolerance = 0.1  # Perbesar toleransi menjadi 100 ms

    while cap.isOpened() and sampling_index < len(sampling_times):
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0  # Waktu dalam detik

        # Periksa apakah timestamp saat ini mendekati salah satu waktu sampling
        if abs(timestamp - sampling_times[sampling_index]) < tolerance:  # Toleransi diperbesar
            number = read_number_from_frame(frame)  # Baca angka dari frame
            if number is not None:
                last_valid_number = number  # Simpan angka terakhir yang valid
            else:
                number = last_valid_number  # Gunakan angka terakhir jika OCR gagal membaca
            
            print(f"Time: {timestamp:.2f}s, Detected Number: {number}")  # Tampilkan hasil di terminal
            results.append((timestamp, number))
            sampling_index += 1  # Pindah ke waktu sampling berikutnya

        pbar.update(1)  # Update progress bar
        cv2.imshow("Frame", frame)  # Tampilkan video yang sedang diproses
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Tekan 'q' untuk keluar
            break

    pbar.close()
    cap.release()
    cv2.destroyAllWindows()

    # Simpan hasil ke CSV di Desktop
    desktop_path = get_desktop_path()
    output_csv = os.path.join(desktop_path, "hasil_sampling_detik.csv")
    df = pd.DataFrame(results, columns=["Timestamp (s)", "Detected Number"])
    df.to_csv(output_csv, index=False)

    print(f"Results saved to {output_csv}")

# Path ke file Excel yang berisi waktu sampling
sampling_file = r"<FILE PATH>"
sampling_times = load_sampling_times(sampling_file)  # Baca waktu sampling dari file Excel

# Jalankan program
video_path = r"<VIDEO PATH>" 
process_video(video_path, sampling_times)
