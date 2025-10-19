#!/usr/bin/env python3
import os
import sys
import time
import logging
import subprocess
import winreg
import psutil
import shutil
from pathlib import Path
class OfficeDefender:
    def __init__(self):
        self.setup_logging()
        self.wps_processes = ['wps.exe', 'et.exe', 'wpp.exe', 'wpscloudsvr.exe', 'ksolaunch.exe', 'wpsnotify.exe']
        self.office_extensions = ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
    def setup_logging(self):
        logging.basicConfig(
            filename='C:\\Windows\\Temp\\office_defender.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    def run_as_admin(self):
        if not self.is_admin():
            logging.warning("Требуются права администратора. Перезапуск...")
            subprocess.run(['powershell', '-Command', 
                          f'Start-Process "{sys.executable}" -ArgumentList "{" ".join(sys.argv)}" -Verb RunAs'])
            sys.exit()
    def is_admin(self):
        try:
            return os.getuid() == 0
        except AttributeError:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
    def kill_wps_processes(self):
        logging.info("Поиск процессов WPS...")
        killed = False
        for proc in psutil.process_iter(['name', 'pid', 'exe']):
            try:
                proc_name = proc.info['name'].lower()
                if proc_name in self.wps_processes:
                    logging.info(f"Завершаю процесс: {proc_name} (PID: {proc.pid})")
                    proc.kill()
                    killed = True
                elif proc.info['exe'] and 'kingsoft' in proc.info['exe'].lower():
                    logging.info(f"Завершаю процесс Kingsoft: {proc.info['exe']} (PID: {proc.pid})")
                    proc.kill()
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                continue
        if killed:
            time.sleep(3)  
        return killed    
    def find_wps_installation(self):
        wps_paths = []
        possible_paths = [
            "C:\\Program Files\\Kingsoft\\WPS Office",
            "C:\\Program Files (x86)\\Kingsoft\\WPS Office",
            os.path.expandvars("%PROGRAMDATA%\\Kingsoft\\WPS Office")
        ]
        appdata_paths = [
            os.path.expandvars("%LOCALAPPDATA%\\Kingsoft"),
            os.path.expandvars("%APPDATA%\\Kingsoft"),
            os.path.expandvars("%LOCALAPPDATA%\\Programs\\Kingsoft\\WPS Office")
        ]
        all_paths = possible_paths + appdata_paths
        for base_path in all_paths:
            if os.path.exists(base_path):
                for root, dirs, files in os.walk(base_path):
                    if any(exe in files for exe in ['wps.exe', 'et.exe', 'wpp.exe', 'ksolaunch.exe']):
                        wps_paths.append(root)
                        logging.info(f"Найден WPS: {root}")
        ksolaunch_path = os.path.expandvars("%LOCALAPPDATA%\\Kingsoft\\WPS Office\\ksolaunch.exe")
        if os.path.exists(ksolaunch_path):
            wps_dir = os.path.dirname(ksolaunch_path)
            if wps_dir not in wps_paths:
                wps_paths.append(wps_dir)
                logging.info(f"Найден ksolaunch: {wps_dir}")
        reg_paths = [
            "SOFTWARE\\WOW6432Node\\Kingsoft\\WPS Office",
            "SOFTWARE\\Kingsoft\\WPS Office",
            "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WPS Office",
            "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WPS Office"
        ]
        for reg_path in reg_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                    wps_paths.append(f"Обнаружен в реестре: {reg_path}")
            except:
                pass
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Kingsoft\\WPS Office") as key:
                wps_paths.append("Обнаружен в HKCU")
        except:
            pass
        return wps_paths
    
    def get_wps_uninstall_string(self):
        uninstall_paths = [
            "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WPS Office",
            "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WPS Office",
            "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Kingsoft WPS",
        ]
        for reg_path in uninstall_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                    uninstall_string = winreg.QueryValueEx(key, "UninstallString")[0]
                    display_name = winreg.QueryValueEx(key, "DisplayName")[0]
                    logging.info(f"Найдена команда удаления: {display_name} - {uninstall_string}")
                    return uninstall_string
            except:
                continue
        return None
    def uninstall_wps(self):
        logging.info("Попытка удаления WPS Office...")
        uninstall_string = self.get_wps_uninstall_string()
        if uninstall_string:
            try:
                logging.info(f"Запуск деинсталлятора: {uninstall_string}")
                if uninstall_string.endswith('.exe'):
                    uninstall_string += ' /S'
                subprocess.run(uninstall_string, shell=True, timeout=60)
                time.sleep(10)
                return True
            except Exception as e:
                logging.error(f"Ошибка удаления через инсталлятор: {e}")
        uninstallers = [
            "C:\\Program Files\\Kingsoft\\WPS Office\\uninstall.exe",
            "C:\\Program Files (x86)\\Kingsoft\\WPS Office\\uninstall.exe",
            os.path.expandvars("%LOCALAPPDATA%\\Kingsoft\\WPS Office\\uninstall.exe"),
        ]
        for uninstaller in uninstallers:
            if os.path.exists(uninstaller):
                try:
                    logging.info(f"Запуск деинсталлятора: {uninstaller}")
                    subprocess.run([uninstaller, '/S'], timeout=60)
                    time.sleep(10)
                    return True
                except Exception as e:
                    logging.error(f"Ошибка удаления {uninstaller}: {e}")
        return False
    
    def force_remove_wps(self):
        logging.info("Принудительное удаление остатков WPS...")
        wps_paths = self.find_wps_installation()
        for path in wps_paths:
            if os.path.exists(path):
                try:
                    shutil.rmtree(path, ignore_errors=True)
                    logging.info(f"Удалена папка: {path}")
                except Exception as e:
                    logging.error(f"Ошибка удаления {path}: {e}")
        self.clean_wps_registry()
    def clean_wps_registry(self):
        logging.info("Очистка реестра от записей WPS...")
        reg_paths = [
            "SOFTWARE\\WOW6432Node\\Kingsoft",
            "SOFTWARE\\Kingsoft",
            "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WPS Office",
            "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WPS Office",
        ]
        for reg_path in reg_paths:
            try:
                winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                logging.info(f"Удален ключ реестра: {reg_path}")
            except:
                pass
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, "Software\\Kingsoft")
        except:
            pass
    def find_office_path(self):
        """Поиск установленного Microsoft Office"""
        office_versions = [
            "C:\\Program Files\\Microsoft Office\\root\\Office16",
            "C:\\Program Files\\Microsoft Office\\Office16", 
            "C:\\Program Files\\Microsoft Office\\Office15",
            "C:\\Program Files\\Microsoft Office\\Office14",
            "C:\\Program Files (x86)\\Microsoft Office\\root\\Office16",
            "C:\\Program Files (x86)\\Microsoft Office\\Office16",
        ]
        for path in office_versions:
            word_path = os.path.join(path, "WINWORD.EXE")
            if os.path.exists(word_path):
                logging.info(f"Найден Office: {path}")
                return path
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                              "SOFTWARE\\Microsoft\\Office\\16.0\\Common\\InstallRoot") as key:
                path = winreg.QueryValueEx(key, "Path")[0]
                if os.path.exists(os.path.join(path, "WINWORD.EXE")):
                    logging.info(f"Найден Office через реестр: {path}")
                    return path
        except:
            pass
        logging.error("Microsoft Office не найден!")
        return None
    def restore_file_associations(self):
        office_path = self.find_office_path()
        if not office_path:
            logging.error("Не удалось восстановить ассоциации - Office не найден")
            return False
        logging.info("Восстановление ассоциаций файлов...")
        word_path = os.path.join(office_path, "WINWORD.EXE")
        excel_path = os.path.join(office_path, "EXCEL.EXE")
        powerpoint_path = os.path.join(office_path, "POWERPNT.EXE")
        associations = {
            '.doc': f'"{word_path}" "%1"',
            '.docx': f'"{word_path}" "%1"',
            '.xls': f'"{excel_path}" "%1"',
            '.xlsx': f'"{excel_path}" "%1"',
            '.ppt': f'"{powerpoint_path}" "%1"',
            '.pptx': f'"{powerpoint_path}" "%1"'
        }
        success_count = 0
        for ext, command in associations.items():
            try:
                prog_id = f"Office.File{ext.upper().replace('.', '')}"
                subprocess.run(['ftype', prog_id, command], check=True, 
                             capture_output=True, timeout=10)
                subprocess.run(['assoc', ext, prog_id], check=True,
                             capture_output=True, timeout=10)
                logging.info(f"Установлена ассоциация: {ext} -> {prog_id}")
                success_count += 1
            except subprocess.CalledProcessError as e:
                logging.warning(f"Не удалось установить ассоциацию {ext}: {e}")
            except Exception as e:
                logging.error(f"Ошибка ассоциации {ext}: {e}")
        logging.info(f"Успешно установлено ассоциаций: {success_count}/{len(associations)}")
        return success_count > 0
    def block_wps_installation(self):
        """Блокировка установки WPS через hosts файл"""
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        block_domains = [
            "127.0.0.1 kingsoft.com",
            "127.0.0.1 wps.com", 
            "127.0.0.1 ksoapi.wps.com",
            "127.0.0.1 activate.adobe.com",
            "127.0.0.1 pc.kingsoft.com",
            "127.0.0.1 service.kingsoft.com"
        ]
        try:
            with open(hosts_path, 'r', encoding='utf-8') as f:
                content = f.read()
            new_domains = []
            for domain in block_domains:
                if domain not in content:
                    new_domains.append(domain)
            if new_domains:
                with open(hosts_path, 'a', encoding='utf-8') as f:
                    f.write("\n# Блокировка WPS Office\n")
                    for domain in new_domains:
                        f.write(f"{domain}\n")
                logging.info(f"Заблокировано доменов WPS: {len(new_domains)}")
                return True
            else:
                logging.info("Домены WPS уже заблокированы")
                return True
        except Exception as e:
            logging.error(f"Ошибка блокировки hosts: {e}")
            return False
    def set_office_defaults_ps(self):
        logging.info("Установка Office программ по умолчанию через PowerShell...")
        try:
            result = subprocess.run([
                'powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script
            ], capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                logging.info("PowerShell скрипт выполнен успешно")
                return True
            else:
                logging.error(f"Ошибка PowerShell: {result.stderr}")
                return False
        except Exception as e:
            logging.error(f"Ошибка выполнения PowerShell: {e}")
            return False
    def run_protection(self):
        logging.info("=== ЗАПУСК ПОЛНОЙ ЗАЩИТЫ OFFICE ===")
        self.run_as_admin()
        self.kill_wps_processes()
        wps_installed = self.find_wps_installation()
        if wps_installed:
            logging.warning(f"Обнаружен WPS Office: {wps_installed}")
            self.uninstall_wps()
            time.sleep(5)
            self.force_remove_wps()
        self.restore_file_associations()
        self.set_office_defaults_ps()
        self.block_wps_installation()
        logging.info("Защита Office завершена")
        return True
def main():
    defender = OfficeDefender()
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        while True:
            defender.kill_wps_processes()
            wps_paths = defender.find_wps_installation()
            if wps_paths:
                logging.warning("Обнаружен WPS в режиме мониторинга")
                defender.run_protection()
            time.sleep(30)
    else:
        defender.run_protection()
if __name__ == "__main__":
    main()
