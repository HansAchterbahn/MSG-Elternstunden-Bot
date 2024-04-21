import pandas as pd
import toml
import tomli                        # read and write toml config data
from tabulate import tabulate       # format beautiful tables
import requests                     # API requests
import io                           # easy input/output operations for strings
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def elternstunden_bot():
    # get toml config data
    with open('config.toml', "r") as f:
        config = toml.load(f)
        nextcloud_settings = config["nextcloud"]
        email_settings = config["email"]
        changes_settings = config["changes"]

    # get config data for nextcloud api
    api_user                        = nextcloud_settings['username']
    api_key                         = nextcloud_settings['app_token']
    api_url_get_elternstunden_csv   = nextcloud_settings['url_get_elternstunden_csv']
    api_header                      = nextcloud_settings['api_header']
    export_table_columns            = nextcloud_settings['export_table_columns']

    # get last timestamp
    last_timestamp                  = changes_settings['last_timestamp']

    # connect to nextcloud API
    session = requests.session()            # connect to API and open a session
    session.auth = (api_user, api_key)      # authentification (user + password)
    response = session.get(api_url_get_elternstunden_csv, headers=api_header)   # get Elternstunden as CSV file sting
    #print(response.content.decode('utf-8'))                                    # Anzeige der Datei - Todo: kann weg


    # create pandas dataframe from CSV file string, check for changes since last timestamp and modify dataframe
    df = pd.read_csv(                                           # read pandas dataframe
        io.StringIO(response.content.decode('utf-8')),          # from CSV file string
        sep=','                                                 # with ',' as seperator
    )
    df_new_entries = df.loc[
        df['Zeitstempel'] > last_timestamp,                     # check for new entries since last timestamp
    ]
    new_last_timestamp = df.iloc[-1]['Zeitstempel']             # Get new last timestamp
    print("Einträge gesamt:")
    print(tabulate(df, headers = 'keys', tablefmt = 'mixed_outline')) # Todo: kann weg # simple_outline, mixed_outline, pretty,
    print("Einträge neu:")
    print(tabulate(df_new_entries, headers = 'keys', tablefmt = 'mixed_outline')) # Todo: kann weg


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
        table_html = df_feedback.to_html(               # create html feedback table from feedback dataframe
            index=False,                                    # without index
            justify='center',                               # headline text justified centered
            na_rep='',                                      # an empty string as NaN representation
            border=''                                       # no border in table tag
        )
        table_plain = tabulate(                         # create plain feedback table
            df_feedback,                                    # from feedback dataframe
            headers='keys',                                 # dataframe key values are used as headline text
            tablefmt='mixed_outline',                       # format table (use mixed_outline, simple_outline or pretty)
            showindex=False                                 # without index
        )

        # get e-mail message from config file and paste actual family_pseudonym and table_html/plain to string
        message_plain = email_settings['message_plain'].format(Familienpseudonym=family_pseudonym, Tabelle=table_plain)
        message_html = email_settings['message_html'].format(Familienpseudonym=family_pseudonym, Tabelle=table_html)
        #print(message_plain)        # todo: kann weg
        #print(message_html)         # todo: kann weg

        # append actual e-mail address, html- and plain-message to emails array
        emails.append({
            'e-mail-address': email,
            'message_plain': message_plain,
            'message_html': message_html
        })

    # get e-mail server settings from config file
    smtp_server     = email_settings["smtp_server"]
    port            = email_settings["smtp_port"]
    password        = email_settings["password"]
    sender          = email_settings["user"]

    # send e-mails
    for email in emails:
        print(email)

        # get e-mail data
        receiver        = email['e-mail-address']
        message_plain   = email['message_plain']
        message_html    = email['message_html']

        # create e-mail-message
        message = MIMEMultipart('alternative')
        message["Subject"] = "MSG Elternstunden"
        message["From"] = sender
        message["To"] = receiver
        message.attach(MIMEText(message_plain, 'plain'))
        message.attach(MIMEText(message_html, 'html'))

        # send e-mail
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, message.as_string())

    # write changes to toml config file
    config["changes"]["last_timestamp"] = new_last_timestamp
    with open('config.toml', "w") as f:
        toml.dump(config, f)


if __name__ == "__main__":
    elternstunden_bot()
