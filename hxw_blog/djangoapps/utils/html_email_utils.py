"""
Utilities for setting html email.
"""
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
