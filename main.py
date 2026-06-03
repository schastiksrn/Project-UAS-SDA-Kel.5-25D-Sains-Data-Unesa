import sys
from datetime import datetime, timedelta
from collections import deque 
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
                             QTimeEdit, QComboBox, QGroupBox)
from PySide6.QtCore import Qt, QTime
import pandas as pd
import os

FILE_RUANG = r'ruang.csv'

# data kelas+ruang kalau 'FILE_RUANG' belum ada 
dataruangotomatis = pd.DataFrame({
    'kode_ruang': ['E2.01.02', 'E2.01.04', 'E2.01.05', 'E2.01.06', 'E2.01.07', 
                   'E2.01.08', 'E2.01.09', 'E2.01.10', 'E2.02.01'],
    'nama_ruang': ['Ruang Kelas', 'Ruang Kelas', 'Ruang Kelas', 'Ruang Kelas', 'Ruang Kelas',
                   'Ruang Kelas', 'Ruang Kelas', 'Ruang Kelas', 'LAB Analisis Data']
})

def buat_file_ruang_jika_belum_ada():
    if not os.path.exists(FILE_RUANG):
        dataruangotomatis.to_csv(FILE_RUANG, index=False, encoding='utf-8')

class SistemReservasiFCFS(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistem Reservasi Ruang Kelas - Logika FCFS") 
        self.setMinimumSize(900, 600)
        
        self.daftar_ruang = []
        self.antrian_reservasi = deque()  # ← Queue
        self.daftar_reservasi = []  # Untuk tampilan tabel
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout_utama = QVBoxLayout(self.central_widget)
        
        self.setup_ui_input_reservasi()
        self.setup_ui_tabel()
        
        buat_file_ruang_jika_belum_ada()
        self.load_ruang_dari_file(FILE_RUANG)
        
        self.btn_proses = QPushButton("Jalankan Algoritma FCFS")
        self.btn_proses.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 40px;")
        self.btn_proses.clicked.connect(self.proses_fcfs)
        self.layout_utama.addWidget(self.btn_proses)

    def load_ruang_dari_file(self, filepath):
        if not os.path.exists(filepath):
            return
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            self.combo_ruang.clear()
            self.combo_ruang.addItem("-- Pilih Ruang --")
            
            for _, row in df.iterrows():
                kode = str(row["kode_ruang"]).upper()
                nama = str(row["nama_ruang"])
                info_ruang = f"{kode} - {nama}"
                self.daftar_ruang.append({"kode": kode, "nama": nama})
                self.combo_ruang.addItem(info_ruang)
            print(f"Berhasil load {len(df)} ruang.")
        except Exception as e:
            print(f"Error: {e}")

    def setup_ui_input_reservasi(self):
        group_res = QGroupBox("Input Reservasi (First Come First Served)")
        layout = QHBoxLayout()
        
        self.input_nama_mahasiswa = QLineEdit()
        self.input_nama_mahasiswa.setPlaceholderText("Nama Mahasiswa")
        
        self.combo_ruang = QComboBox()
        self.combo_ruang.addItem("-- Pilih Ruang --")
        
        self.input_waktu_datang = QTimeEdit()
        self.input_waktu_datang.setTime(QTime.currentTime())
        
        self.input_durasi = QLineEdit()
        self.input_durasi.setPlaceholderText("Menit")
        self.input_durasi.setFixedWidth(50)
        
        btn_tambah_res = QPushButton("Daftar Antrian")
        btn_tambah_res.clicked.connect(self.tambah_reservasi)
        
        #
        btn_hapus_antrian = QPushButton("Pop")
        btn_hapus_antrian.clicked.connect(self.pop_hapus)

        layout.addWidget(QLabel("Mahasiswa:"))
        layout.addWidget(self.input_nama_mahasiswa)
        layout.addWidget(QLabel("Pilih Ruang:"))
        layout.addWidget(self.combo_ruang)
        layout.addWidget(QLabel("Jam Datang:"))
        layout.addWidget(self.input_waktu_datang)
        layout.addWidget(QLabel("Durasi (menit):"))
        layout.addWidget(self.input_durasi)
        layout.addWidget(btn_tambah_res)
        
        #
        layout.addWidget(btn_hapus_antrian)

        group_res.setLayout(layout)
        self.layout_utama.addWidget(group_res)

    def setup_ui_tabel(self):
        self.tabel = QTableWidget()
        self.tabel.setColumnCount(7)
        self.tabel.setHorizontalHeaderLabels([
            "Ruang", "Mahasiswa", "Jam Datang", "Durasi (menit)", 
            "Mulai Pinjam", "Waktu Tunggu (menit)", "Selesai"
        ])
        self.tabel.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout_utama.addWidget(self.tabel)

    def tambah_reservasi(self):
        mahasiswa = self.input_nama_mahasiswa.text()
        ruang_idx = self.combo_ruang.currentIndex()
        waktu_datang_str = self.input_waktu_datang.time().toString("HH:mm")
        durasi = self.input_durasi.text()
        
        if not mahasiswa or ruang_idx == 0 or not durasi:
            QMessageBox.warning(self, "Error", "Lengkapi data reservasi!")
            return
            
        try:
            durasi_menit = int(durasi)
            if durasi_menit <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Durasi harus angka positif (menit)!")
            return
        
        waktu_datang = datetime.strptime(waktu_datang_str, "%H:%M")
        
        reservasi_baru = {
            "ruang": self.combo_ruang.currentText(),
            "mahasiswa": mahasiswa,
            "waktu_datang_str": waktu_datang_str,
            "waktu_datang": waktu_datang,
            "durasi_menit": durasi_menit,
            "timestamp": datetime.now()
        }
        
        self.antrian_reservasi.append(reservasi_baru)
        self.update_daftar_reservasi()
        self.refresh_tabel_input()
        
        self.input_nama_mahasiswa.clear()
        self.input_durasi.clear()
        
        print(f"Ditambahkan: {mahasiswa} - {waktu_datang_str}")

    def update_daftar_reservasi(self):
        self.daftar_reservasi = list(self.antrian_reservasi)
        self.daftar_reservasi.sort(key=lambda x: (x['waktu_datang'], x['timestamp']))
        #
       

    def refresh_tabel_input(self):
        self.tabel.setRowCount(len(self.daftar_reservasi))
        for i, data in enumerate(self.daftar_reservasi):
            self.tabel.setItem(i, 0, QTableWidgetItem(data['ruang']))
            self.tabel.setItem(i, 1, QTableWidgetItem(data['mahasiswa']))
            self.tabel.setItem(i, 2, QTableWidgetItem(data['waktu_datang_str']))
            self.tabel.setItem(i, 3, QTableWidgetItem(f"{data['durasi_menit']} menit"))

    def proses_fcfs(self):
        if not self.antrian_reservasi:
            QMessageBox.information(self, "Info", "Tidak ada reservasi!")
            return
        
        self.update_daftar_reservasi()
        
        reservasi_per_ruang = {}
        for res in self.daftar_reservasi:
            ruang = res['ruang']
            if ruang not in reservasi_per_ruang:
                reservasi_per_ruang[ruang] = []
            reservasi_per_ruang[ruang].append(res)
        
        for ruang, reservasi_list in reservasi_per_ruang.items():
            waktu_selesai_sebelumnya = None
            
            for i, data in enumerate(reservasi_list):
                waktu_datang = data['waktu_datang']
                
                if waktu_selesai_sebelumnya is None or waktu_datang >= waktu_selesai_sebelumnya:
                    waktu_mulai = waktu_datang
                    waktu_tunggu = timedelta(0)
                else:
                    waktu_mulai = waktu_selesai_sebelumnya
                    waktu_tunggu = waktu_mulai - waktu_datang
                
                durasi_jam = data['durasi_menit'] / 60
                waktu_selesai = waktu_mulai + timedelta(hours=durasi_jam)
                waktu_selesai_sebelumnya = waktu_selesai
                
                row = self.daftar_reservasi.index(data)
                self.tabel.setItem(row, 4, QTableWidgetItem(waktu_mulai.strftime("%H:%M")))
                menit_tunggu = int(waktu_tunggu.total_seconds() / 60)
                self.tabel.setItem(row, 5, QTableWidgetItem(f"{menit_tunggu} menit"))
                self.tabel.setItem(row, 6, QTableWidgetItem(waktu_selesai.strftime("%H:%M")))
        
        QMessageBox.information(self, "Sukses", f"Proses FCFS selesai!")

    def pop_hapus(self):
        """Dequeue - Hapus reservasi pertama dari antrian"""
        if not self.antrian_reservasi:
            QMessageBox.warning(self, "Error", "Antrian kosong!")
            return
        
        # Hapus dari depan antrian (dequeue)
        tercepat = min(self.antrian_reservasi, key= lambda x: (x['waktu_datang'], x['timestamp']))
        self.antrian_reservasi.remove(tercepat)
        self.update_daftar_reservasi()
        self.refresh_tabel_input()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SistemReservasiFCFS()
    window.show()
    sys.exit(app.exec())
