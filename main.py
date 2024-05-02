import os

import pandas as pd                             # allows pandas dataframes → easy data management
import toml                                     # read and write toml config files
from tabulate import tabulate                   # format beautiful tables
import requests                                 # API requests
import io                                       # easy input/output operations for strings
import smtplib, ssl                             # SMTP server connection
from email.mime.text import MIMEText            # MIME text typ (e-mail)
from email.mime.multipart import MIMEMultipart  # MIME multipart type (e-mail)


def elternstunden_bot(max_new_lines=100):

    # get config data for nextcloud dav api from environment variables
    nc_dav_settings = dict()
    nc_dav_settings["user"]      = os.environ.get("ELTERNSTUNDEN_BOT_NC_USER")
    nc_dav_settings["key"]       = os.environ.get("ELTERNSTUNDEN_BOT_NC_PASS")
    nc_dav_settings["url"]       = os.environ.get("ELTERNSTUNDEN_BOT_NC_URL_DAV_CONFIG_TOML")
    nc_dav_settings["headers"]   = ''

    # connect to MSG Nextcloud and query config.toml from Dav API
    response = get_nc_object(nc_dav_settings)
    config = toml.loads(response.content.decode('utf-8'))  # read string in to a toml object (loads = load string)

    # get TOML config data in to separat dicts
    nc_settings         = config["nextcloud"]       # get nextcloud config settings
    email_settings      = config["email"]           # get e-mail config settings
    changes_settings    = config["changes"]         # get changes config settings

    # get config data for nextcloud forms api from TOML config file
    nc_forms_settings = dict()
    nc_forms_settings["user"]       = os.environ.get("ELTERNSTUNDEN_BOT_NC_USER")
    nc_forms_settings["key"]        = os.environ.get("ELTERNSTUNDEN_BOT_NC_PASS")
    nc_forms_settings["url"]        = nc_settings['url_forms_get_elternstunden_csv']
    nc_forms_settings["headers"]    = nc_settings['forms_api_header']
    export_table_columns            = nc_settings['forms_export_table_columns']

    if changes_settings["to_many_new_entries"] == True:
        return "Error: To many new entries"

    # get last timestamp
    last_timestamp                  = changes_settings['last_timestamp']

    # query Nextcloud Forms API
    response = get_nc_object(nc_forms_settings)

    # create pandas dataframe from CSV file string, check for changes since last timestamp and modify dataframe
    df = pd.read_csv(                                           # read pandas dataframe
        io.StringIO(response.content.decode('utf-8')),              # from CSV file string
        sep=','                                                     # with ',' as seperator
    )
    df_new_entries = df.loc[                                    # create dataframe with only new entries
        df['Zeitstempel'] > last_timestamp,                         # check for new entries since last timestamp
    ]
    lines_added = len(df_new_entries.index)
    new_last_timestamp = df.iloc[-1]['Zeitstempel']             # Get new last timestamp

    # abort script in case there are no new lines added
    if lines_added == 0:
        return "No new lines - nothing to do here! :-)"

    # abort script in case there are more new lines than defined in max_new_lines
    if lines_added > max_new_lines:
        # get e-mail data
        error_string = f"(lines added = {lines_added}) > (max_new_lines = {max_new_lines})"

        send_email(
            settings=email_settings,
            receiver = "webmaster@msg-freunde.de",
            subject = "Fehler im MSG Elternstunden-Bot",
            message_plain = f"Fehler:\n{error_string}\n\nEinträge neu:\n{tabulate(df_new_entries, headers = 'keys', tablefmt = 'mixed_outline')}"
        )
        config["changes"]["to_many_new_entries"] = True             # set flag in TOML file for to many new lines
        put_nc_object(nc_dav_settings, config)

        return "Error: " + error_string

    # Debugging message: Show all entries and new entries
    print("Einträge gesamt:")
    print(tabulate(df, headers = 'keys', tablefmt = 'mixed_outline'))
    print("Einträge neu:")
    print(tabulate(df_new_entries, headers = 'keys', tablefmt = 'mixed_outline'))

    # create a feedback table for every e-mail address in new entries
    emails = []                                 # create empty array to store the feedback e-mails in
    emails_new_entries = set(                   # defines a set of all e-mail addresses in new entries
        df_new_entries['E-Mail-Adresse']
    )
    for email in emails_new_entries:            # iterate over all e-mails in new entries
        df_feedback = df.loc[                       # create a feedback table for every e-mail-address in new entries
            df['E-Mail-Adresse'] == email,              # search for the current e-mail address in all entries
            export_table_columns                        # export only columns that are defined in the config file
        ]

        family_pseudonym = df_feedback.iloc[-1]['Familienpseudonym']    # get last used 'Familienpseudonym'
        table_html = df_feedback.to_html(           # create html feedback table from feedback dataframe
            index=False,                                # without index
            justify='center',                           # headline text justified centered
            na_rep='',                                  # an empty string as NaN representation
            border=''                                   # no border in table tag
        )
        table_plain = tabulate(                     # create plain feedback table
            df_feedback,                                # from feedback dataframe
            headers='keys',                             # dataframe key values are used as headline text
            tablefmt='mixed_outline',                   # format table (use mixed_outline, simple_outline or pretty)
            showindex=False                             # without index
        )

        # get e-mail message from config file and paste actual family_pseudonym and table_html/plain to string
        message_plain = email_settings['message_plain'].format(Familienpseudonym=family_pseudonym, Tabelle=table_plain)
        message_html  = email_settings['message_html' ].format(Familienpseudonym=family_pseudonym, Tabelle=table_html)

        # append actual e-mail address, html- and plain-message to emails array
        emails.append({
            'e-mail-address':   email,
            'message_plain':    message_plain,
            'message_html':     message_html
        })

    # send e-mails
    for email in emails:
        # send e-mail
        send_email(
            settings        = email_settings,
            receiver        = email['e-mail-address'],
            subject         = "MSG Elternstunden",
            message_plain   = email['message_plain'],
            message_html    = email['message_html']
        )
        print("E-Mails gesendet:", email['e-mail-address'])


    # connect to MSG Nextcloud and write new/changed config.toml to Dav API
    config["changes"]["last_timestamp"]         = new_last_timestamp
    config["changes"]["lines_added_last_run"]   = lines_added
    response = put_nc_object(nc_dav_settings, config)

    return f"New lines added: {lines_added}"

def get_nc_object(settings:dict):
    # get Nextcloud login data and URL
    user    = settings["user"]                    # Nextcloud API user
    key     = settings["key"]                     # Nextcloud API app token
    url     = settings["url"]                     # Nextcloud API URL to config.toml
    headers = settings["headers"]                 # Nextcloud API headers

    # connect to MSG Nextcloud and query config.toml from Dav API
    session = requests.session()                            # open a session
    session.auth = (user, key)                              # hand over login data (user + password)
    response = session.get(url=url, headers=headers)        # get config.toml from MSG Nextcloud as sting

    return response
                                         # return toml object
def put_nc_object(settings:dict, object):
    # get Nextcloud login data and URL
    user    = settings["user"]            # Nextcloud API user
    key     = settings["key"]             # Nextcloud API app token
    url     = settings["url"]             # Nextcloud API URL to config.toml

    # connect to MSG Nextcloud and put config.toml to Dav API
    session = requests.session()                            # open a session
    session.auth = (user, key)                      # hand over login data (user + password)
    response = session.put(
        url=url,
        data=toml.dumps(object).encode('utf-8'))       # get config.toml from MSG Nextcloud as sting

    return response                                 # return put response content

def send_email(settings:dict, receiver:str, subject:str= '', message_plain:str= '', message_html:str= ''):
    # get e-mail server settings from config file
    smtp_server     = settings["smtp_server"]
    port            = settings["smtp_port"]
    password        = settings["password"]
    sender          = settings["user"]

    # create e-mail-message
    message = MIMEMultipart('alternative')
    message["From"] = sender
    message["To"] = receiver
    message["Subject"] = subject
    if message_plain != '':
        message.attach(MIMEText(message_plain, 'plain'))
    if message_html != '':
        message.attach(MIMEText(message_html, 'html'))

    # send e-mail
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, message.as_string())

if __name__ == "__main__":
    feedback = elternstunden_bot()
    print(feedback)
