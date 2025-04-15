import logging

class Logger:
    def __init__(self, log_file="system.log"):
        self.logger = logging.getLogger('TaskSchedulerLogger')
        self.logger.setLevel(logging.INFO)

        # Avoid duplicate handlers if Logger is used multiple times
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log(self, message, color=None):
        """Logs to both file and console. Adds color if specified for console output only."""
        self.logger.info(message)  # Log to file (no color)

        if color:
            print(f"{color}{message}\033[0m")  # Print with color to terminal
        else:
            print(message)
