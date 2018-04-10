"""
Utilities for setting html email.
"""
import threading

from django.core.mail import EmailMessage
from django.template import loader


def send_html_mail(subject, template_path, mail_context, from_address, recipient_list, fail_silently=False):
    """
    Setting html email to user.

    Args:
        subject: The email's subject.
        template_path: The template path of the email.
        mail_context: The parameters to be parsed by the template.
        from_address: The sender of the email.
        recipient_list: The recipients list of the email.
        fail_silently: 是否安静的失败，如果是，发送失败不抛出异常，否则抛出一个smtplib.SMTPException 默认值: False。

    Returns:

    """
    html_content = loader.render_to_string(
        template_path,
        mail_context
    )
    msg = EmailMessage(subject, html_content, from_address, recipient_list)
    msg.content_subtype = "html"
    msg.send(fail_silently)


class HtmlEmailThread(threading.Thread):
    def __init__(self, subject, template_path, mail_context, from_address, recipient_list, fail_silently):
        """
        :param subject: The email's subject.
        :param template_path: The template path of the email.
        :param mail_context: The parameters to be parsed by the template.
        :param from_address: The sender of the email.
        :param recipient_list: The recipients list of the email.
        :param fail_silently: If set it to False, through a SMTPException when fail to send email.
        """
        self.subject = subject
        self.template_path = template_path
        self.mail_context = mail_context
        self.from_address = from_address
        self.recipient_list = recipient_list
        self.fail_silently = fail_silently
        threading.Thread.__init__(self)

    def run(self):
        html_content = loader.render_to_string(
            self.template_path,
            self.mail_context
        )
        msg = EmailMessage(self.subject, html_content, self.from_address, self.recipient_list)
        msg.content_subtype = "html"
        msg.send(self.fail_silently)


def send_html_email_in_thread(subject, template_path, mail_context, from_address, recipient_list, fail_silently=False):
    html_email_thread = HtmlEmailThread(subject, template_path, mail_context, from_address, recipient_list,
                                        fail_silently)
    html_email_thread.start()
