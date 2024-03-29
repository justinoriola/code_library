from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
from time import sleep
from googleapiclient.errors import HttpError
import random
load_dotenv(dotenv_path='.env')
from datetime import datetime, timedelta, time
from account_handler import AccountHandler

# Constants
MY_EMAIL = os.environ.get('MY_EMAIL')
GOOGLE_API_SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'
MAX_RETRIES = 5
CURRENT_TIME = datetime.now().time()

class SpreadSheetHandler(AccountHandler):

    def __init__(self,account_key):

        super().__init__(account_key)
        self.scope = GOOGLE_API_SCOPES
        self.service_account_file = SERVICE_ACCOUNT_FILE
        self.spreadsheet_data = {}
        self.credentials = self.get_credentials()
        self.service_sheet = build('sheets', 'v4', credentials=self.credentials)
        self.service_drive = build('drive', 'v3',credentials=self.credentials)
        self.today = datetime.now().strftime('%A')
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime('%A')
        self.retry_counter = 0
        self.spreadsheet_values = self.get_spreadsheet_values()
        self.cash_float = int(self.spreadsheet_values['total_float'][0].replace(',', ''))
        self.expenses = int(self.spreadsheet_values['total_expenses'][0].replace(',', ''))
        self.banking = int(self.spreadsheet_values['total_banking'][0].replace(',', ''))
        self.today_closing_balance = int(self.spreadsheet_values['today_closing_balance'][0].replace(',', ''))
        self.today_opening_balance = int(self.spreadsheet_values['today_opening_balance'][0].replace(',', ''))
        self.yesterday_closing_balance = int(self.spreadsheet_values['yesterday_closing_balance'][0].replace(',', ''))
        self.bet_paid = self.spreadsheet_values['bet_ids']
        self.already_paid_bet = self.spreadsheet_values['already_paid_bet']

    def get_credentials(self):
        return service_account.Credentials.from_service_account_file(self.service_account_file, scopes=self.scope)

    # Select spreadsheet day based on script run time
    def closing_balance(self):
        if time(00, 0) <= CURRENT_TIME <= time(10, 29):
            closing_balance_day = datetime.now() - timedelta(days=1)
            return closing_balance_day.strftime('%A')
        else:
            return self.today

    def bet_day(self, day_of_the_week):
        day_ranges = {
            'Tuesday': '!N6:N46',
            'Wednesday': '!O6:O46',
            'Thursday': '!P6:P46',
            'Friday': '!Q6:Q46',
            'Saturday': '!R6:R46',
            'Sunday': '!S6:S46',
            'Monday': '!T6:T46'
        }
        return 'Weekly Report' + day_ranges.get(day_of_the_week, '')

    def get_spreadsheet_values(self):
        print(f'\nRetrieving spreadsheet value(s) for account {self.admin_username}...')
        bet_paid_range = self.bet_day(self.today)
        # Data
        WEEKLY_REPORT_RANGE = {
            'total_float': 'Weekly Report' + '!G15',
            'total_expenses': 'Weekly Report' + '!I15',
            'total_banking': 'Weekly Report' + '!k15',
            'bet_ids': bet_paid_range,
            'today_closing_balance': f'{self.today}' + '!F11',
            'today_opening_balance': f'{self.today}' + '!C28',
            'yesterday_closing_balance': f'{self.yesterday}' + '!F11',
            'already_paid_bet': 'Weekly Report' + '!W6:W100',
        }
        # Calculate the delay between each request to avoid exceeding rate limit (60 requests per minute)
        delay = 100.0 / 60

        # Loop over the weekly report range
        for key, value in WEEKLY_REPORT_RANGE.items():

            for i in range(MAX_RETRIES):
                sleep(delay)
                try:
                    response = self.service_sheet.spreadsheets().values().get(spreadsheetId=self.sheet_id,
                                                                              range=value).execute()
                    values = response.get('values', [])
                    result = [item[0].strip() for item in values]
                    if key == 'bet_ids':
                        result = [value.strip() for sublist in values for value in sublist if isinstance(value, str)
                              and value.lower().startswith('b')]
                    self.spreadsheet_data[key] = result
                    # print('quick nap cos of api limit...')
                    sleep(2)
                    break
                except HttpError as error:
                    if error.resp.status == 429:
                        print(f'API rate limit exceeded. Retrying in {i ** 2} seconds.')
                        sleep((i ** 2) + random.random())
                except Exception as e:
                    if self.retry_counter == 0:
                        print(f'Something went wrong. Retrying in 120 seconds.')
                        sleep(120)
                        self.get_spreadsheet_values()
                        self.retry_counter += 1
                    else:
                        print(f'Unable to retrieve spreadsheet value for {key}: {value}')
                        print(f'HTTP error occurred: {e}')
                        break
                finally:
                    if 'already_paid_bet' in self.spreadsheet_data:
                        print(f'All spreadsheet values retrieved successfully')
        return self.spreadsheet_data

    def create_spreadsheet_duplicate(self, duplicate_spreadsheet_name):

        try:
            # Create a request for duplicating the Spreadsheet
            request = self.service_drive.files().copy(
                fileId=self.sheet_id,
                body={"name": duplicate_spreadsheet_name}
            ).execute()
            copied_file_id = request.get('id')

            # Share the copied spreadsheet with your account
            def_permission = self.service_drive.permissions().create(
                fileId=copied_file_id,
                body={
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': MY_EMAIL
                },
                fields='id'
            ).execute()
            sleep(3)
            print(f"duplicate spreadsheet '{duplicate_spreadsheet_name}' was successfully created.")
        except Exception as error:
            print(f'An error occurred: {error}')

    def clear_spreadsheet(self, days_to_clear):

        """Clears specific cells of a spreadsheet for a given day."""
        # Data - cells in spreadsheet to be cleared
        cells_to_clear = {
            f'{days_to_clear}!C10:F11': [['0', '0', '0', '0']] * 2,
            f'{days_to_clear}!C18:C28': [['0']] * 11,
            f'{days_to_clear}!F18:F29': [['0']] * 12,
            f'{days_to_clear}!E23:E29': [['x']] * 7,
            f'{days_to_clear}!B23:B28': [['x']] * 6,
            f'{days_to_clear}!L4:L44': [['0']] * 41,
            f'{days_to_clear}!K4:L44': [['x']] * 41,
            f'{days_to_clear}!I6:I14': [['in progress...']] * 1,
        }

        # Loop over the cells to be cleared
        for cell_range, new_values in cells_to_clear.items():
            for i in range(MAX_RETRIES):
                try:
                    # Prepare the request body with the new values
                    body = {
                        'values': new_values
                    }
                    # Send the update request
                    result = self.service_sheet.spreadsheets().values().update(
                        spreadsheetId=self.sheet_id,
                        range=cell_range,
                        valueInputOption='USER_ENTERED',
                        body=body).execute()

                    print(f'Successfully cleared cells "{cell_range}"')
                    sleep(3)
                    break
                except HttpError as error:
                    if error.resp.status == 429:
                        print(f'API rate limit exceeded. Retrying in {i ** 2} seconds.')
                        sleep((i ** 2) + random.random())
                    else:
                        print(f'HTTP error occurred: {error}')
                        break

    def upload_to_google_sheets(self, value_list1, value_list2):
        if value_list1 is not None:
            for i in range(MAX_RETRIES):
                try:
                    """
                    Upload a list of values to a Google Spreadsheet using Google Sheets API.
            
                    Args:
                    - values_list (list): The list of values to upload.
                    - spreadsheet_id (str): The ID of the Google Spreadsheet.
                    - sheet_name (str): The name of the sheet in the spreadsheet (default is 'Sheet1').
                    """
                    range_ = f'Weekly Report!W{len(value_list2) + 6}'

                    # Resize the sheet based on the length of the values_list
                    result = self.service_sheet.spreadsheets().values().update(
                        spreadsheetId=self.sheet_id,
                        range=range_,
                        body={'values': [[value] for value in value_list1]},
                        valueInputOption='RAW'
                    ).execute()
                    print(f'Paid tickets successfully uploaded on the spreadsheet')
                    break
                except HttpError as error:
                    if error.resp.status == 429:
                        print(f'API rate limit exceeded. Retrying in {i ** 2} seconds.')
                        sleep((i ** 2) + random.random())
                    else:
                        print(f'HTTP error occurred: {error}')
                        break

    def betid_checks(self, bet_list1: list, bet_list2: list):
        print("\nChecking betIDs for incorrect input or already paid ticket(s)...")
        try:
            previously_paid_tickets = [item for item in bet_list1 if item in bet_list2]
            incorrect_ticket_input = [ticket for ticket in bet_list1 if len(ticket) != 22]

            if previously_paid_tickets and incorrect_ticket_input:
                message = (f'{len(previously_paid_tickets)} previously paid tickets found:\n{", ".join(previously_paid_tickets)}\n'
                        f'{len(incorrect_ticket_input)} incorrect ticket input:\n{", ".join(incorrect_ticket_input)}')

            # Display previously paid tickets
            if previously_paid_tickets:
                message = f'{len(previously_paid_tickets)} previously paid tickets found:\n{", ".join(previously_paid_tickets)}'

            # Display tickets with wrong input
            if incorrect_ticket_input:
                message = f'{len(incorrect_ticket_input)} incorrect ticket input:\n{", ".join(incorrect_ticket_input)}'

            # Display message if no anomalies found
            if not previously_paid_tickets and not incorrect_ticket_input:
                message = 'no incorrect or already paid ticket!'
        except Exception as error:
            print(f'Error occurred: {error}')
        finally:
            return message

    def opening_balance_check(self, today_opening_balance, yesterday_balance):
        try:
            if yesterday_balance == today_opening_balance:
                return f"yday's closing = today's opening = {yesterday_balance}"
            else:
                return f"today's opening != yday's closing: {abs(yesterday_balance - today_opening_balance)} shortage."
        except Exception as e:
            print(f'Error occurred: {e}')
