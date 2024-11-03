import os
import sys
import configparser
from src.monitor import EmployeeMonitor

def load_config():

    config = configparser.ConfigParser()
    config_path = os.path.join('config', 'config.ini')
    
    if not os.path.exists(config_path):
        print("Error: File konfigurasi tidak ditemukan!")
        sys.exit(1)
        
    config.read(config_path)
    return config

def create_folders(config):

    folders = [
        config['Paths']['data_folder'],
        config['Paths']['archive_folder'],
        config['Paths']['error_folder'],
        config['Paths']['output_folder']
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

def main():

    config = load_config()
    
    create_folders(config)

    monitor = EmployeeMonitor(config)
    monitor.run_monitoring()

if __name__ == "__main__":
    main()