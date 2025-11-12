#!/usr/bin/env python3
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.config import settings

# Configuración de FastAPI Mail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME=settings.mail_from_name,
    MAIL_STARTTLS=settings.mail_tls,
    MAIL_SSL_TLS=settings.mail_ssl,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(conf)


async def send_verification_email(email: str, token: str):
    """Envía email de verificación"""
    
    verification_url = f"{settings.frontend_url}/verify-email?token={token}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
            .content {{ background: #f9f9f9; padding: 30px; }}
            .button {{ 
                display: inline-block; 
                padding: 12px 30px; 
                background: #4F46E5; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Verifica tu Email</h1>
            </div>
            <div class="content">
                <p>¡Hola!</p>
                <p>Gracias por registrarte. Por favor, verifica tu dirección de email haciendo clic en el botón de abajo:</p>
                <div style="text-align: center;">
                    <a href="{verification_url}" class="button">Verificar Email</a>
                </div>
                <p>O copia y pega este enlace en tu navegador:</p>
                <p style="word-break: break-all; color: #4F46E5;">{verification_url}</p>
                <p><strong>Este enlace expira en 1 hora.</strong></p>
                <p>Si no te registraste en nuestra plataforma, ignora este email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2025 Auth Service. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Verifica tu email",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    await fm.send_message(message)


async def send_password_reset_email(email: str, token: str):
    """Envía email de recuperación de contraseña"""
    
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #EF4444; color: white; padding: 20px; text-align: center; }}
            .content {{ background: #f9f9f9; padding: 30px; }}
            .button {{ 
                display: inline-block; 
                padding: 12px 30px; 
                background: #EF4444; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Recupera tu Contraseña</h1>
            </div>
            <div class="content">
                <p>¡Hola!</p>
                <p>Recibimos una solicitud para restablecer tu contraseña. Haz clic en el botón de abajo para crear una nueva:</p>
                <div style="text-align: center;">
                    <a href="{reset_url}" class="button">Restablecer Contraseña</a>
                </div>
                <p>O copia y pega este enlace en tu navegador:</p>
                <p style="word-break: break-all; color: #EF4444;">{reset_url}</p>
                <p><strong>Este enlace expira en 1 hora.</strong></p>
                <p>Si no solicitaste este cambio, ignora este email y tu contraseña permanecerá sin cambios.</p>
            </div>
            <div class="footer">
                <p>&copy; 2025 Auth Service. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Recupera tu contraseña",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    await fm.send_message(message)


async def send_welcome_email(email: str, username: str):
    """Envía email de bienvenida después de verificar"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #10B981; color: white; padding: 20px; text-align: center; }}
            .content {{ background: #f9f9f9; padding: 30px; }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>¡Bienvenido, {username}!</h1>
            </div>
            <div class="content">
                <p>Tu cuenta ha sido verificada exitosamente.</p>
                <p>Ahora puedes acceder a todas las funcionalidades de nuestra plataforma.</p>
                <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
            </div>
            <div class="footer">
                <p>&copy; 2025 Auth Service. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject=f"¡Bienvenido, {username}!",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    await fm.send_message(message)