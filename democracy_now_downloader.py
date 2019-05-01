import argparse
import datetime
import os
import requests
from shutil import move
from time import sleep


class DNApp:
    def __init__(self, get_hd_file, save_file_path, share_path):
        self.get_hd = get_hd_file
        if save_file_path is None:
            self.save_file_path = os.getcwd()
        else:
            self.save_file_path = save_file_path

        self.share_path = share_path

    @staticmethod
    def download_file(url):
        # does the downloading of the mp4
        local_file_name = url.split('/')[-1]
        r = requests.get(url)
        with open(local_file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return

    @staticmethod
    def convert_bytes(num):
        # used with os.stat(file) st_size for a more readable file size number
        for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if num < 1024.0:
                return '%3.1f %s' % (num, x)
            num /= 1024

    def move_file(self, year, month, day, attempts=3):
        for attempt in range(attempts):
            try:
                # attempting move the downloaded episode to the specified path
                from_local = '{}/dn{}-{}{}.mp4'.format(self.save_file_path, year, month, day)
                to_share = '{}/dn{}-{}{}.mp4'.format(self.share_path, year, month, day)
                move(from_local, to_share)
                break
            except Exception as ex:
                print('Move attempt: {}/{} failed\n{}'.format(attempt + 1, attempts, ex))
                sleep(60)

    def get_democracy_now(self):
        today = datetime.date.today()
        year = today.year
        # single digit months and days get a zero added in front of them for use in the url
        month = today.month
        if len(str(month)) == 1:
            month = '0' + str(month)
        day = today.day
        if len(str(day)) == 1:
            day = '0' + str(day)
        # Democracy now does not produce new episodes on weekends so they are skipped
        if datetime.date(year, int(month), int(day)).weekday() < 6:
            if self.get_hd:
                demo_now_url = 'https://publish.dvlabs.com/democracynow/720/dn{}-{}{}.mp4'.format(year, month, day)
            else:
                demo_now_url = 'https://publish.dvlabs.com/democracynow/360/dn{}-{}{}.mp4'.format(year, month, day)
            # An attempt is made to open specified save directory, defaults to cwd upon failure
            try:
                os.chdir(self.save_file_path)
            except Exception as ex:
                print('Unable to find save location, saving to DNApp directory.\n{}'.format(ex))
                self.save_file_path = os.getcwd()

            # downloading the episode
            self.download_file(demo_now_url)

            # reporting info about the file, and moving the file if necessary
            demo_now_file = 'dn{}-{}{}.mp4'.format(year, month, day)
            file_info = os.stat(demo_now_file)
            file_size = self.convert_bytes(file_info.st_size)
            if os.path.exists(demo_now_file):
                print('Download complete for {}/{}/{},'.format(month, day, year), 'File size:', file_size)
                if self.share_path is not None:
                    self.move_file(year, month, day)

    def run(self):
        print('Democracy Now downloader started:', str(datetime.datetime.today())[:-7])
        while True:
            today = datetime.datetime.today()
            hour_now = today.hour
            minute_now = today.minute
            current_time = datetime.time(hour=hour_now, minute=minute_now)
            # setting up the three hour window in which the download will be attempted
            # this window was chosen to ensure enough time has passed for the episode to become available online
            eleven_thirty_am = datetime.time(hour=11, minute=30)
            two_thirty_pm = datetime.time(hour=16, minute=30)
            # checking if the current time is during specified hours, if so, download is attempted
            if eleven_thirty_am < current_time < two_thirty_pm:
                self.get_democracy_now()
                # waiting four hours after attempting the download to prevent multiple downloads of the same file
                sleep(60 * 60 * 4)
            else:
                # if it is not during the download window, wait for one hour before checking again
                sleep(60 * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-hd', '--get_hd', help='set to True to get hd file instead of web quality file', type=bool)
    parser.add_argument('-sv', '--save_path', help='add a specific path to save the file to', type=str)
    parser.add_argument('-sh', '--share_path', help='add a specific path to move the completed file to', type=str)
    args = parser.parse_args()
    app = DNApp(get_hd_file=args.get_hd, save_file_path=args.save_path, share_path=args.share_path)
    app.run()
