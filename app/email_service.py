import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

async def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send email using SMTP"""
    try:
        message = MIMEMultipart("alternative")
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        message["Subject"] = subject
        
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=True,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

async def send_parent_credentials(to_email: str, password: str, child_name: str) -> bool:
    """Send auto-generated credentials to parent"""
    subject = "🌟 Welcome to Autism Therapy Management System"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; }}
            .header p {{ color: rgba(255,255,255,0.9); margin-top: 10px; }}
            .content {{ padding: 40px 30px; }}
            .welcome-box {{ background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%); border-radius: 12px; padding: 25px; margin-bottom: 25px; }}
            .credentials {{ background: #fff; border: 2px solid #667eea; border-radius: 12px; padding: 20px; margin: 20px 0; }}
            .credentials h3 {{ color: #667eea; margin-top: 0; }}
            .credential-item {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #eee; }}
            .credential-item:last-child {{ border-bottom: none; }}
            .label {{ color: #666; font-weight: 500; }}
            .value {{ color: #333; font-weight: 600; background: #f0f4ff; padding: 5px 15px; border-radius: 20px; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 30px; font-weight: 600; margin-top: 20px; }}
            .footer {{ background: #f8f9fa; padding: 20px 30px; text-align: center; color: #666; font-size: 14px; }}
            .emoji {{ font-size: 48px; margin-bottom: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="emoji">🌈</div>
                <h1>Welcome to Our Family!</h1>
                <p>Your account has been created successfully</p>
            </div>
            <div class="content">
                <div class="welcome-box">
                    <p>Dear Parent,</p>
                    <p>An account has been created for you to monitor <strong>{child_name}</strong>'s therapy progress. You can now track sessions, view reports, and stay connected with the therapy team.</p>
                </div>
                
                <div class="credentials">
                    <h3>🔐 Your Login Credentials</h3>
                    <div class="credential-item">
                        <span class="label">Email:</span>
                        <span class="value">{to_email}</span>
                    </div>
                    <div class="credential-item">
                        <span class="label">Password:</span>
                        <span class="value">{password}</span>
                    </div>
                </div>
                
                <p style="color: #e74c3c; font-size: 14px;">⚠️ Please change your password after first login for security.</p>
                
                <center>
                    <a href="#" class="button">Login to Dashboard</a>
                </center>
            </div>
            <div class="footer">
                <p>🌟 Autism Therapy Management System</p>
                <p>Supporting every step of the journey</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(to_email, subject, html_content)

async def send_child_code_email(to_email: str, child_code: str, child_name: str) -> bool:
    """Send child code to parent for self-registration"""
    subject = "🔑 Your Child Code for Registration"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 40px 30px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; }}
            .content {{ padding: 40px 30px; text-align: center; }}
            .code-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; padding: 30px; margin: 30px 0; }}
            .code {{ font-size: 36px; font-weight: 700; color: white; letter-spacing: 5px; font-family: 'Courier New', monospace; }}
            .footer {{ background: #f8f9fa; padding: 20px 30px; text-align: center; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔑 Child Registration Code</h1>
            </div>
            <div class="content">
                <p>Use the following code to register and link your account with <strong>{child_name}</strong>'s profile:</p>
                
                <div class="code-box">
                    <div class="code">{child_code}</div>
                </div>
                
                <p>Enter this code during parent registration to connect with your child's therapy records.</p>
            </div>
            <div class="footer">
                <p>🌟 Autism Therapy Management System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(to_email, subject, html_content)

async def send_weekly_report_notification(to_email: str, child_name: str, report_summary: str) -> bool:
    """Notify parent about weekly report availability"""
    subject = f"📊 Weekly Progress Report for {child_name}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 40px 30px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; }}
            .content {{ padding: 40px 30px; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 30px; font-weight: 600; }}
            .footer {{ background: #f8f9fa; padding: 20px 30px; text-align: center; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Weekly Report Available</h1>
            </div>
            <div class="content">
                <p>Dear Parent,</p>
                <p>The weekly progress report for <strong>{child_name}</strong> is now available.</p>
                <p>{report_summary}</p>
                <center>
                    <a href="#" class="button">View Full Report</a>
                </center>
            </div>
            <div class="footer">
                <p>🌟 Autism Therapy Management System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(to_email, subject, html_content)
