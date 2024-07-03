import pandas as pd
import datetime

def filter_data(column_name, date,data):
    return data[column_name].apply(lambda x: False if x == "Never accessed" else pd.to_datetime(x, format='%d %b %Y', errors='coerce') > pd.to_datetime(date, format='%d %b %Y'))

def filterAccount(data):
    # Define the date
    current_date = datetime.datetime.now()
    date = (current_date - datetime.timedelta(days=30)).strftime('%d %b %Y')

    # Apply the filter to the necessary columns
    data['Filter Jira Service Management'] = filter_data('Last seen in Jira Service Management - telkomdds', date,data)
    data['Filter Jira Software'] = filter_data('Last seen in Jira - telkomdds', date,data)
    data['Filter Confluence'] = filter_data('Last seen in Confluence - telkomdds', date,data)
    data['Filter Atlas'] = filter_data('Last seen in Atlas - telkomdds', date,data)

    # Filter the 'Added to org' column
    data['One Month Create'] = pd.to_datetime(data['Added to org'], format='%d %b %Y', errors='coerce') > pd.to_datetime(date, format='%d %b %Y')

    # Create a mask for rows where all filters are False
    mask = (
        (data['Filter Jira Software'] == False) &
        (data['Filter Jira Service Management'] == False) &
        (data['Filter Confluence'] == False) &
        (data['Filter Atlas'] == False) &
        (data['One Month Create'] == False)
    )

    # Print the filtered data and save it to a CSV file
    return data[mask]
