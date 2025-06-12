from django.template import Template, Context
from django.conf import settings
import os

class EmailTemplateEngine:
    """Enhanced email template engine with HTML templates"""
    
    # Color schemes for different template types
    COLOR_SCHEMES = {
        'order_placed': {
            'primary': '#28a745',      # Green
            'secondary': '#20c997',
            'accent': '#e8f5e9',
            'text': '#2d3436',
            'background': '#ffffff'
        },
        'order_shipped': {
            'primary': '#007bff',      # Blue
            'secondary': '#17a2b8',
            'accent': '#e3f2fd',
            'text': '#2d3436',
            'background': '#ffffff'
        },
        'order_delivered': {
            'primary': '#6f42c1',      # Purple
            'secondary': '#e83e8c',
            'accent': '#f3e5f5',
            'text': '#2d3436',
            'background': '#ffffff'
        },
        'marketing': {
            'primary': '#fd7e14',      # Orange
            'secondary': '#ffc107',
            'accent': '#fff3cd',
            'text': '#2d3436',
            'background': '#ffffff'
        },
        'security': {
            'primary': '#dc3545',      # Red
            'secondary': '#fd7e14',
            'accent': '#f8d7da',
            'text': '#2d3436',
            'background': '#ffffff'
        },
        'system': {
            'primary': '#6c757d',      # Gray
            'secondary': '#495057',
            'accent': '#f8f9fa',
            'text': '#2d3436',
            'background': '#ffffff'
        },
        'reminders': {
            'primary': '#20c997',      # Teal
            'secondary': '#17a2b8',
            'accent': '#d1ecf1',
            'text': '#2d3436',
            'background': '#ffffff'
        }
    }
    
    def get_base_template(self):
        """Get the base HTML email template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{{subject}}</title>
    <!--[if mso]>
    <noscript>
        <xml>
            <o:OfficeDocumentSettings>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
    </noscript>
    <![endif]-->
    <style>
        /* Reset styles */
        body, table, td, p, a, li, blockquote {
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }
        table, td {
            mso-table-lspace: 0pt;
            mso-table-rspace: 0pt;
        }
        img {
            -ms-interpolation-mode: bicubic;
            border: 0;
            height: auto;
            line-height: 100%;
            outline: none;
            text-decoration: none;
        }
        
        /* Base styles */
        body {
            margin: 0 !important;
            padding: 0 !important;
            background-color: #f4f4f4;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: {{colors.background}};
        }
        
        .header {
            background: linear-gradient(135deg, {{colors.primary}} 0%, {{colors.secondary}} 100%);
            padding: 30px 20px;
            text-align: center;
        }
        
        .logo {
            max-width: 200px;
            height: auto;
        }
        
        .content {
            padding: 40px 30px;
            background-color: {{colors.background}};
        }
        
        .content h1 {
            color: {{colors.primary}};
            font-size: 28px;
            font-weight: 700;
            margin: 0 0 20px 0;
            line-height: 1.2;
        }
        
        .content h2 {
            color: {{colors.text}};
            font-size: 22px;
            font-weight: 600;
            margin: 30px 0 15px 0;
        }
        
        .content p {
            color: {{colors.text}};
            font-size: 16px;
            line-height: 1.6;
            margin: 0 0 20px 0;
        }
        
        .highlight-box {
            background-color: {{colors.accent}};
            border-left: 4px solid {{colors.primary}};
            padding: 20px;
            margin: 25px 0;
            border-radius: 4px;
        }
        
        .button {
            display: inline-block;
            background: linear-gradient(135deg, {{colors.primary}} 0%, {{colors.secondary}} 100%);
            color: white !important;
            text-decoration: none;
            padding: 15px 30px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 16px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }
        
        .order-details {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin: 25px 0;
        }
        
        .order-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
        }
        
        .order-item:last-child {
            border-bottom: none;
            font-weight: 600;
            font-size: 18px;
        }
        
        .tracking-info {
            background: linear-gradient(135deg, {{colors.accent}} 0%, rgba(255,255,255,0.8) 100%);
            border-radius: 8px;
            padding: 25px;
            margin: 25px 0;
            text-align: center;
        }
        
        .tracking-number {
            font-size: 24px;
            font-weight: 700;
            color: {{colors.primary}};
            letter-spacing: 2px;
            margin: 10px 0;
        }
        
        .footer {
            background-color: #2d3436;
            color: #ffffff;
            padding: 30px 20px;
            text-align: center;
        }
        
        .footer p {
            color: #b2bec3;
            font-size: 14px;
            margin: 5px 0;
        }
        
        .social-links {
            margin: 20px 0;
        }
        
        .social-links a {
            display: inline-block;
            margin: 0 10px;
            color: #74b9ff;
            text-decoration: none;
        }
        
        /* Responsive */
        @media only screen and (max-width: 600px) {
            .email-container {
                width: 100% !important;
            }
            .content {
                padding: 20px !important;
            }
            .content h1 {
                font-size: 24px !important;
            }
            .button {
                display: block !important;
                text-align: center !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }
        }
    </style>
</head>
<body>
    <div class="email-container">
        <!-- Header -->
        <div class="header">
<img src="https://i.ibb.co/mC6YMbhf/Kalen-wht-Rd-Ylw-Primary.png" alt="Kalen Company Logo" class="logo">
        </div>
        
        <!-- Content -->
        <div class="content">
            {{content_body}}
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p><strong>{{company_name}}</strong></p>
            <p>{{company_address}}</p>
            <div class="social-links">
                <a href="{{social_facebook}}">Facebook</a>
                <a href="{{social_twitter}}">Twitter</a>
                <a href="{{social_instagram}}">Instagram</a>
            </div>
            <p>© {{current_year}} {{company_name}}. All rights reserved.</p>
            <p>
                <a href="{{unsubscribe_url}}" style="color: #74b9ff;">Unsubscribe</a> | 
                <a href="{{preferences_url}}" style="color: #74b9ff;">Manage Preferences</a>
            </p>
        </div>
    </div>
</body>
</html>
        """
    
    def get_order_placed_template(self):
        """Template for order placed notifications"""
        return """
            <h1>🎉 Order Confirmed!</h1>
            <p>Hi {{customer_name}},</p>
            <p>Thank you for your order! We're excited to get your items ready for shipment.</p>
            
            <div class="highlight-box">
                <h2>Order #{{order_number}}</h2>
                <p><strong>Order Date:</strong> {{order_date}}</p>
                <p><strong>Estimated Delivery:</strong> {{estimated_delivery}}</p>
            </div>
            
            <div class="order-details">
                <h3>Order Summary</h3>
                {{order_items}}
                <div class="order-item">
                    <span><strong>Total:</strong></span>
                    <span><strong>${{order_total}}</strong></span>
                </div>
            </div>
            
            <div style="text-align: center;">
                <a href="{{track_order_url}}" class="button">Track Your Order</a>
            </div>
            
            <p>We'll send you another email when your order ships. If you have any questions, feel free to contact our customer support.</p>
            
            <p>Thanks for choosing {{company_name}}!</p>
        """
    
    def get_order_shipped_template(self):
        """Template for order shipped notifications"""
        return """
            <h1>📦 Your Order is On Its Way!</h1>
            <p>Hi {{customer_name}},</p>
            <p>Great news! Your order has been shipped and is on its way to you.</p>
            
            <div class="tracking-info">
                <h2>Tracking Information</h2>
                <div class="tracking-number">{{tracking_number}}</div>
                <p><strong>Carrier:</strong> {{shipping_carrier}}</p>
                <p><strong>Expected Delivery:</strong> {{delivery_date}}</p>
            </div>
            
            <div class="highlight-box">
                <h3>Order #{{order_number}}</h3>
                <p><strong>Ship Date:</strong> {{ship_date}}</p>
                <p><strong>Shipping Address:</strong><br>{{shipping_address}}</p>
            </div>
            
            <div style="text-align: center;">
                <a href="{{tracking_url}}" class="button">Track Package</a>
            </div>
            
            <p>You can track your package using the tracking number above or by clicking the track button.</p>
            
            <p>Thank you for your business!</p>
        """
    
    def get_order_delivered_template(self):
        """Template for order delivered notifications"""
        return """
            <h1>✅ Order Delivered!</h1>
            <p>Hi {{customer_name}},</p>
            <p>Your order has been successfully delivered! We hope you love your purchase.</p>
            
            <div class="highlight-box">
                <h2>Delivery Confirmed</h2>
                <p><strong>Order #{{order_number}}</strong></p>
                <p><strong>Delivered:</strong> {{delivery_date}} at {{delivery_time}}</p>
                <p><strong>Location:</strong> {{delivery_location}}</p>
            </div>
            
            <div style="text-align: center;">
                <a href="{{review_url}}" class="button">Leave a Review</a>
                <a href="{{reorder_url}}" class="button" style="margin-left: 10px;">Reorder Items</a>
            </div>
            
            <p>How was your experience? We'd love to hear your feedback!</p>
            
            <p>Need to return something? Our return policy allows returns within 30 days of delivery.</p>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="{{return_url}}" style="color: {{colors.primary}}; text-decoration: none;">Start a Return</a>
            </div>
        """
    
    def get_marketing_template(self):
        """Template for marketing notifications"""
        return """
            <h1>🔥 {{campaign_title}}</h1>
            <p>Hi {{customer_name}},</p>
            <p>{{marketing_message}}</p>
            
            <div class="highlight-box">
                <h2>{{offer_title}}</h2>
                <p style="font-size: 18px; font-weight: 600;">{{offer_description}}</p>
                {% if discount_code %}
                <p><strong>Use Code:</strong> <span style="background: {{colors.primary}}; color: white; padding: 5px 10px; border-radius: 4px; font-weight: 600;">{{discount_code}}</span></p>
                {% endif %}
            </div>
            
            <div style="text-align: center;">
                <a href="{{cta_url}}" class="button">{{cta_text}}</a>
            </div>
            
            <p style="font-size: 14px; color: #6c757d;">{{offer_terms}}</p>
        """
    
    def get_security_template(self):
        """Template for security notifications"""
        return """
            <h1>🔒 Security Alert</h1>
            <p>Hi {{user_name}},</p>
            <p>We detected unusual activity on your account and wanted to let you know.</p>
            
            <div class="highlight-box">
                <h2>{{alert_type}}</h2>
                <p><strong>Date & Time:</strong> {{alert_timestamp}}</p>
                <p><strong>Location:</strong> {{alert_location}}</p>
                <p><strong>Device:</strong> {{alert_device}}</p>
            </div>
            
            <p><strong>What happened?</strong></p>
            <p>{{alert_details}}</p>
            
            <div style="text-align: center;">
                <a href="{{secure_account_url}}" class="button">Secure My Account</a>
            </div>
            
            <p><strong>If this was you:</strong> No action is needed.</p>
            <p><strong>If this wasn't you:</strong> Please secure your account immediately by clicking the button above.</p>
            
            <p>For additional help, contact our security team at {{security_email}}.</p>
        """
    
    def render_email_template(self, template_type, subject, variables, logo_url=None):
        """Render complete HTML email template"""
        from datetime import datetime
        
        # Get color scheme for template type
        colors = self.COLOR_SCHEMES.get(template_type, self.COLOR_SCHEMES['system'])
        
        # Get appropriate content template
        content_templates = {
            'order_placed': self.get_order_placed_template(),
            'order_shipped': self.get_order_shipped_template(),
            'order_delivered': self.get_order_delivered_template(),
            'marketing': self.get_marketing_template(),
            'security': self.get_security_template(),
        }
        
        content_body = content_templates.get(template_type, """
            <h1>{{subject}}</h1>
            <p>{{message}}</p>
        """)
        
        # Default company information
        company_info = {
            'company_name': getattr(settings, 'COMPANY_NAME', 'Kalen Tech'),
            'company_address': getattr(settings, 'COMPANY_ADDRESS', '123 Business St, City, State 12345'),
            'logo_url': logo_url or getattr(settings, 'COMPANY_LOGO_URL', '/static/images/logo.png'),
            'social_facebook': getattr(settings, 'SOCIAL_FACEBOOK', '#'),
            'social_twitter': getattr(settings, 'SOCIAL_TWITTER', '#'),
            'social_instagram': getattr(settings, 'SOCIAL_INSTAGRAM', '#'),
            'unsubscribe_url': getattr(settings, 'UNSUBSCRIBE_URL', '#'),
            'preferences_url': getattr(settings, 'PREFERENCES_URL', '#'),
            'current_year': datetime.now().year,
        }
        
        # Merge all template variables
        template_vars = {
            'subject': subject,
            'colors': colors,
            'content_body': content_body,
            **company_info,
            **variables
        }
        
        # Render base template
        base_template = Template(self.get_base_template())
        html_content = base_template.render(Context(template_vars))
        
        # Render content body within the base template
        final_template = Template(html_content)
        return final_template.render(Context(template_vars))
