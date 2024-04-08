import pandas as pd
import tomli


last_timestamp = "2023-01-01 00:00:00"
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
            <table align="center">
                <tr class="table-head">
                    <td>Name</td>
                    <td>Arbeitskreis</td>
                    <td>Klasse</td>
                </tr>
                <tr>
                    <td>Heiz Jakobi</td>
                    <td>AK Hof</td>
                    <td>Linde</td>
                </tr>
                <tr>
                    <td>Simone Kältel</td>
                    <td>AK Expertiese</td>
                    <td>Buche</td>
                </tr>
                <tr class=table-foot>
                </tr>
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

if __name__ == "__main__":
    nextcloud_settings, email_settings, changes_settings = toml_read("config.toml")
    csv_read("data.csv")
    nc_forms_api(nextcloud_settings)
    write_email(email_settings)
