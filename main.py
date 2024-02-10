
from datetime import datetime, timedelta, time

from notification_handler import NotificationHandler
from spreadsheet_handler import SpreadSheetHandler
from account_handler import AccountHandler, ACCOUNT_CREDENTIALS
from logic_handler import LogicHandler
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')
from time import sleep
from flask import Flask

# Constants
DAYS_OF_THE_WEEK = ['Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'Monday']
CURRENT_TIME = datetime.now().time()
TODAY = datetime.now().strftime('%A')
TODAYS_DATE = datetime.now().date().strftime("%d/%m/%Y")
PAST_DATE = (datetime.now().date() - timedelta(days=6)).strftime("%d/%m/%Y")
message_bank = ''

# # Main script
# app = Flask(__name__)
#
# @app.route('/start')
# def start_route():

if __name__ == '__main__':
    # set a start time
    start_time = datetime.now()

    # instantiate notification object
    notification_handler = NotificationHandler()

    # Loop through the credential dictionary's key
    for key in ACCOUNT_CREDENTIALS.keys():

        # Unpacking account credentials
        admin_username = ACCOUNT_CREDENTIALS[key]['username']
        admin_password = ACCOUNT_CREDENTIALS[key]['password']
        cashier_password = ACCOUNT_CREDENTIALS[key]['cashier_password']
        credited_amount = ACCOUNT_CREDENTIALS[key]['amount_to_credit']
        cashier_numbers = ACCOUNT_CREDENTIALS[key]['number_of_cashier']
        sheet_name = ACCOUNT_CREDENTIALS[key]['worksheet_name']
        sheet_id = ACCOUNT_CREDENTIALS[key]['worksheet_id']
        base_balance = ACCOUNT_CREDENTIALS[key]['base_balance']

        # Instantiate account handler object
        account_handler = AccountHandler(admin_username=admin_username, admin_password=admin_password,
                                         credited_amount=credited_amount, cashier_numbers=cashier_numbers,
                                         cashier_password=cashier_password)

        # Withdraw and credit cashier account
        if time(15, 0) <= CURRENT_TIME <= time(23, 59):
            cashier_checks = account_handler.cashier_check(cashier_numbers)
            account_handler.withdraw_from_cashier()

        # Instantiate spreadsheet handler objects and get spreadsheet values
        if time(15, 0) <= CURRENT_TIME <= time(23, 55):
            sleep(2)

            # Instantiate handler object and get spreadsheet values
            spreadsheet_handler = SpreadSheetHandler(sheet_id, sheet_name,
                                                     admin_username=admin_username,
                                                     admin_password=account_handler.admin_password,
                                                     credited_amount=account_handler.credited_amount,
                                                     cashier_numbers=account_handler.cashier_numbers,
                                                     cashier_password=account_handler.cashier_password)
            # get spreadsheet values
            spreadsheet_values = spreadsheet_handler.get_spreadsheet_values()

            # Unpack spreadsheet values
            cash_float = int(spreadsheet_values['total_float'][0].replace(',', ''))
            expenses = int(spreadsheet_values['total_expenses'][0].replace(',', ''))
            banking = int(spreadsheet_values['total_banking'][0].replace(',', ''))
            today_closing_balance = int(spreadsheet_values['today_closing_balance'][0].replace(',', ''))
            today_opening_balance = int(spreadsheet_values['today_opening_balance'][0].replace(',', ''))
            yesterday_closing_balance = int(spreadsheet_values['yesterday_closing_balance'][0].replace(',', ''))
            bet_paid = spreadsheet_values['bet_ids']
            already_paid_bet = spreadsheet_values['already_paid_bet']

            # filter bet_paid list
            bet_ticket_checks = spreadsheet_handler.betid_checks(bet_paid, already_paid_bet)

            # Pay out bet slips
            paid_betlist = account_handler.bet_payout(bet_paid)
            spreadsheet_handler.upload_to_google_sheets(paid_betlist, already_paid_bet)
            # if not paid_betlist:
            #     account_handler.login()
            winning = account_handler.winning_balance()

            # Instantiate logic handler object
            logic = LogicHandler()
            admin_balance = account_handler.get_admin_balance()

            account_balance = logic.account_balance(base_balance=base_balance, expenses=expenses, banking=banking,
                                                    closing_balance=today_closing_balance, float=cash_float,
                                                    winning=winning, admin_balance=admin_balance)
            account_handler.driver.quit()

            account_reset_message = logic.account_reset(base_balance=base_balance, winning=winning,
                                                closing_balance=today_closing_balance, admin_balance=admin_balance)

            # print account balance/reset status
            account_status_message = logic.account_status(account_balance)
            # message_account_reset = f'Reset amount:' + f'{str(account_reset)}'

            # check if yesterday's closing == today's opening balance
            message_account_checks = (
                  f'\nChecks performed:'
                  f'\n-{spreadsheet_handler.betid_checks(bet_paid, already_paid_bet)}'
                  f'\n-{spreadsheet_handler.opening_balance_check(today_opening_balance, yesterday_closing_balance)}'
                  f'\n-{cashier_checks}'
            )

            # instantiate and get the message to be sent
            message = logic.text(admin_username, key, base_balance=base_balance, expenses=expenses, banking=banking,
                                       closing_balance=today_closing_balance, float=cash_float, winning=winning,
                                       admin_balance=admin_balance)

            # send report to WhatsApp
            message += f'\nAccount Status:' + f"\n{'-' * 15}|" + f'\n{account_status_message}' + f'\n{account_reset_message}' + f"\n{'-' * 30}"
            if account_balance != 0:
                message += message_account_checks

            # bank messages
            message_bank += f'{message}\n\n'

            # send Notification / print to console
            print(message_bank)
            notification_handler.send_sms(message)

            # Create duplicate spreadsheet and reset existing spreadsheet for re-use.
            if TODAY == "Monday" and time(13, 25) <= CURRENT_TIME <= time(23, 50):
                new_sheet_name = f'{sheet_name}: {PAST_DATE} - {TODAYS_DATE}'
                spreadsheet_handler.create_spreadsheet_duplicate(new_sheet_name)
                for days_to_clear in DAYS_OF_THE_WEEK:
                    spreadsheet_handler.clear_spreadsheet(days_to_clear)
            else:
                print(f'\nspreadsheet duplicate/clear function not schedule to run by this time')


        # credit cashier account at specified time
        elif time(5, 0) <= CURRENT_TIME <= time(7, 30):
            admin_balance = account_handler.get_admin_balance()
            account_handler.credit_cashier(admin_balance)
        else:
            print('This other section(s) of the script is not scheduled to run by this time')
            print(f'CURRENT_TIME: {CURRENT_TIME}')
        sleep(5)


    # calculate and print the total time taken to process the entire script
    end_time = datetime.now()
    elapsed_time = end_time - start_time
    minutes, seconds = divmod(elapsed_time.seconds, 60)
    print(f'\nTotal time: {minutes} minutes and {seconds} seconds')


    # app.run(debug=True)