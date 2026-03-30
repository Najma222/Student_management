email_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Account</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;">
    
    <!-- Main Container -->
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f4f4; padding: 20px 0;">
        <tr>
            <td align="center">
                <table width="100%" max-width="600" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #ffffff; padding: 40px 30px 20px 30px; text-align: center; border-radius: 8px 8px 0 0;">
                            <div style="font-size: 32px; font-weight: bold; color: #1a73e8; margin-bottom: 10px;">
                                📚 Course Management System
                            </div>
                            <div style="font-size: 14px; color: #5f6368; font-weight: 500;">
                                Secure Student Portal
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="background-color: #ffffff; padding: 0 30px 30px 30px; border-radius: 0 0 8px 8px;">
                            
                            <!-- Welcome Message -->
                            <div style="text-align: center; margin-bottom: 30px;">
                                <h1 style="color: #202124; font-size: 24px; font-weight: 600; margin: 0 0 10px 0;">
                                    Welcome, {name}!
                                </h1>
                                <p style="color: #5f6368; font-size: 16px; line-height: 1.5; margin: 0;">
                                    Thank you for registering with the Course Management System. Please verify your email address to activate your account.
                                </p>
                            </div>
                            
                            <!-- Verify Button -->
                            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{verify_url}" 
                                           style="background-color: #1a73e8; color: #ffffff; font-size: 16px; font-weight: 600; text-decoration: none; padding: 15px 30px; border-radius: 6px; display: inline-block; -webkit-text-size-adjust: none;">
                                            Verify Your Account
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Alternative Link -->
                            <div style="text-align: center; margin: 20px 0;">
                                <p style="color: #5f6368; font-size: 14px; line-height: 1.5; margin: 0;">
                                    If the button above doesn't work, copy and paste this link into your browser:
                                </p>
                                <p style="color: #1a73e8; font-size: 12px; word-break: break-all; margin: 5px 0; font-family: 'Courier New', monospace;">
                                    {verify_url}
                                </p>
                            </div>
                            
                            <!-- Security Info -->
                            <div style="background-color: #f8f9fa; border-left: 4px solid #1a73e8; padding: 15px; margin: 20px 0;">
                                <p style="color: #5f6368; font-size: 14px; line-height: 1.5; margin: 0;">
                                    <strong>🔒 Security Notice:</strong> This link expires in 1 hour for your protection. If you didn't request this verification, you can safely ignore this email.
                                </p>
                            </div>
                            
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 0; text-align: center;">
                            <div style="color: #5f6368; font-size: 14px; line-height: 1.5;">
                                <p style="margin: 0 0 10px 0;">
                                    Thanks,<br>
                                    <strong>Course Management Team</strong>
                                </p>
                                <div style="border-top: 1px solid #e0e0e0; padding-top: 15px; margin-top: 15px;">
                                    <p style="margin: 0; font-size: 12px; color: #9aa0a6;">
                                        This is an automated message. Please do not reply to this email.
                                    </p>
                                </div>
                            </div>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
    
</body>
</html>
"""
