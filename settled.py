import datetime
MAX_DAYS_OUTSIDE_UK = 180

DISCLAIMER_TEXT = """
Disclaimer: This tool provides an estimation based on the provided dates. Always consult with official sources or legal experts regarding immigration rules.
"""

def read_dates_from_file(filename):
    try:
        with open(filename, 'r') as file:
            lines = [l.strip() for l in file.readlines()]
            return [(datetime.datetime.strptime(lines[i].replace("entered UK ", ""), "%d/%m/%Y").date(),
                     datetime.datetime.strptime(lines[i+1].replace("left UK ", ""), "%d/%m/%Y").date() if i + 1 < len(lines) and "left UK" in lines[i+1] else None)
                    for i in range(0, len(lines), 2)]
    except FileNotFoundError:
        print("No 'dates.txt' file found.")
        return []


def validate_dates(dates):
    """Validate and sort the dates to ensure they're in chronological order."""
    # Sort by entry date
    dates.sort(key=lambda x: x[0])

    # Check for exit dates that are before entry dates and correct them
    for i, (entry_date, exit_date) in enumerate(dates):
        if exit_date and exit_date < entry_date:
            print(f"Warning: Exit date {exit_date} is before entry date {entry_date}. Swapping them.")
            dates[i] = (exit_date, entry_date)

    return dates

def calculate_application_date(dates):
    # Calculate the end date after 5 years
    end_date = dates[0][0] + datetime.timedelta(days=365*5)

    # Check for a leap year in the span
    if any(is_leap_year(year) for year in range(dates[0][0].year, dates[0][0].year + 5)):
        end_date += datetime.timedelta(days=1)

    return end_date

def is_leap_year(year):
    """Check if a given year is a leap year."""
    return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0


def check_continuous_residence(dates, current_date):
    continuous_breaks = []

    # Calculate the 12 month period from the current date
    start_date_12_month_period = current_date - datetime.timedelta(days=365)
    total_days_outside_last_12_months = 0


    for i, (_, exit_date) in enumerate(dates[:-1]):  # Exclude the last entry because it doesn't have an exit date
        next_entry_date = dates[i+1][0]

        if not exit_date:  # If currently in the UK
            exit_date = current_date

        days_outside = (next_entry_date - exit_date).days

         # Check if the period overlaps with the last 12 months
        if exit_date > start_date_12_month_period or next_entry_date > start_date_12_month_period:
            total_days_outside_last_12_months += min(
                days_outside,
                (next_entry_date - start_date_12_month_period).days,
                (current_date - exit_date).days)
            
            days_left_outside = MAX_DAYS_OUTSIDE_UK - total_days_outside_last_12_months
            

        if days_outside > 180:
            continuous_breaks.append((exit_date, next_entry_date, days_outside))

    
    if continuous_breaks:
        return False, continuous_breaks
    else:
        return True, days_left_outside


    
def prompt_user_for_dates():
    dates = []
    while True:
        entry_date_str = input("Enter the date you came to the UK (format: dd/mm/yyyy or 'stop' to finish): ")
        if entry_date_str.lower() == 'stop':
            break
        try:
            entry_date = datetime.datetime.strptime(entry_date_str, "%d/%m/%Y").date()
            exit_date_str = input("Enter the date you left the UK (or press Enter if you're currently in the UK): ")
            exit_date = datetime.datetime.strptime(exit_date_str, "%d/%m/%Y").date() if exit_date_str else None
            dates.append((entry_date, exit_date))
        except ValueError:
            print("Invalid date format. Please use dd/mm/yyyy.")
    return dates

def write_dates_to_file(filename, dates):
    with open(filename, 'w') as file:
        file.write('\n'.join(f"entered UK {d[0].strftime('%d/%m/%Y')}\n" + (f"left UK {d[1].strftime('%d/%m/%Y')}" if d[1] else '') for d in dates))

def main():
    print(DISCLAIMER_TEXT)
    
    filename = "dates.txt"
    dates = read_dates_from_file(filename) or prompt_user_for_dates() or write_dates_to_file(filename, dates)

    # Validate and sort the dates
    dates = validate_dates(dates)
    write_dates_to_file(filename, dates)
    current_date = datetime.date.today()
    is_rule_maintained, days_left_outside = check_continuous_residence(dates, current_date)
    
    for i, (entry_date, exit_date) in enumerate(dates):
        inside_period = (exit_date or current_date) - entry_date
        print(f"From {entry_date.strftime('%d/%m/%Y')} to {(exit_date or current_date).strftime('%d/%m/%Y')}: {inside_period.days} days inside the UK.")
        if i != len(dates) - 1:
            outside_period = dates[i+1][0] - (exit_date or current_date)
            print(f"From {(exit_date or current_date).strftime('%d/%m/%Y')} to {dates[i+1][0].strftime('%d/%m/%Y')}: {outside_period.days} days outside the UK.")
    
    application_date = calculate_application_date(dates)
    if is_rule_maintained:
        print("\nYou have maintained continuous residence.")
        print(f"You can still be outside the UK for {days_left_outside} more days within the current 12-month period without breaking the continuous residence rule.")
        print(f"You can apply for settled status on or after {application_date.strftime('%d/%m/%Y')}.")
    else:
        print("\nYou have broken the continuous residence rule.")
        print(f"However, you can apply for settled status on or after {application_date.strftime('%d/%m/%Y')} if you maintain continuous residence until then.")

if __name__ == "__main__":
    main()