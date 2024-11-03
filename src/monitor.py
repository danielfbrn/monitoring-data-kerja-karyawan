import os
import pandas as pd
from datetime import datetime
from plyer import notification
import logging
from .utils import parse_date, setup_logging

class EmployeeMonitor:
    def __init__(self, config):
        self.config = config
        self.data_folder = config['Paths']['data_folder']
        self.output_folder = config['Paths']['output_folder']
        self.file_pattern = config['Files']['file_pattern']
        self.notification_timeout = int(config['Monitoring']['notification_timeout'])
        
        log_file = os.path.join(config['Paths']['error_folder'], 
                                f'error_{datetime.now().strftime("%Y%m%d")}.log')
        self.logger = setup_logging(log_file)

    def analyze_data(self):
        try:
            latest_files = self._get_latest_files()
            if not latest_files:
                self.show_notification("Peringatan", "Tidak ada file laporan ditemukan!")
                return

            for file in latest_files:
                file_path = os.path.join(self.data_folder, file)
                df = pd.read_excel(file_path)

                print(f"\nMemproses file: {file}")
                self._validate_and_process_data(df, file)

        except Exception as e:
            self.logger.error(f"Error dalam analisis data: {str(e)}")
            self.show_notification("Error", f"Terjadi kesalahan dalam analisis data")
        
    
    def _validate_and_process_data(self, df, file_name):
        today = datetime.now().date()
        
        required_columns = ['NO ID', 'NAMA', 'TANGGAL PENGERJAAN', 'KARYAWAN']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Format file {file_name} tidak sesuai")

        df['TANGGAL PENGERJAAN'] = df['TANGGAL PENGERJAAN'].apply(parse_date)

        print("Data setelah parsing tanggal:")
        print(df.head())

        valid_data = df[df['TANGGAL PENGERJAAN'].notna()]
        outdated_records = valid_data[valid_data['TANGGAL PENGERJAAN'] < today]

        print(f"Jumlah data yang belum diperbarui: {len(outdated_records)}")

        if not outdated_records.empty:
            self._save_monitoring_log(outdated_records, file_name)
            message = self._create_notification_message(outdated_records, file_name, today)
            self.show_notification("Data Belum Update", message)
        else:
            self.show_notification("Info", f"File {file_name}: Semua data telah diupdate!")

    def _get_latest_files(self):
        files = [f for f in os.listdir(self.data_folder) if f.startswith(self.file_pattern.split('*')[0]) and f.endswith('.xlsx')]
        print(f"DEBUG: Files ditemukan di {self.data_folder}: {files}")
        return sorted(files, reverse=True) if files else []
    
    def _save_monitoring_log(self, outdated_records, file_name):
        today = datetime.now().date()
        log_file_path = os.path.join(self.output_folder, f"monitoring_{today.strftime('%Y%m%d')}.log")
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"\nHasil Monitoring untuk File: {file_name}\n")
            log_file.write("=" * 50 + "\n")

            karyawan_groups = outdated_records.groupby('KARYAWAN')
            for karyawan, group in karyawan_groups:
                log_file.write(f"\nKARYAWAN: {karyawan}\n")
                log_file.write("-" * 50 + "\n")
                for _, row in group.iterrows():
                    days_late = (today - row['TANGGAL PENGERJAAN']).days
                    log_file.write(f"Nasabah: {row['NAMA']}\n")
                    log_file.write(f"  - Tanggal Pengerjaan: {row['TANGGAL PENGERJAAN']}\n")
                    log_file.write(f"  - Terlambat: {days_late} hari\n")
            log_file.write("\n")

    def _create_notification_message(self, outdated_records, file_name, today):
        message = f"File {file_name}: Data belum diupdate untuk:\n"
        karyawan_groups = outdated_records.groupby('KARYAWAN')
        for karyawan, group in karyawan_groups:
            message += f"\nKARYAWAN: {karyawan}\n"
            for _, row in group.iterrows():
                days_late = (today - row['TANGGAL PENGERJAAN']).days
                message += f"  - Client: {row['NAMA']} (Terlambat {days_late} hari)\n"
        return message

    def show_notification(self, title, message):
        try:
            notification.notify(
                title=title,
                message=message,
                timeout=self.notification_timeout
            )
        except Exception as e:
            self.logger.error(f"Error dalam menampilkan notifikasi: {str(e)}")

        print(f"\n{title}")
        print("-" * 50)
        print(message)

    def run_monitoring(self):
        self.logger.info(f"Memulai monitoring folder: {self.data_folder}")
        self.analyze_data()
