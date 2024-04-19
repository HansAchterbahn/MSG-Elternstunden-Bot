import pandas as pd
import tomli
from tabulate import tabulate

last_timestamp = "2023-01-01T00:00:00+02:00"
def csv_read(file_path):
    df_new = pd.read_csv(file_path)        # read csv file to dataframe
    df_new["Zeitstempel"] = (
        pd.to_datetime(df_new["Zeitstempel"], yearfirst=True, utc=True)) # convert timestamp strings to UTC+0 values
    print(df_new["Zeitstempel"])
    print(df_new.loc[df_new["Zeitstempel"] > last_timestamp])

def toml_read(file_path):
    with open(file_path, "rb") as config_file:
        config = tomli.load(config_file)
        nextcloud_settings = config["nextcloud"]
        email_settings = config["email"]
        changes_settings = config["changes"]
        return [nextcloud_settings, email_settings, changes_settings]

def write_email(email_settings:dict):
    import smtplib, ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    smtp_server = email_settings["smtp_server"]
    port = email_settings["smtp_port"]
    password = email_settings["password"]
    sender = email_settings["user"]
    receiver = 'mario.hesse@posteo.de'

    text = """\
Hallo ..., 

vielen Dank für deinen Einsatz an der Montessori Schule Göttingen! 
Anbei bekommst du eine Auflistung aller Elternstunden die mit deiner E-Mail-Adresse verknüpft sind.

Liebe Grüße und bis zum nächsten Mal!
Elternstunden-Bot


| Name          | Arbeitskreis  | Klasse |
|---------------|---------------|--------|
| Heinz Jakobi  | AK Hof        | Linde  |
| Simone Kältel | AK Expertiese | Buche  | 
    """
    html = """\
    <body>
        <style>
            table, th, td {
              border-left: 1px solid black;
              border-right: 1px solid black;
              border-collapse: collapse;
              padding-left: 10px;
              padding-right: 10px;
              padding-top: 2px;
              padding-bottom: 2px;
            }
            .table-head {
                font-weight: bold;
                border-bottom: 1px solid black;
                border-top: 1px solid black;
            }
            .table-foot {
                border-bottom: 1px solid black;
            }
            
        </style>
        <p>
            Hallo ..., 
        </p>
        <p>
            vielen Dank für deinen Einsatz an der Montessori Schule Göttingen! <br /> 
            Anbei bekommst du eine Auflistung aller Elternstunden die mit deiner E-Mail-Adresse verknüpft sind.
        </p>
        <p>            
            Liebe Grüße und bis zum nächsten Mal! <br />
            Elternstunden-Bot
        </p>
        <p>
            <table border="1" class="dataframe">
              <thead>
                <tr>
                  <th></th>
                  <th>Datum</th>
                  <th>Zeit</th>
                  <th>Klasse</th>
                  <th>Arbeitskreis</th>
                  <th>Art der Arbeit</th>
                  <th>Veranstaltungskontext</th>
                  <th>E-Mail-Adresse</th>
                  <th>Familienpseudonym</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th>0</th>
                  <td>2024-04-10</td>
                  <td>02:20</td>
                  <td>Linde</td>
                  <td>Erdkinderplan</td>
                  <td>Planung</td>
                  <td>Keiner</td>
                  <td>mario.hesse@gfisch.de</td>
                  <td>GFisch</td>
                </tr>
              </tbody>
            </table>
        </p>
    </body>
    """
    message = MIMEMultipart('alternative')
    message["Subject"] = "MSG Elternstunden"
    message["From"] = sender
    message["To"] = receiver
    message.attach(MIMEText(text, 'plain'))
    message.attach(MIMEText(html, 'html'))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, message.as_string())


def nc_forms_api(nextcloud_settings:dict):
    import requests         # Paket für API-Anfragen
    import io               # Paket für einfache Input/Output Verarbeitung

    # Konfigurationsdaten aus Config-Dict holen
    api_user                        = nextcloud_settings['username']
    api_key                         = nextcloud_settings['app_token']
    api_url_get_elternstunden_csv   = nextcloud_settings['url_get_elternstunden_csv']
    api_header                      = nextcloud_settings['api_header']

    # Verbinden mit der Nextcloud API, eröffnen einer Session, Elternstunden.csv herunterladen & in Pandas Datenrahmen speichern
    session = requests.session()            # API öffnen
    session.auth = (api_user, api_key)      # Authentifizieren (User + Passwort)
    response = session.get(api_url_get_elternstunden_csv, headers=api_header)       # Elternstunden CSV Datei als String abfragen
    #print(response.content.decode('utf-8'))                                     # Anzeige der Datei - Todo: kann weg
    df = pd.read_csv(io.StringIO(response.content.decode('utf-8')), sep=',')    # einlesen der CSV Datei in einen Pandas Datenrahmen

    # Bearbeiten des Pandas Dataframes: Prüfen, ob neue Einträge gemacht wurden seit dem letzten Programmdurchlauf
    Letzter_Zeitstempel = '2024-04-10T18:05:30'
    Formular_Kategorien = ['Datum','Zeit','Klasse','Arbeitskreis','Art der Arbeit', 'Veranstaltungskontext','E-Mail-Adresse','Familienpseudonym']
    df_new = df.loc[df['Zeitstempel']> Letzter_Zeitstempel, Formular_Kategorien]
    print(tabulate(df_new, headers = 'keys', tablefmt = 'psql'))
    html_table = df.loc[df['Zeitstempel'] <= Letzter_Zeitstempel, Formular_Kategorien].to_html()

    # Für jeden neuen Eintrag werden die E-Mail-Adressen ermittelt und alle bisherigen Einträge gebündelt als
    # HTML-Tabelle den einzelnen E-Mail-Adressen aus den neuen Einträgen zugeordnet.
    emails = []
    for email in set(df_new['E-Mail-Adresse']):
        df_feedback = df.loc[df['E-Mail-Adresse']==email, Formular_Kategorien]
        emails.append({
            'E-Mail-Adresse':email,
            'Familienpseudonym':df_feedback.iloc[-1]['Familienpseudonym'],
            'HTML-Tabelle':df_feedback.to_html(),
            'Text-Tabelle':tabulate(df_feedback, headers = 'keys', tablefmt = 'psql', showindex=False)
        })
        print(tabulate(df_feedback, headers = 'keys', tablefmt = 'psql', showindex=False))

    for email in emails:
        print(email)

if __name__ == "__main__":
    nextcloud_settings, email_settings, changes_settings = toml_read("config.toml")
    #csv_read("data.gfisch.csv")
    nc_forms_api(nextcloud_settings)
    #write_email(email_settings)
