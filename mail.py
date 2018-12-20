import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText


def send_mail(toaddr, subject, body):
	msg = MIMEMultipart()
	fromaddr = 'YOUR_MAIL_HERE'
	msg['From'] = fromaddr
	msg['To'] = toaddr
	msg['Subject'] = subject

	msg.attach(MIMEText(body, 'plain'))

	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(fromaddr, 'YOUR_PASSWORD_HERE')
	text = msg.as_string()
	server.sendmail(fromaddr, toaddr, text)
	server.quit()
