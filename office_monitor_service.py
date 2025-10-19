import time
import logging
from office_defender import OfficeDefender
class OfficeMonitorService:
    def __init__(self):
        self.defender = OfficeDefender()
        self.check_interval = 60
    def run_service(self):
        logging.info("Запуск службы мониторинга Office")
        while True:
            try:
                self.defender.kill_wps_processes()
                if int(time.time()) % 300 == 0:
                    wps_paths = self.defender.find_wps_installation()
                    if wps_paths:
                        logging.warning("Обнаружен WPS - запуск удаления")
                        self.defender.uninstall_wps()
                        self.defender.restore_file_associations()
                time.sleep(self.check_interval)
            except Exception as e:
                logging.error(f"Ошибка службы: {e}")
                time.sleep(self.check_interval * 2)
if __name__ == "__main__":
    service = OfficeMonitorService()
    service.run_service()
